import ollama
import base64
import os

def encode_image_to_base64(image_path):
    """Resmi base64 formatına çevirir (Ollama'nın okuyabilmesi için)"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analyze_image_with_vlm(image_path):
    """
    Kaydedilen görseli LLaVA modeline gönderir ve 
    görseldeki verinin metinsel bir özetini/çevirisini alır.
    Anlamsız tasarım elementlerini filtreler.
    """
    if not os.path.exists(image_path):
        return "Görsel bulunamadı."

    print(f"\n[VLM] {image_path} analiz ediliyor...")
    base64_image = encode_image_to_base64(image_path)

    # TUSAŞ vakasına uygun AKILLI SİSTEM PROMPTU (Gürültü Filtreli)
    prompt = (
        "Sen bir veri analistisin. Bu görseli incele. "
        "DİKKAT: Eğer görsel sadece düz bir renk, boş bir çerçeve, renk geçişi (gradyan) "
        "veya anlamsız bir sayfa süsü ise SADECE VE SADECE 'ANLAMSIZ_GORSEL' yaz ve başka hiçbir şey ekleme. "
        "Eğer görselde gerçekten bir metin, tablo, grafik veya akış şeması varsa, "
        "sadece içeriğini detaylıca metne dök ve yorum katma."
    )

    try:
        response = ollama.chat(
            model="llava:7b",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "images": [base64_image]
                }
            ]
        )
        return response["message"]["content"]
    except Exception as e:
        return f"VLM Analiz Hatası: {str(e)}"

# Test Bloğu
if __name__ == "__main__":
    # Test etmek için o boş çerçevelerden veya gradyanlardan birinin adını yaz
    # Örnek: "data/image_0c061d.png" (Senin klasöründeki bir çöp görseli kullan)
    test_image = "data1/image_p11_b32.png" 
    
    sonuc = analyze_image_with_vlm(test_image)
    print("\n--- VLM ÇIKTISI ---")
    print(sonuc)