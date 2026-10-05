from typing import Optional
import os
import sys
import ollama
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

class TusasRAGEngine:
    def __init__(self, collection_name="tusas_doc_collection", db_path="./qdrant_data", client=None, model=None):
        print("[RAG] BGE-M3 Vektör Motoru ve Qwen2.5 Sentez Motoru başlatılıyor...")
        self.model = model or SentenceTransformer('BAAI/bge-m3', model_kwargs={"use_safetensors": True})
        self.client = client or QdrantClient(path=db_path)
        self.collection_name = collection_name

    def search(self, query: str, top_k=6, document_id: Optional[str] = None):
        print(f"\n[Arama Yapılıyor]: '{query}'")
        query_vector = self.model.encode(query).tolist()
        
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        query_filter = None
        if document_id:
            query_filter = Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            )

        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
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

    def generate_answer(self, query: str, document_id: Optional[str] = None):
        contexts = self.search(query, top_k=6, document_id=document_id)
        
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
                ],
                options={
                    "temperature": 0.1,
                    "repeat_penalty": 1.15,
                    "num_predict": 600
                }
            )
            return response["message"]["content"], image_references, contexts
        except Exception as e:
            return f"LLM Hata: {str(e)}", [], []