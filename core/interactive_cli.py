import os
import sys
from rag_engine import TusasRAGEngine

def main():
    print("="*70)
    print("TUSAŞ ENTERPRISE-GRADE MULTİMODAL RAG - İNTERAKTİF TEST KONSOLU")
    print("Modeller: BAAI/bge-m3 (Vektör) & Qwen2.5-7B-Instruct (Sentez & Dil Eşleme)")
    print("="*70)
    
    try:
        engine = TusasRAGEngine()
    except Exception as e:
        print(f"[HATA] RAG Motoru başlatılamadı: {e}")
        return

    print("\nSistem kullanıma hazırdı. Çıkmak için 'q' veya 'exit' yazabilirsiniz.\n")

    while True:
        try:
            query = input("Soru Sorunuz > ").strip()
            if not query:
                continue
            if query.lower() in ['q', 'exit', 'çıkış']:
                print("Konsoldan çıkılıyor. İyi günler!")
                break

            print("\n[İşleniyor] Yanıt oluşturuluyor...")
            answer, image_refs = engine.generate_answer(query)

            print("\n" + "-"*70)
            print("YANIT:")
            print("-"*70)
            print(answer)
            
            if image_refs:
                print("\n[İlişkili Görsel Referansları]:")
                for img_ref in set(image_refs):
                    print(f" - {img_ref}")
            print("="*70 + "\n")

        except KeyboardInterrupt:
            print("\nÇıkılıyor tabular...")
            break
        except Exception as e:
            print(f"\n[Hata oluştu]: {e}\n")

if __name__ == "__main__":
    main()