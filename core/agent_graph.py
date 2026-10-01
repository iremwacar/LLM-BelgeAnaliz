import os
from rag_engine import TusasRAGEngine
import ollama

class TusasAgentWorkflow:
    def __init__(self):
        print("[AGENT] Graf Ajan Mimarisi başlatılıyor...")
        self.rag_engine = TusasRAGEngine()

    def rewrite_query(self, query: str) -> str:
        """Adım 1: Kullanıcı sorgusunu Vektör RAG için doğal dilde optimize eder."""
        print(f"\n[Ajan - Adım 1] Sorgu optimize ediliyor: '{query}'")
        prompt = (
            "Kullanıcı sorusunu vektör veritabanında arama yapmak için sade bir arama cümlesine çevir. "
            "KESİNLİKLE açıklama, not, 'Note:', parantez içi bilgi veya sohbet metni ekleme. "
            "Sadece arama metnini ver.\n\n"
            f"Soru: {query}"
        )
        try:
            response = ollama.chat(
                model="llama3", 
                messages=[{"role": "user", "content": prompt}]
            )
            optimized = response["message"]["content"].strip()
            # Modelin ekleyebileceği olası sohbet/not satırlarını ayıkla, ilk satırı al
            optimized = optimized.split('\n')[0].replace('"', '').replace("'", "")
            print(f"[Ajan] Optimize Edilen Doğal Sorgu: '{optimized}'")
            return optimized
        except Exception:
            return query 

    def run(self, user_query: str):
        """Çok adımlı ajan akışını (Agentic Workflow) çalıştırır."""
        print("="*50)
        print("AJAN İŞ AKIŞI BAŞLATILDI")
        print("="*50)

        # 1. Aşama: Doğal Dil Sorgu Optimizasyonu
        optimized_query = self.rewrite_query(user_query)

        # 2. Aşama: Akıllı Arama ve Veri Çekme (Retrieval)
        contexts = self.rag_engine.search(optimized_query, top_k=3)

        # Bağlam metinlerini oluştur
        context_text = ""
        image_references = []
        for ctx in contexts:
            context_text += f"\n--- Sayfa {ctx['page']} ({ctx['type']}) ---\n{ctx['content']}\n"
            if ctx['type'] == 'image' and ctx['image_path']:
                image_references.append(ctx['image_path'])

        # Hızlı LLM Hakem Kontrolü (Relevancy Check)
        hakem_prompt = (
            "Sen bir RAG doğrulama hakemisin. Sana bir kullanıcı sorusu ve bu soruyu yanıtlamak için "
            "belgeden çekilen metinler (bağlam) verilecek.\n"
            "Soru: " + user_query + "\n"
            "Bağlam:\n" + context_text + "\n\n"
            "Bu bağlam, kullanıcının sorusunu yanıtlamak için yeterli ve ilgili mi? "
            "Sadece 'EVET' veya 'HAYIR' yaz."
        )
        
        hakem_yanit = ollama.chat(
            model="llama3",
            messages=[{"role": "user", "content": hakem_prompt}]
        )["message"]["content"].strip().upper()

        print(f"[Ajan Hakem Kararı]: {hakem_yanit}")

        if "HAYIR" in hakem_yanit or not contexts:
            return (
                "Üzgünüm, yüklediğiniz teknik belgede bu soruyla ilgili herhangi bir bilgiye ulaşılamadı. "
                "Lütfen belgenin kapsamına uygun bir soru sorun.", 
                []
            )

        # 3. Aşama: Nihai Yanıt Sentezi (Katı Türkçe Kilidi)
        system_prompt = (
            "Sen TUSAŞ üst düzey belge analiz ve AR-GE asistanısın. "
            "Kullanıcının sorusunu **kesinlikle ve yalnızca akıcı, teknik bir Türkçe ile** yanıtla. "
            "Asla 'Context:', 'Response:' gibi İngilizce kalıplar veya etiketler kullanma. "
            "Yanıtına doğrudan Türkçe metinle başla. İngilizce bağlamdaki tüm teknik terimleri "
            "Türkçeye çevirerek profesyonel bir mühendislik raporu gibi sentezle."
        )
        user_prompt = f"Bağlam:\n{context_text}\n\nOrijinal Soru: {user_query}"

        print("[Ajan - Adım 3] Ollama (Llama-3) nihai yanıtı sentezliyor...")
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
    test_soru = "İstenen nedir?" 
    yanit, gorseller = agent.run(test_soru)
    print("\n" + "="*50)
    print("AJANIN NİHAİ YANITI:")
    print(yanit)
    print("="*50)