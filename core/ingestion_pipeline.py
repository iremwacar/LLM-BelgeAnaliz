import os
import io
import uuid
import base64
from PIL import Image
import fitz  # PyMuPDF
import pdfplumber
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from typing import Optional
import ollama

class TusasIngestionPipeline:
    def __init__(
        self,
        collection_name="tusas_doc_collection",
        db_path="./qdrant_data",
        client=None,
        model=None,
        recreate_collection=False,
    ):
        print("[INGESTION] BGE-M3 ve Granüler Multimodal Belge Ayrıştırma Boru Hattı başlatılıyor...")
        self.model = model or SentenceTransformer('BAAI/bge-m3', model_kwargs={"use_safetensors": True})
        self.client = client or QdrantClient(path=db_path)
        self.collection_name = collection_name
        self._init_collection(recreate=recreate_collection)

    def _init_collection(self, recreate=False):
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        vector_size = 1024  # BGE-M3 dimension

        if exists and recreate:
            self.client.delete_collection(collection_name=self.collection_name)
            print("[Qdrant] Eski koleksiyon temizlendi.")
            exists = False

        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            print(f"[Qdrant] '{self.collection_name}' koleksiyonu (1024d) başarıyla oluşturuldu.")
        else:
            print(f"[Qdrant] '{self.collection_name}' koleksiyonu kullanılıyor.")
        try:
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="document_id",
                field_schema="keyword",
            )
        except Exception:
            pass

    def delete_document_vectors(self, document_id: str):
        from qdrant_client.models import Filter, FieldCondition, MatchValue, FilterSelector

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
                )
            ),
        )

    def sanitize_text(self, text: str) -> str:
        if not text:
            return ""
        return text.strip()

    def _get_easyocr_reader(self):
        # Lazy loading to save memory if not needed immediately
        if not hasattr(self, '_reader'):
            import easyocr
            import logging
            logging.getLogger("easyocr").setLevel(logging.ERROR)
            print("[OCR] EasyOCR motoru başlatılıyor (İlk yükleme birkaç saniye sürebilir)...")
            self._reader = easyocr.Reader(['tr', 'en'], gpu=True) # If no GPU, it will fallback to CPU safely
        return self._reader

    def analyze_image_with_vlm(self, image_path: str) -> str:
        # Note: Method name kept same to avoid breaking other parts of the code, but it now uses OCR.
        if not os.path.exists(image_path):
            return "Görsel bulunamadı."
        try:
            reader = self._get_easyocr_reader()
            
            results = reader.readtext(
                image_path, 
                paragraph=True,
                x_ths=0.7, 
                y_ths=0.5  
            )
            
            extracted_texts = []
            for bbox, text in results:
                cleaned_text = text.strip()
                if cleaned_text:
                    extracted_texts.append(cleaned_text)
            
            if not extracted_texts:
                return "ANLAMSIZ_GORSEL"
                
            return "\n".join(extracted_texts)
            
        except Exception as e:
            print(f"[OCR Uyarı] Görsel analiz edilemedi: {e}")
            return ""

    def extract_granular_blocks_from_image(self, image_path: str, progress_cb=None):
        print(f"[OCR] Görsel belge taranıyor ve granüler bloklara ayrıştırılıyor: {image_path}")
        if progress_cb:
            progress_cb("images", 28, "Resim analiz ediliyor")
        raw_text = self.analyze_image_with_vlm(image_path)
        if not raw_text or "ANLAMSIZ_GORSEL" in raw_text.upper():
            return []

        lines = raw_text.split("\n")
        document_blocks = []
        
        current_heading = "Giriş / Genel Başlık"
        for idx, line in enumerate(lines):
            cleaned = line.strip()
            if not cleaned:
                continue
            
            is_heading = False
            if len(cleaned) < 50 and not cleaned.startswith("-") and not cleaned.startswith("✓") and not cleaned.startswith("*"):
                is_heading = True
                current_heading = cleaned

            document_blocks.append({
                "id": f"img_block_{idx}",
                "page": 1,
                "level": 0,
                "type": "chunk",
                "is_heading": is_heading,
                "content": f"[{current_heading}]: {cleaned}",
                "image_path": image_path
            })

        return document_blocks

    def extract_lfrag_blocks(self, pdf_path: str, progress_cb=None):
        print(f"[LFRAG] PDF Başlık ve Yapı Duyarlı Ayrıştırma: {pdf_path}")
        document_blocks = []
        pdf_fitz = fitz.open(pdf_path)
        pdf_plumber = pdfplumber.open(pdf_path)
        page_count = max(len(pdf_fitz), 1)

        font_sizes = []
        for page in pdf_fitz:
            for b in page.get_text("dict").get("blocks", []):
                if b.get("type") == 0:
                    for l in b.get("lines", []):
                        for s in l.get("spans", []):
                            font_sizes.append(s.get("size", 10))
        
        avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 11.0

        for page_num in range(len(pdf_fitz)):
            if progress_cb:
                page_pct = 12 + int((page_num / page_count) * 38)
                progress_cb("processing", page_pct, f"İşlem sayfası {page_num + 1} / {page_count}")
            fitz_page = pdf_fitz[page_num]
            plumber_page = pdf_plumber.pages[page_num]

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
                    "id": f"sayfa_{page_num+1}_tablo_{tab_index}",
                    "page": page_num + 1,
                    "level": 0,
                    "type": "table",
                    "is_heading": False,
                    "content": md_table if md_table else "[BOŞ TABLO]",
                    "image_path": ""
                })

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
                        has_math_symbols = any(sym in cleaned_text for sym in ["=", "softmax", "√", "∑", "∏", "±"])
                        has_email = "@" in cleaned_text
                        has_author_stars = any(sym in cleaned_text for sym in ["∗", "†", "‡"])
                        is_reference = cleaned_text.startswith("[") and "]" in cleaned_text[:5]

                        if 3 <= cleaned_len <= 90 and not has_email and not has_author_stars and not has_math_symbols and not is_reference:
                            if max_span_size > avg_font_size + 1.5 or is_bold:
                                is_heading = True

                        document_blocks.append({
                            "id": f"sayfa_{page_num+1}_blok_{b_index}",
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
                        os.makedirs("data1", exist_ok=True)
                        image_filename = f"image_p{page_num+1}_b{b_index}.png"
                        image_filepath = os.path.join("data1", image_filename)
                        with open(image_filepath, "wb") as f:
                            f.write(image_bytes)

                        if progress_cb:
                            progress_cb(
                                "images",
                                min(54, 40 + (page_num * 2)),
                                f"Resim analiz ediliyor, sayfa {page_num + 1}",
                            )
                        vlm_caption = self.analyze_image_with_vlm(image_filepath)
                        if vlm_caption:
                            document_blocks.append({
                                "id": f"page_{page_num+1}_img_{b_index}",
                                "page": page_num + 1,
                                "level": 0,
                                "type": "image",
                                "is_heading": False,
                                "content": f"[GÖRSEL ANALİZİ (OCR)]: {vlm_caption}",
                                "image_path": image_filepath
                            })

        pdf_fitz.close()
        pdf_plumber.close()
        return document_blocks

    def generate_raptor_hierarchy(self, document_blocks, progress_cb=None):
        print("[RAPTOR] Hiyerarşik Ağaç inşa ediliyor...")
        if progress_cb:
            progress_cb("hierarchy", 58, "Building knowledge hierarchy")
        sections = []
        current_section_blocks = []
        current_heading = "Giriş / Genel Bölüm"
        
        for block in document_blocks:
            if block.get("is_heading", False):
                if current_section_blocks:
                    sections.append({
                        "heading": current_heading,
                        "blocks": current_section_blocks
                    })
                    current_section_blocks = []
                current_heading = block["content"]
            
            current_section_blocks.append(block)
            if sum([len(b["content"]) for b in current_section_blocks]) > 3500:
                sections.append({
                    "heading": current_heading,
                    "blocks": current_section_blocks
                })
                current_section_blocks = []

        if current_section_blocks:
            sections.append({
                "heading": current_heading,
                "blocks": current_section_blocks
            })

        section_summaries = []
        for sec_index, sec in enumerate(sections):
            if progress_cb and sections:
                hierarchy_pct = 58 + int((sec_index / max(len(sections), 1)) * 14)
                progress_cb("hierarchy", hierarchy_pct, f"Bilgiler topanıyor {sec_index + 1} / {len(sections)}")
            sec_text = "\n".join([b["content"] for b in sec["blocks"]])
            start_p = sec["blocks"][0]["page"] if sec["blocks"] else 1
            end_p = sec["blocks"][-1]["page"] if sec["blocks"] else 1

            prompt = (
                f"Sen kıdemli bir AR-GE teknik direktörüsün. Belgenin '{sec['heading']}' başlıklı "
                f"bölümünü incele ve buradaki ana odak noktalarını, teknik detayları kapsayan hiyerarşik bir konu özeti çıkar.\n\n"
                f"Bölüm İçeriği:\n{sec_text[:8000]}"
            )
            try:
                res = ollama.chat(model="qwen2.5:7b-instruct", messages=[{"role": "user", "content": prompt}])
                summary_text = res["message"]["content"].strip()
                section_summaries.append({
                    "id": str(uuid.uuid4()),
                    "page": f"{start_p}-{end_p}",
                    "level": 1,
                    "type": "section_summary",
                    "content": f"[KONU/BÖLÜM ÖZETİ ('{sec['heading']}')]: {summary_text}",
                    "image_path": ""
                })
            except Exception as e:
                pass

        all_section_texts = "\n".join([s["content"] for s in section_summaries])
        global_summary = []
        global_prompt = (
            "Sen başmimarsın. Aşağıdaki dinamik konu özetlerinin tamamını sentezle "
            "ve bu belgenin bütünsel vizyonunu özetleyen küresel vizyon özeti çıkar.\n\n"
            f"Konu Özetleri:\n{all_section_texts[:15000]}"
        )
        try:
            res = ollama.chat(model="qwen2.5:7b-instruct", messages=[{"role": "user", "content": global_prompt}])
            global_text = res["message"]["content"].strip()
            global_summary.append({
                "id": str(uuid.uuid4()),
                "page": "Tümü (Global)",
                "level": 2,
                "type": "document_summary",
                "content": f"[BELGE KÜRESEL VİZYON ÖZETİ (ROOT)]: {global_text}",
                "image_path": ""
            })
        except Exception as e:
            pass

        return global_summary + section_summaries + document_blocks

    def ingest_document(self, file_path: str, document_id: Optional[str] = None, progress_cb=None):
        print("="*60)
        print(f"MULTİMODAL GRANÜLER INGESTION BAŞLATILDI: {file_path}")
        print("="*60)

        document_id = document_id or str(uuid.uuid4())

        def report(step: str, percent: int, detail: str = ""):
            if progress_cb:
                progress_cb(step, percent, detail)

        report("processing", 8, "Processing document")

        ext = os.path.splitext(file_path)[1].lower()
        document_blocks = []

        if ext in ['.png', '.jpg', '.jpeg', '.webp']:
            document_blocks = self.extract_granular_blocks_from_image(file_path, progress_cb=progress_cb)
            if not document_blocks:
                print("[Hata] Görsel belgeden anlamlı metin çıkarılamadı.")
                raise ValueError("No readable text could be extracted from the image.")
        elif ext == '.pdf':
            document_blocks = self.extract_lfrag_blocks(file_path, progress_cb=progress_cb)
        else:
            raise ValueError(f"Desteklenmeyen dosya formatı: {ext}")

        hierarchical_items = self.generate_raptor_hierarchy(document_blocks, progress_cb=progress_cb)

        print(f"[INGESTION] Toplam {len(hierarchical_items)} granüler hiyerarşik düğüm BGE-M3 ile Qdrant'a yükleniyor...")
        report("embedding", 75, "Creating embeddings")

        points = []
        total_items = max(len(hierarchical_items), 1)
        for index, item in enumerate(hierarchical_items):
            vector = self.model.encode(item["content"]).tolist()
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "document_id": document_id,
                        "type": item["type"],
                        "page": str(item["page"]),
                        "level": item.get("level", 0),
                        "content": item["content"],
                        "image_path": item.get("image_path", "")
                    }
                )
            )
            if index % 4 == 0 or index == len(hierarchical_items) - 1:
                embed_pct = 75 + int(((index + 1) / total_items) * 15)
                report("embedding", min(embed_pct, 90), f"Bilgiler kadediliyor {index + 1} / {total_items}")

        report("vector_db", 92, "Transferring to vector DB")
        batch_size = 32
        for start in range(0, len(points), batch_size):
            batch = points[start:start + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
            done = min(start + batch_size, len(points))
            vector_pct = 92 + int((done / max(len(points), 1)) * 7)
            report("vector_db", min(vector_pct, 99), f"İndekslenen {done} / {len(points)} düğüm")

        report("ready", 100, "Document is ready for questions")
        print(f"[INGESTION] Granüler Multimodal İndeksleme Başarıyla Tamamlandı! ({len(points)} düğüm)")
        return {"document_id": document_id, "chunk_count": len(points)}