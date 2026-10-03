import os
from rag_engine import TusasRAGEngine
import ollama

class TusasAgentWorkflow:
    def __init__(self):
        print("[AGENT] İki Katmanlı Ajan Mimarisi başlatılıyor...")
        self.rag_engine = TusasRAGEngine()

    def run(self, user_query: str):
        """
        Niyet Bağımsız ve Katmanlı Ajan Akışı. 
        Kullanıcı ister global ('Bu belge ne anlatıyor?') ister local ('Attention nedir?') sorsun,
        vektör motoru en doğru bağlamı (özet veya detay) doğrudan yakalar.
        """
        print("="*50)
        print("AJAN İŞ AKIŞI BAŞLATILDI")
        print("="*50)

        print(f"[Ajan] İşlenen Sorgu: '{user_query}'")
        
        # Two-Tier Retrieval (Özetler ve Chunk'lar ortak uzayda taranır)
        contexts = self.rag_engine.search(user_query, top_k=4)

        context_text = ""
        image_references = []
        for ctx in contexts:
            context_text += f"\n--- [Tip: {ctx['type'].upper()} | Sayfa: {ctx['page']}] ---\n{ctx['content']}\n"
            if ctx['type'] == 'image' and ctx['image_path']:
                image_references.append(ctx['image_path'])

        # Profesyonel Sistem Promptu
        system_prompt = (
            "Sen kıdemli AR-GE Belge Analiz Asistanısın. "
            "Sana sunulan bağlam hem belgenin makro/genel özetlerini hem de mikro/teknik detaylarını içerebilir. "
            "Kullanıcının sorusunu (ister genel ister teknik olsun) kesinlikle ve yalnızca **akıcı, profesyonel ve teknik bir Türkçe** ile yanıtla. "
            "Asla İngilizce etiketler veya kalıplar kullanma. "
            "Eğer bilgi bağlamda kesinlikle yoksa 'Belgede bu bilgiye ulaşılamadı' de."
        )
        
        user_prompt = f"Bağlam:\n{context_text}\n\nKullanıcı Sorusu: {user_query}"

        print("[Ajan] Ollama (Llama-3) nihai sentezi gerçekleştiriyor...")
        try:
            response = ollama.chat(
                model="llama3",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            answer = response["message"]["content"]
            return answer, image_references
        except Exception as e:
            return f"Ajan Yanıt Üretme Hatası: {str(e)}", []

if __name__ == "__main__":
    agent = TusasAgentWorkflow()
    
    # Test edelim: Hem global hem local soruları aynı anda kusursuz yönetebiliyor mu?
    test_soru = "Sürdürülebilirlik hakkında düşünceleri neler?" 
    
    yanit, gorseller = agent.run(test_soru)
    
    print("\n" + "="*50)
    print("AJANIN NİHAİ YANITI:")
    print(yanit)
    print("="*50)