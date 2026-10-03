import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.rag_engine import TusasRAGEngine
import ollama

class RigorousRAGEvaluator:
    def __init__(self):
        print("[EVALUATOR] Gelişmiş ve Çeşitlendirilmiş Altın Standart Benchmark Çerçevesi Başlatılıyor...")
        self.rag_engine = TusasRAGEngine()
        
        # Soru çeşitliliği artırılmış, her üç belgeyi ve farklı kategorileri (Global, Local, Nonsensical)
        # hem Türkçe hem İngilizce olarak kapsayan kapsamlı Altın Standart (Ground Truth) test setimiz:
        self.benchmark_suite = [
            # --- 1. BELGE: 1706.03762v7.pdf (Transformer / Attention Is All You Need) ---
            {
                "doc": "data/1706.03762v7.pdf",
                "category": "Global",
                "lang": "EN",
                "query": "What is the main architecture introduced in this paper?",
                "ground_truth": "The Transformer architecture based solely on attention mechanisms, dispensing with recurrence and convolutions entirely."
            },
            {
                "doc": "data/1706.03762v7.pdf",
                "category": "Global",
                "lang": "TR",
                "query": "Bu makalede tanıtılan ana mimari nedir?",
                "ground_truth": "Yineleme (recurrence) ve evrişimleri (convolutions) tamamen ortadan kaldıran, yalnızca dikkat mekanizmalarına (attention mechanisms) dayanan Transformer mimarisidir."
            },
            {
                "doc": "data/1706.03762v7.pdf",
                "category": "Local",
                "lang": "EN",
                "query": "What are the components of the Multi-Head Attention mechanism?",
                "ground_truth": "Scaled Dot-Product Attention performed in parallel across multiple attention heads projecting queries, keys, and values."
            },
            {
                "doc": "data/1706.03762v7.pdf",
                "category": "Local",
                "lang": "TR",
                "query": "Multi-Head Attention (Çok Başlıklı Dikkat) mekanizmasının bileşenleri nelerdir?",
                "ground_truth": "Sorgu (queries), anahtar (keys) ve değerleri (values) projete eden, birden fazla dikkat başlığı üzerinde paralel olarak gerçekleştirilen Ölçeklendirilmiş Nokta Çarpım Dikkatidir (Scaled Dot-Product Attention)."
            },

            # --- 2. BELGE: Case_Study_TUSAŞ_LLM.pdf ---
            {
                "doc": "data/Case_Study_TUSAŞ_LLM.pdf",
                "category": "Global",
                "lang": "TR",
                "query": "Bu belgenin ve projenin temel amacı nedir?",
                "ground_truth": "TUSAŞ için geliştirilen RAG tabanlı belge analiz, iki katmanlı indeksleme ve LLM asistan mimarisinin vaka çalışmasını sunmaktır."
            },
            {
                "doc": "data/Case_Study_TUSAŞ_LLM.pdf",
                "category": "Global",
                "lang": "EN",
                "query": "What is the primary objective of this document and project?",
                "ground_truth": "To present the case study of a RAG-based document analysis, two-tier indexing, and LLM assistant architecture developed for TUSAŞ."
            },
            {
                "doc": "data/Case_Study_TUSAŞ_LLM.pdf",
                "category": "Local",
                "lang": "TR",
                "query": "Belgede geçen İki Katmanlı İndeksleme (Two-Tier Indexing) mimarisi nasıl çalışır?",
                "ground_truth": "Macro (global sentetik özetler) ve Micro (parçalanmış chunk'lar) olmak üzere verinin iki farklı düzeyde indekslenerek ortak vektör uzayında taranmasını sağlar."
            },
            {
                "doc": "data/Case_Study_TUSAŞ_LLM.pdf",
                "category": "Local",
                "lang": "EN",
                "query": "How does the Two-Tier Indexing architecture work in the document?",
                "ground_truth": "It organizes data into Macro (synthetic global summaries) and Micro (raw chunks) tiers to be searched simultaneously in a unified vector space."
            },

            # --- 3. BELGE: TUSAŞ_2024_Sürdürülebilirlik_Raporu_TR.pdf ---
            {
                "doc": "data/TUSAŞ_2024_Sürdürülebilirlik_Raporu_TR.pdf",
                "category": "Global",
                "lang": "TR",
                "query": "TUSAŞ'ın 2024 sürdürülebilirlik raporunda odaklandığı ana stratejik alanlar nelerdir?",
                "ground_truth": "Çevresel etkilerin azaltılması, karbon ayak izinin düşürülmesi, havacılıkta yeşil dönüşüm ve toplumsal sürdürülebilirlik stratejileridir."
            },
            {
                "doc": "data/TUSAŞ_2024_Sürdürülebilirlik_Raporu_TR.pdf",
                "category": "Global",
                "lang": "EN",
                "query": "What are the main strategic sustainability focus areas of TUSAŞ in the 2024 report?",
                "ground_truth": "Reduction of environmental impacts, lowering carbon footprint, green transformation in aerospace, and social sustainability strategies."
            },
            {
                "doc": "data/TUSAŞ_2024_Sürdürülebilirlik_Raporu_TR.pdf",
                "category": "Local",
                "lang": "TR",
                "query": "Raporda belirtilen karbon emisyonu azaltım hedefleri veya metrikleri nelerdir?",
                "ground_truth": "Sera gazı emisyonlarının azaltılması, enerji verimliliği projeleri ve çevre yönetim sistemleri metrikleridir."
            },

            # --- 4. ANLAMSIZ / NEGATİF TESTLER (Hallucination / Reddetme Testi) ---
            {
                "doc": "data/1706.03762v7.pdf",
                "category": "Nonsensical",
                "lang": "EN",
                "query": "What was the quantum entanglement coefficient used in the Transformer model in 2028?",
                "ground_truth": "Belgede bu bilgiye ulaşılamadı."
            },
            {
                "doc": "data/Case_Study_TUSAŞ_LLM.pdf",
                "category": "Nonsensical",
                "lang": "TR",
                "query": "TUSAŞ'ın 2030 yılında uzaya fırlatacağı roketin yakıt kapasitesi kaç tondur?",
                "ground_truth": "Belgede bu bilgiye ulaşılamadı."
            }
        ]

    def evaluate(self):
        print("\n" + "="*80)
        print("ÇEŞİTLENDİRİLMİŞ GERÇEKÇİ RAG PERFORMANS BENCHMARK TESTİ (GROUND TRUTH)")
        print("="*80)
        
        results = []
        total_score = 0

        for idx, item in enumerate(self.benchmark_suite):
            print(f"\n[Test {idx+1}/{len(self.benchmark_suite)}] Belge: {os.path.basename(item['doc'])} | Kategori: {item['category']} ({item['lang']})")
            print(f"Soru: {item['query']}")
            print(f"Beklenen (Ground Truth): {item['ground_truth']}")

            # RAG Motoru ile yanıt üret
            answer, _ = self.rag_engine.generate_answer(item['query'])
            print(f"Sistem Yanıtı: {answer}")

            # Hakem LLM ile Ground Truth'a göre kıyasla
            score, reason = self.judge_against_ground_truth(item['query'], item['ground_truth'], answer, item['category'])
            print(f"Hakem Puanı: {score} | Gerekçe: {reason}")
            
            total_score += score
            results.append({
                "doc": item['doc'],
                "category": item['category'],
                "lang": item['lang'],
                "query": item['query'],
                "ground_truth": item['ground_truth'],
                "system_answer": answer.replace("\n", " "),
                "score": score,
                "reason": reason
            })

        # Sonuç Tablosunu Yazdır
        self.print_markdown_table(results, total_score / len(self.benchmark_suite) * 100)

    def judge_against_ground_truth(self, query, gt, answer, category):
        prompt = f"""
Sen tarafsız ve katı kuralları olan kıdemli bir RAG Hakemisin (LLM-as-a-Judge).
Sistemin verdiği yanıtı, uzmanın yazdığı 'Altın Standart (Ground Truth)' yanıtla karşılaştır.

Soru: {query}
Altın Standart (Beklenen): {gt}
Sistemin Ürettiği Yanıt: {answer}
Kategori: {category}

Değerlendirme Kriterleri:
- Eğer kategori "Nonsensical" ise, sistem uydurma yapmayıp bilginin olmadığını ("Belgede bu bilgiye ulaşılamadı") belirttiyse Puan = 1.0, uydurduysa Puan = 0.0.
- Eğer kategori "Global" veya "Local" ise, sistem yanıtı Altın Standart ile örtüşen, doğru ve eksiksiz bir şekilde verdiyse Puan = 1.0, kısmen yanlış veya eksikse Puan = 0.5, tamamen alakasız veya yanlışsa Puan = 0.0.

Sadece ve sadece JSON formatında şu çıktıyı ver:
{{"score": 1.0, "reason": "Kısa gerekçe"}}
"""
        try:
            res = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}])
            content = res["message"]["content"].strip()
            if "{" in content and "}" in content:
                data = json.loads(content[content.find("{"):content.rfind("}")+1])
                return float(data.get("score", 0.0)), data.get("reason", "Gerekçe yok")
        except Exception:
            pass
        return 0.0, "Değerlendirme hatası"

    def print_markdown_table(self, results, overall_accuracy):
        print("\n" + "="*80)
        print("DETAYLI TEST SONUÇ TABLOSU (BENCHMARK REPORT)")
        print("="*80)
        print("| Belge | Kategori | Dil | Soru | Altın Standart (GT) | Sistem Yanıtı | Puan |")
        print("|---|---|---|---|---|---|---|")
        for r in results:
            doc_short = os.path.basename(r['doc'])
            print(f"| {doc_short} | {r['category']} | {r['lang']} | {r['query']} | {r['ground_truth']} | {r['system_answer'][:70]}... | {r['score']} |")
        print("="*80)
        print(f"Net Sistem Başarı Skoru (Ground Truth Accuracy): %{overall_accuracy:.1f}")
        print("="*80)

if __name__ == "__main__":
    evaluator = RigorousRAGEvaluator()
    evaluator.evaluate()