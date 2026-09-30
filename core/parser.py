import fitz  # PyMuPDF

def extract_lfrag_blocks(pdf_path):
    """
    PDF belgesini okur ve sayfa düzenini (layout) koruyarak 
    yapısal bloklara (metin, resim) ayırır.
    """
    print(f"[{pdf_path}] işleniyor...")
    doc = fitz.open(pdf_path)
    document_blocks = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Sayfadaki tüm blokları sözlük (dict) formatında çekiyoruz
        page_dict = page.get_text("dict")
        blocks = page_dict.get("blocks", [])
        
        for b_index, block in enumerate(blocks):
            # block['type'] == 0 ise bu bir METİN bloğudur
            if block['type'] == 0:
                # Blok içindeki satırları ve kelimeleri birleştir
                text_content = ""
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text_content += span.get("text", "") + " "
                
                text_content = text_content.strip()
                
                if text_content: # Boş blokları atla
                    document_blocks.append({
                        "id": f"page_{page_num+1}_block_{b_index}",
                        "page": page_num + 1,
                        "type": "text",
                        "content": text_content
                    })
                    
            # block['type'] == 1 ise bu bir GÖRSEL (Image) bloğudur
            elif block['type'] == 1:
                # Şimdilik sadece yer tutucu (placeholder) koyuyoruz.
                # Daha sonra burayı VLM (Görsel Dil Modeli) ile güncelleyeceğiz.
                document_blocks.append({
                    "id": f"page_{page_num+1}_block_{b_index}",
                    "page": page_num + 1,
                    "type": "image",
                    "content": "[GÖRSEL BULUNDU - VLM TARAFINDAN ÖZETLENECEK]"
                })

    doc.close()
    return document_blocks

# Test Bloğu
if __name__ == "__main__":
    # Test etmek için data klasörüne tablo/görsel içeren bir PDF koy ve adını yaz
    test_pdf = "data/Case_Study_TUSAŞ_LLM.pdf" 
    
    try:
        extracted_blocks = extract_lfrag_blocks(test_pdf)
        for i, block in enumerate(extracted_blocks[:10]): # İlk 10 bloğu yazdır
            print(f"\n--- Blok {i+1} ---")
            print(f"Sayfa: {block['page']} | Tür: {block['type']}")
            print(f"İçerik: {block['content'][:150]}...") # İçeriğin ilk 150 karakteri
    except Exception as e:
        print(f"Hata oluştu: {e}")