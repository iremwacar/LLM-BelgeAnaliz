import os
import io
import uuid
import base64
from PIL import Image, ImageStat
import fitz  # PyMuPDF
import pdfplumber
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import ollama

class TusasIngestionPipeline:
    def __init__(self, collection_name="tusas_doc_collection", db_path="./qdrant_data"):
        print("[INGESTION] Konu/Başlık Duyarlı (Heading-Aware) RAPTOR Hiyerarşik Boru Hattı başlatılıyor...")
        self.model = SentenceTransformer('sentence-transformers/clip-ViT-B-32-multilingual-v1')
        self.client = QdrantClient(path=db_path)
        self.collection_name = collection_name
        self._init_collection()

    def _init_collection(self):
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        vector_size = 512  # CLIP ViT-B-32 dimension
        
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            print(f"[Qdrant] '{self.collection_name}' koleksiyonu oluşturuldu.")
        else:
            print(f"[Qdrant] '{self.collection_name}' koleksiyonu zaten mevcut.")

    def sanitize_text(self, text: str) -> str:
        if not text:
            return ""
        return text.strip()

    def analyze_image_with_vlm(self, image_path: str) -> str:
        if not os.path.exists(image_path):
            return "Görsel bulunamadı."
        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")

            prompt = (
                "Sen kıdemli bir AR-GE görsel analiz uzmanısın. Bu görseli incele. "
                "Eğer görsel sadece düz renk, boş çerçeve, gradyan veya anlamsız sayfa süsüyse SADECE 'ANLAMSIZ_GORSEL' yaz. "
                "Eğer görselde metin, tablo, grafik, mimari şema veya akış şeması varsa, içeriğini detaylıca teknik Türkçe ile açıkla."
            )

            response = ollama.chat(
                model="llava:7b",
                messages=[{
                    "role": "user",
                    "content": prompt,
                    "images": [base64_image]
                }]
            )
            caption = response["message"]["content"].strip()
            if "ANLAMSIZ_GORSEL" in caption.upper():
                return ""
            return caption
        except Exception as e:
            print(f"[VLM Uyarı] Görsel analiz edilemedi: {e}")
            return ""

    def extract_lfrag_blocks(self, pdf_path: str):
        print(f"[LFRAG] Başlık ve Yapı Duyarlı Ayrıştırma: {pdf_path}")
        document_blocks = []

        pdf_fitz = fitz.open(pdf_path)
        pdf_plumber = pdfplumber.open(pdf_path)

        # Önce belgedeki ortalama font boyutunu hesaplayarak başlık tespiti yapalım
        font_sizes = []
        for page in pdf_fitz:
            for b in page.get_text("dict").get("blocks", []):
                if b.get("type") == 0:
                    for l in b.get("lines", []):
                        for s in l.get("spans", []):
                            font_sizes.append(s.get("size", 10))
        
        avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 11.0

        for page_num in range(len(pdf_fitz)):
            fitz_page = pdf_fitz[page_num]
            plumber_page = pdf_plumber.pages[page_num]

            # 1. Tablolar
            table_bboxes = []
            tables = plumber_page.find_tables()
            for tab_index, table in enumerate(tables):
                table_bboxes.append(table.bbox)
                extracted_data = table.extract()
                md_table = ""
                if extracted_data:
                    md_table = "\n"
                    for row_idx, row in enumerate(extracted_data):
                        clean_row = [str(cell).replace('\n', ' ').strip() if cell is not None else "" for cell in row]
                        md_table += "| " + " | ".join(clean_row) + " |\n"
                        if row_idx == 0:
                            md_table += "|" + "|".join(["---" for _ in clean_row]) + "|\n"
                
                document_blocks.append({
                    "id": f"page_{page_num+1}_table_{tab_index}",
                    "page": page_num + 1,
                    "level": 0,
                    "type": "table",
                    "is_heading": False,
                    "content": md_table if md_table else "[BOŞ TABLO]",
                    "image_path": ""
                })

            # 2. Metin ve Görseller
            page_dict = fitz_page.get_text("dict")
            blocks = page_dict.get("blocks", [])

            for b_index, block in enumerate(blocks):
                block_bbox = fitz.Rect(block["bbox"])
                
                is_in_table = False
                for t_bbox in table_bboxes:
                    plumber_rect = fitz.Rect(t_bbox)
                    if block_bbox.intersects(plumber_rect):
                        intersect_area = block_bbox.intersect(plumber_rect).get_area()
                        block_area = block_bbox.get_area()
                        if block_area > 0 and (intersect_area / block_area) > 0.5:
                            is_in_table = True
                            break
                if is_in_table:
                    continue

                if block['type'] == 0:
                    text_content = ""
                    max_span_size = 0.1
                    is_bold = False
                    
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            txt = span.get("text", "")
                            text_content += txt + " "
                            s_size = span.get("size", 10)
                            if s_size > max_span_size:
                                max_span_size = s_size
                            if "bold" in span.get("font", "").lower() or span.get("flags", 0) & 2:
                                is_bold = True
                    
                    cleaned_text = self.sanitize_text(text_content)
                    if cleaned_text:
                        is_heading = False
                        cleaned_len = len(cleaned_text)

                        # Yasaklı formül ve gürültü kontrolü
                        has_math_symbols = any(sym in cleaned_text for sym in ["=", "softmax", "√", "∑", "∏", "矩阵"])
                        has_email = "@" in cleaned_text
                        has_author_stars = any(sym in cleaned_text for sym in ["∗", "†", "‡"])
                        is_reference = cleaned_text.startswith("[") and "]" in cleaned_text[:5]

                        if 3 <= cleaned_len <= 90 and not has_email and not has_author_stars and not has_math_symbols and not is_reference:
                            if max_span_size > avg_font_size + 1.5 or is_bold:
                                is_heading = True

                        document_blocks.append({
                            "id": f"page_{page_num+1}_block_{b_index}",
                            "page": page_num + 1,
                            "level": 0,
                            "type": "chunk",
                            "is_heading": is_heading,
                            "content": cleaned_text,
                            "image_path": ""
                        })

                elif block['type'] == 1:
                    bbox = block.get("bbox")
                    width = bbox[2] - bbox[0]
                    height = bbox[3] - bbox[1]
                    if width < 50 or height < 50:
                        continue

                    image_bytes = block.get("image")
                    if image_bytes:
                        try:
                            img = Image.open(io.BytesIO(image_bytes)).convert("L")
                            if img.entropy() < 3.0:
                                continue
                        except Exception:
                            pass

                        os.makedirs("data1", exist_ok=True)
                        image_filename = f"image_p{page_num+1}_b{b_index}.png"
                        image_filepath = os.path.join("data1", image_filename)
                        
                        with open(image_filepath, "wb") as f:
                            f.write(image_bytes)

                        print(f"[VLM] Sayfa {page_num+1} görseli analiz ediliyor...")
                        vlm_caption = self.analyze_image_with_vlm(image_filepath)
                        
                        if vlm_caption:
                            document_blocks.append({
                                "id": f"page_{page_num+1}_img_{b_index}",
                                "page": page_num + 1,
                                "level": 0,
                                "type": "image",
                                "is_heading": False,
                                "content": f"[GÖRSEL ANALİZİ (VLM)]: {vlm_caption}",
                                "image_path": image_filepath
                            })

        pdf_fitz.close()
        pdf_plumber.close()
        return document_blocks

    def generate_raptor_hierarchy(self, document_blocks):
        """
        Konu ve Başlık Duyarlı (Heading/Topic-Aware) RAPTOR Ağacı Oluşturur:
        - Level 0: Micro Chunks / Tablolar / Görseller
        - Level 1: Tespit edilen başlıklar veya anlamsal eşiklere göre dinamik konu bölümleri (Section Summaries)
        - Level 2: Belge Küresel Vizyon Özeti (Document Global Summary)
        """
        print("[RAPTOR] Başlık ve Konu Değişimlerine Duyarlı Hiyerarşik Ağaç inşa ediliyor...")
        
        # 1. Adım: Level 1 - Konu/Başlık Bazlı Bölüm Özetleri (Semantic Chunking by Headings)
        sections = []
        current_section_blocks = []
        current_heading = "Giriş / Genel Bölüm"
        
        for block in document_blocks:
            if block.get("is_heading", False):
                # Eğer bir önceki bölüm doluysa kaydet
                if current_section_blocks:
                    sections.append({
                        "heading": current_heading,
                        "blocks": current_section_blocks
                    })
                    current_section_blocks = []
                current_heading = block["content"]
            
            current_section_blocks.append(block)
            
            # Eğer bir konu çok uzadıysa (örn. 3500 karakteri geçtiyse) ara bölme yap
            if sum([len(b["content"]) for b in current_section_blocks]) > 3500:
                sections.append({
                    "heading": current_heading,
                    "blocks": current_section_blocks
                })
                current_section_blocks = []

        # Kalan son bölümü ekle
        if current_section_blocks:
            sections.append({
                "heading": current_heading,
                "blocks": current_section_blocks
            })

        section_summaries = []
        for sec_idx, sec in enumerate(sections):
            sec_text = "\n".join([b["content"] for b in sec["blocks"]])
            start_p = sec["blocks"][0]["page"] if sec["blocks"] else 1
            end_p = sec["blocks"][-1]["page"] if sec["blocks"] else 1

            prompt = (
                f"Sen kıdemli bir AR-GE teknik direktörüsün. Belgenin '{sec['heading']}' başlıklı "
                f"(Sayfa {start_p}-{end_p}) bölümünü incele ve buradaki ana odak noktalarını, "
                f"teknik detayları ve stratejik hedefleri kapsayan hiyerarşik bir konu özeti (Section Summary) çıkar.\n\n"
                f"Bölüm İçeriği:\n{sec_text[:8000]}"
            )
            try:
                res = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}])
                summary_text = res["message"]["content"].strip()
                section_summaries.append({
                    "id": str(uuid.uuid4()),
                    "page": f"{start_p}-{end_p}",
                    "level": 1,  # Section Tier
                    "type": "section_summary",
                    "content": f"[KONU/BÖLÜM HİYERARŞİK ÖZETİ ('{sec['heading']} - Sayfa {start_p}-{end_p}')]: {summary_text}",
                    "image_path": ""
                })
                print(f"[RAPTOR] Konu Özeti Oluşturuldu: '{sec['heading']}' (Sayfa {start_p}-{end_p})")
            except Exception as e:
                print(f"[Uyarı] Konu özeti üretilemedi: {e}")

        # 2. Adım: Level 2 - Belge Küresel Vizyon Özeti (Root Summary)
        all_section_texts = "\n".join([s["content"] for s in section_summaries])
        global_summary = []
        global_prompt = (
            "Sen TUSAŞ başmimarsın. Aşağıdaki dinamik konu özetlerinin tamamını sentetik olarak sentezle "
            "ve bu belgenin bütünsel vizyonunu, ana hedeflerini ve stratejik kapsamını özetleyen "
            "en üst düzey küresel vizyon özeti (Document-Level Global Summary) çıkar.\n\n"
            f"Konu Özetleri:\n{all_section_texts[:15000]}"
        )
        try:
            res = ollama.chat(model="llama3", messages=[{"role": "user", "content": global_prompt}])
            global_text = res["message"]["content"].strip()
            global_summary.append({
                "id": str(uuid.uuid4()),
                "page": "Tümü (Kök/Global)",
                "level": 2,  # Root / Global Tier
                "type": "document_summary",
                "content": f"[BELGE KÜRESEL VİZYON ÖZETİ (ROOT)]: {global_text}",
                "image_path": ""
            })
            print("[RAPTOR] En üst düzey Global Vizyon Özeti (Root) başarıyla oluşturuldu.")
        except Exception as e:
            print(f"[Uyarı] Global vizyon özeti üretilemedi: {e}")

        return global_summary + section_summaries + document_blocks

    def ingest_document(self, pdf_path: str):
        print("="*60)
        print(f"KONU DUYARLI RAPTOR HİYERARŞİK INGESTION BAŞLATILDI: {pdf_path}")
        print("="*60)
        
        blocks = self.extract_lfrag_blocks(pdf_path)
        hierarchical_items = self.generate_raptor_hierarchy(blocks)
        
        print(f"[INGESTION] Toplam {len(hierarchical_items)} hiyerarşik düğüm Qdrant'a yükleniyor...")

        points = []
        for item in hierarchical_items:
            vector = self.model.encode(item["content"]).tolist()
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "type": item["type"],
                        "page": item["page"],
                        "level": item.get("level", 0),
                        "content": item["content"],
                        "image_path": item.get("image_path", "")
                    }
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"[INGESTION] Konu Duyarlı RAPTOR İndeksleme Başarıyla Tamamlandı! ({len(points)} düğüm)")

if __name__ == "__main__":
    pipeline = TusasIngestionPipeline()
    test_pdf = "data/Banka Kartı Sözleşmesi Türkçe-069465f2-9cba-4f9e-953e-a1c3347a30aa.pdf"
    if os.path.exists(test_pdf):
        pipeline.ingest_document(test_pdf)
    else:
        print(f"[Uyarı] Test PDF dosyası bulunamadı: {test_pdf}")