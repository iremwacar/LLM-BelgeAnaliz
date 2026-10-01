import os
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import ollama

class TusasRAGEngine:
    def __init__(self, collection_name="tusas_doc_collection", db_path="./qdrant_data"):
        print("[RAG] Motor başlatılıyor...")
        self.model = SentenceTransformer('sentence-transformers/clip-ViT-B-32-multilingual-v1')
        self.client = QdrantClient(path=db_path)
        self.collection_name = collection_name

    def search(self, query, top_k=3):
        """Kullanıcı sorgusunu vektörleştirir ve Qdrant'ta anlamsal arama yapar."""
        print(f"\n[Arama Yapılıyor]: '{query}'")
        
        # Kullanıcının metin sorgusunu vektöre çevir
        query_vector = self.model.encode(query).tolist()
        
        # Qdrant güncel yerel istemci yapısı (query_points)
        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k
        )
        
        retrieved_contexts = []
        # query_points sonucundaki .points listesini dönüyoruz
        for result in search_result.points:
            payload = result.payload
            retrieved_contexts.append({
                "page": payload.get("page"),
                "type": payload.get("type"),
                "content": payload.get("content"),
                "image_path": payload.get("image_path", ""),
                "score": result.score
            })
            
        return retrieved_contexts

    def generate_answer(self, query):
        """Bulunan bağlamları (context) LLM'e vererek Türkçe yanıt üretir."""
        contexts = self.search(query, top_k=3)
        
        context_text = ""
        image_references = []
        
        for ctx in contexts:
            context_text += f"\n--- Sayfa {ctx['page']} ({ctx['type']}) ---\n{ctx['content']}\n"
            if ctx['type'] == 'image' and ctx['image_path']:
                image_references.append(ctx['image_path'])

        system_prompt = (
            "Sen TUSAŞ belge analiz ve AR-GE asistanısın. Sana sağlanan bağlam (context) "
            "bilgilerini kullanarak kullanıcı sorusunu net, teknik ve Türkçe olarak yanıtla. "
            "Eğer bilgi bağlamda yoksa uydurma, 'Belgede bu bilgiye ulaşılamadı' de."
        )

        user_prompt = f"Bağlam:\n{context_text}\n\nSoru: {query}"

        print("[LLM] Ollama (Llama-3) yanıt üretiyor...")
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
            return f"LLM Yanıt Üretme Hatası: {str(e)}", []

# Test Bloğu
if __name__ == "__main__":
    engine = TusasRAGEngine()
    test_soru = "Attention mekanizması nedir?" 
    
    yanit, gorseller = engine.generate_answer(test_soru)
    
    print("\n" + "="*40)
    print("YANIT:")
    print(yanit)
    if gorseller:
        print("\nİlgili Görsel Referansları:", gorseller)
    print("="*40)