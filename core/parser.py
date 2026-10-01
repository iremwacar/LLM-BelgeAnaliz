import fitz  # PyMuPDF (Metin blokları ve görseller için)
import pdfplumber  # (Çizgisiz ve karmaşık tablolar için)
from PIL import Image, ImageStat

def extract_lfrag_blocks(pdf_path):
    """
    PDF belgesini işler: 
    Tabloları pdfplumber ile bularak Markdown'a çevirir,
    Metin ve Görselleri PyMuPDF ile yapısal olarak ayırır.
    """
    print(f"[{pdf_path}] işleniyor...")
    document_blocks = []

    # İki kütüphaneyi de aynı PDF üzerinde açıyoruz
    pdf_fitz = fitz.open(pdf_path)
    pdf_plumber = pdfplumber.open(pdf_path)

    for page_num in range(len(pdf_fitz)):
        fitz_page = pdf_fitz[page_num]
        plumber_page = pdf_plumber.pages[page_num]

        # --- ADIM 1: PDFPLUMBER İLE TABLOLARI ÇIKAR ---
        table_bboxes = []
        
        # pdfplumber tabloyu metin hizalamalarına göre bulur (çizgisiz tabloları yakalar)
        tables = plumber_page.find_tables()
        
        for tab_index, table in enumerate(tables):
            # Tablonun koordinatlarını kaydet (PyMuPDF okurken bu alanı atlayacak)
            table_bboxes.append(table.bbox)
            
            # Tablonun verisini çıkar
            extracted_data = table.extract()
            
            md_table = ""
            if extracted_data:
                md_table = "\n"
                for row_idx, row in enumerate(extracted_data):
                    # Hücrelerdeki None değerleri temizle ve alt satırları boşlukla değiştir
                    clean_row = [str(cell).replace('\n', ' ').strip() if cell is not None else "" for cell in row]
                    md_table += "| " + " | ".join(clean_row) + " |\n"
                    
                    # Başlık satırının altına Markdown ayırıcı (---) ekle
                    if row_idx == 0:
                        md_table += "|" + "|".join(["---" for _ in clean_row]) + "|\n"
                        
            document_blocks.append({
                "id": f"page_{page_num+1}_table_{tab_index}",
                "page": page_num + 1,
                "type": "table",
                "content": md_table if md_table else "[BOŞ TABLO]"
            })

        # --- ADIM 2: PYMUPDF İLE METİN VE GÖRSELLERİ ÇIKAR ---
        page_dict = fitz_page.get_text("dict")
        blocks = page_dict.get("blocks", [])
        
        for b_index, block in enumerate(blocks):
            block_bbox = fitz.Rect(block["bbox"])
            
            # KONTROL: Bu blok, pdfplumber'ın bulduğu tablonun içine düşüyor mu?
            is_in_table = False
            for t_bbox in table_bboxes:
                plumber_rect = fitz.Rect(t_bbox)
                
                # Eğer bloğun yarıdan fazlası tablonun içindeyse bunu atla
                if block_bbox.intersects(plumber_rect):
                    intersect_area = block_bbox.intersect(plumber_rect).get_area()
                    block_area = block_bbox.get_area()
                    if block_area > 0 and (intersect_area / block_area) > 0.5:
                        is_in_table = True
                        break
            
            if is_in_table:
                continue

            # METİN BLOĞU
            if block['type'] == 0:
                text_content = ""
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text_content += span.get("text", "") + " "
                
                text_content = text_content.strip()
                if text_content: 
                    document_blocks.append({
                        "id": f"page_{page_num+1}_block_{b_index}",
                        "page": page_num + 1,
                        "type": "text",
                        "content": text_content
                    })
                    
           # GÖRSEL (Image) Bloğu
            # GÖRSEL (Image) Bloğu
            elif block['type'] == 1:
                bbox = block.get("bbox")
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]

                # 1. BOYUT FİLTRESİ (Çok küçük ikonları atla)
                if width < 50 or height < 50:
                    continue

                image_bytes = block.get("image")
                if image_bytes:
                    # 2. GÖRSEL KARMAŞIKLIK (ENTROPİ) FİLTRESİ
                    try:
                        img = Image.open(io.BytesIO(image_bytes)).convert("L")
                        
                        # img.entropy() 0 ile 8 arasında bir değer döner.
                        # Düz kutular ve gradyanlar genellikle 1-2 civarındadır.
                        # Şemalar ve grafikler 3'ün üzerindedir.
                        if img.entropy() < 3.0:
                            continue
                            
                    except Exception:
                        pass # Hata olursa güvenli tarafta kal, silme

                    image_filename = f"image_p{page_num+1}_b{b_index}.png"
                    image_filepath = f"data1/{image_filename}"
                    
                    with open(image_filepath, "wb") as f:
                        f.write(image_bytes)
                        
                    document_blocks.append({
                        "id": f"page_{page_num+1}_block_{b_index}",
                        "page": page_num + 1,
                        "type": "image",
                        "image_path": image_filepath,
                        "content": "[VLM_BEKLIYOR]"
                    })
                    
    pdf_fitz.close()
    pdf_plumber.close()
    return document_blocks

# Test Bloğu
if __name__ == "__main__":
    test_pdf = "data/TUSAŞ_2024_Sürdürülebilirlik_Raporu_TR.pdf" 
    
    try:
        extracted_blocks = extract_lfrag_blocks(test_pdf)
        for block in extracted_blocks:
            # Sadece tabloları yazdırarak yeni sistemin performansını görelim
            if block['type'] == 'table':
                print(f"\n--- TABLO BULUNDU (Sayfa {block['page']}) ---")
                print(block['content'][:500])
    except Exception as e:
        print(f"Hata oluştu: {e}")