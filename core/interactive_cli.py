import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.agent_graph import TusasAgentWorkflow

def main():
    print("="*60)
    print("TUSAŞ MAGE-RAG / RAPTOR AKILLI AJAN SİSTEMİ - İLETİŞİM KONSOLU")
    print("="*60)
    print("Sistem başarıyla yüklendi. Sorularınızı sorabilirsiniz (Çıkış için 'q' yazın).\n")
    
    agent = TusasAgentWorkflow()
    
    while True:
        try:
            query = input("\n[Kullanıcı Sorusu]: ").strip()
            if query.lower() in ['q', 'quit', 'exit']:
                print("Konsoldan çıkılıyor. İyi günler!")
                break
            if not query:
                continue
                
            answer, images = agent.run(query)
            print("\n" + "-"*50)
            print("AJANIN YANITI:")
            print(answer)
            if images:
                print(f"\n[İlgili Görsel Referansları]: {images}")
            print("-" * 50)
        except KeyboardInterrupt:
            print("\nÇıkış yapılıyor...")
            break
        except Exception as e:
            print(f"Hata oluştu: {str(e)}")

if __name__ == "__main__":
    main()