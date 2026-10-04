import os
import sys
import ollama
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

class TusasRAGEngine:
    def __init__(self, collection_name="tusas_doc_collection", db_path="./qdrant_data"):
        print("[RAG] BGE-M3 Vektör Motoru ve Qwen2.5 Sentez Motoru başlatılıyor...")
        self.model = SentenceTransformer('BAAI/bge-m3', model_kwargs={"use_safetensors": True})
        self.client = QdrantClient(path=db_path)
        self.collection_name = collection_name

    def search(self, query: str, top_k=6):
        print(f"\n[Arama Yapılıyor]: '{query}'")
        query_vector = self.model.encode(query).tolist()
        
        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True
        )
        
        retrieved_contexts = []
        for result in search_result.points:
            payload = result.payload
            retrieved_contexts.append({
                "page": payload.get("page", "Genel"),
                "type": payload.get("type", "text"),
                "content": payload.get("content", ""),
                "image_path": payload.get("image_path", ""),
                "score": result.score
            })
            
        return retrieved_contexts

    def generate_answer(self, query: str):
        contexts = self.search(query, top_k=6)
        
        context_text = ""
        image_references = []
        for ctx in contexts:
            context_text += f"\n--- [Kaynak/Sayfa {ctx['page']} - Tip: {ctx['type'].upper()} | Skor: {ctx.get('score', 0):.2f}] ---\n{ctx['content']}\n"
            if ctx['image_path']:
                image_references.append(ctx['image_path'])

        system_prompt = (
            "Sen kıdemli bir yapay zeka AR-GE mühendisi ve belge analiz asistanısın. "
            "KESİN KURALLAR:\n"
            "1. Dil Eşleme (Language Matching): Kullanıcının soruyu yönelttiği DİL HANGİSİYSE, yanıtı da KESİNLİKLE aynı dilde vereceksin (Türkçe soruya tamamen Türkçe, İngilizce soruya tamamen İngilizce yanıtla).\n"
            "2. Bilgi Yoksa (Anti-Hallucination): Eğer aradığın bilgi sağlanan bağlamda kesinlikle yer almıyorsa, yorum yapmadan KESİNLİKLE şu dildeki standart kalıbı kullan:\n"
            "   - Türkçe sorular için: 'Belgede bu bilgiye ulaşılamadı.'\n"
            "   - İngilizce sorular için: 'The requested information is not available in the document.'\n"
            "3. Üslup: Teknik, profesyonel, maddeler halinde ve doğrudan konuya giren bir yapı benimse."
        )

        user_prompt = f"Bağlam:\n{context_text}\n\nKullanıcı Sorusu: {query}"

        print("[LLM] Qwen2.5-7B-Instruct yanıt üretiyor...")
        try:
            response = ollama.chat(
                model="qwen2.5:7b-instruct",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response["message"]["content"], image_references
        except Exception as e:
            return f"LLM Hata: {str(e)}", []