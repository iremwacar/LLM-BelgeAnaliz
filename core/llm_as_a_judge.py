import os
import json
import re
import ollama
from rag_engine import TusasRAGEngine

# =====================================================================
# KAPSAMLI TEST SENARYOLARI (Belge Başına 8 Soru Çeşidi x 2 Dil = 16 Test)
# Data klasöründeki her bir ana belge türüne özel test setleri hazırlanmıştır.
# =====================================================================

TEST_SUITE = {
    "Transformer_Makalesi_1706.03762v7.pdf": [
        {"type": "1_Anlamsiz", "tr": "Dikkat mekanizması (Attention) ile Mars yüzeyindeki su kaynakları arasında nasıl bir bağ vardır?", "en": "What is the relationship between the self-attention mechanism and water resources on Mars?"},
        {"type": "2_Global", "tr": "Bu makalenin literatüre kattığı en büyük temel yenilik (ana vizyon) nedir?", "en": "What is the primary fundamental innovation and vision contributed by this paper to the literature?"},
        {"type": "3_Detay", "tr": "Eğitim (training) sırasında Adam optimizatörü için kullanılan beta1, beta2 ve epsilon değerleri tam olarak nedir?", "en": "What are the exact values of beta1, beta2, and epsilon used for the Adam optimizer during training?"},
        {"type": "4_Lokal", "tr": "Multi-Head Attention mekanizmasında h (kafa sayısı) kaç olarak belirlenmiştir?", "en": "What is the exact value of h (number of heads) defined in the Multi-Head Attention mechanism?"},
        {"type": "5_Karmasik", "tr": "Scaled Dot-Product Attention'daki ölçeklendirme faktörü (1/sqrt(dk)) neden gereklidir ve kullanılmadığında ne tür sorunlar ortaya çıkar?", "en": "Why is the scaling factor (1/sqrt(dk)) necessary in Scaled Dot-Product Attention, and what issues arise if it's omitted?"},
        {"type": "6_Sentez", "tr": "Bu belgedeki mimariyi dikkate alarak, self-attention mekanizmasının uzun hukuki sözleşmeleri analiz etmede neden RNN'lerden daha başarılı olabileceğini sentezle.", "en": "Synthesize the architecture in this document to explain why the self-attention mechanism might be more successful than RNNs in analyzing long legal contracts."},
        {"type": "7_Karsilastirma", "tr": "Transformer mimarisi ile geleneksel Recurrent Neural Networks (RNN) modellerinin eğitim süresi ve paralelleştirme kapasitelerini kıyasla.", "en": "Compare the training time and parallelization capacities of the Transformer architecture with traditional Recurrent Neural Networks (RNNs)."},
        {"type": "8_Tablo_Verisi", "tr": "Makaledeki tablolara göre, WMT 2014 English-to-German (EN-DE) çeviri görevinde 'Transformer (big)' modelinin elde ettiği tam BLEU skoru kaçtır?", "en": "According to the tables in the paper, what is the exact BLEU score achieved by the 'Transformer (big)' model on the WMT 2014 English-to-German (EN-DE) translation task?"}
    ],
    "Banka_Karti_Sozlesmesi.pdf": [
        {"type": "1_Anlamsiz", "tr": "Banka kartı sözleşmesindeki kurallara göre uzay mekiği kiraladığımda ne kadar mil kazanırım?", "en": "According to the rules in the bank card agreement, how many miles do I earn when I rent a space shuttle?"},
        {"type": "2_Global", "tr": "Bu belgenin yasal olarak temel amacı ve düzenlediği ana konular nelerdir?", "en": "What is the primary legal purpose of this document and what main topics does it regulate?"},
        {"type": "3_Detay", "tr": "Sadece banka kartı kullanan bir müşterinin mil kazanabilmesi için gereken aylık net alışveriş alt sınırı tam olarak kaç TL'dir?", "en": "What is the exact minimum monthly net shopping limit in TL required for a customer using only a debit card to earn miles?"},
        {"type": "4_Lokal", "tr": "Miles&Smiles kartlarında mil kazanılamayacak işlem türleri (istisnalar) nelerdir?", "en": "What are the specific transaction types (exceptions) where miles cannot be earned on Miles&Smiles cards?"},
        {"type": "5_Karmasik", "tr": "Sözleşmeye göre, müşteri limitini aşan bir harcama yapıp daha sonra bu harcamayı iptal ederse mil kazanım süreci nasıl işler?", "en": "According to the agreement, how does the mile earning process work if a customer makes an expenditure exceeding their limit and later cancels this transaction?"},
        {"type": "6_Sentez", "tr": "Sözleşmedeki mil kazanım kuralları ile iade/iptal süreçlerini sentezleyerek, bankanın haksız mil kazanımını nasıl engellediğini açıkla.", "en": "Synthesize the mile earning rules and return/cancellation processes in the agreement to explain how the bank prevents unfair mile accumulation."},
        {"type": "7_Karsilastirma", "tr": "Ek kart hamilinin mil kazanım kuralları ile asıl kart hamilinin kuralları arasında bir fark var mıdır?", "en": "Is there a difference between the mile earning rules for a supplementary cardholder and the primary cardholder?"},
        {"type": "8_Tablo_Verisi", "tr": "Belgedeki tablo veya maddelere göre, 'Gecikme Faizi' veya 'Ücretler' gibi kısımlarda belirtilen net bir oran var mı?", "en": "According to the tables or clauses in the document, is there a specific rate mentioned in sections like 'Late Interest' or 'Fees'?"}
    ],
    "Biyoloji_Gorselleri_veya_Semalar": [
        {"type": "1_Anlamsiz", "tr": "Mitokondri içerisine uçak motoru yerleştirirsek enerji üretimi ne kadar artar?", "en": "If we place an aircraft engine inside mitochondria, how much will energy production increase?"},
        {"type": "2_Global", "tr": "Bu biyoloji notu/görseli genel olarak hücredeki hangi yapılara ve süreçlere odaklanmaktadır?", "en": "What cellular structures and processes does this biology note/image generally focus on?"},
        {"type": "3_Detay", "tr": "Mitokondri sıvısına ne denir ve bu sıvının içinde hangi moleküller bulunur?", "en": "What is the mitochondrial fluid called, and what molecules are found within this fluid?"},
        {"type": "4_Lokal", "tr": "Peroksizomlar zehirli atık olan hidrojen peroksiti parçalamak için hangi enzimi kullanır?", "en": "Which enzyme do peroxisomes use to break down the toxic waste hydrogen peroxide?"},
        {"type": "5_Karmasik", "tr": "Mitokondri ve Peroksizom organellerinin her ikisinde de ortak olarak tüketilen madde nedir ve nasıl kullanılır?", "en": "What substance is commonly consumed in both Mitochondria and Peroxisome organelles, and how is it used?"},
        {"type": "6_Sentez", "tr": "Görseldeki bilgileri sentezleyerek, oksijenin hücre organellerindeki enerji ve temizlik süreçlerindeki kritik rolünü açıkla.", "en": "Synthesize the information in the image to explain the critical role of oxygen in energy and cleanup processes within cell organelles."},
        {"type": "7_Karsilastirma", "tr": "Mitokondri ve Peroksizom arasındaki zar yapısı (tek/çift zar) ve DNA bulundurma durumlarını kıyasla.", "en": "Compare Mitochondria and Peroxisome in terms of membrane structure (single/double membrane) and the presence of DNA."},
        {"type": "8_Tablo_Verisi", "tr": "Görseldeki şemada/çizimde mitokondrinin dış kısımlarını gösteren etiketlerde 'İç Zar', 'Dış Zar' dışında hangi yapılar işaretlenmiştir?", "en": "In the diagram/drawing in the image, what structures other than 'Inner Membrane' and 'Outer Membrane' are labeled showing the parts of the mitochondria?"}
    ]
}

class LLMasAJudge:
    def __init__(self, judge_model="qwen2.5:7b-instruct"):
        print("[SİSTEM] RAG Motoru ve LLM Hakem Motoru Başlatılıyor...")
        self.rag_engine = TusasRAGEngine()
        self.judge_model = judge_model

    def evaluate(self, query, context, answer, expected_language):
        judge_prompt = f"""
Sen tarafsız, son derece katı ve analitik bir yapay zeka kalite kontrol (LLM-as-a-Judge) hakemisin.
Görevin, bir RAG (Retrieval-Augmented Generation) sisteminin ürettiği yanıtı, verilen bağlama (context) ve soruya (query) göre 3 kriterde değerlendirmektir.

[KULLANICI SORUSU]
{query}

[RAG SİSTEMİNE SAĞLANAN BAĞLAM (CONTEXT)]
{context}

[RAG SİSTEMİNİN ÜRETTİĞİ YANIT]
{answer}

DEĞERLENDİRME KRİTERLERİ (Her biri 0-10 arası puanlanacak):
1. Gerçekliğe Uygunluk (Faithfulness): Yanıt sadece ve sadece bağlamdaki bilgilere mi dayanıyor? RAG sistemi halüsinasyon yapmış mı? (Bilgi bağlamda yoksa ve RAG 'Belgede bu bilgiye ulaşılamadı' dediyse 10/10 ver).
2. Soruya Uygunluk (Answer Relevance): Yanıt doğrudan soruyu adresliyor mu? Gereksiz gevezelik veya eksik bilgi var mı? (Eğer bilgi bulunamadığı için standart red yanıtı verildiyse, soruya uygunluk da 10/10'dur).
3. Dil Uyumu (Language Match): Kullanıcının sorduğu dil '{expected_language}' idi. Sistem tamamen bu dilde mi yanıt vermiş?

SADECE AŞAĞIDAKİ GİBİ GEÇERLİ BİR JSON FORMATINDA YANIT VER. BAŞKA HİÇBİR AÇIKLAMA YAZMA:
{{
    "faithfulness_score": <int>,
    "relevance_score": <int>,
    "language_score": <int>,
    "reasoning": "<Hakem olarak bu puanları neden verdiğinin profesyonel açıklaması>"
}}
"""
        try:
            response = ollama.chat(
                model=self.judge_model,
                messages=[{"role": "user", "content": judge_prompt}]
            )
            content = response["message"]["content"].strip()
            
            # Extract JSON if wrapped in markdown blocks
            match = re.search(r'\{.*?\}', content, re.DOTALL)
            if match:
                clean_json = match.group(0)
            else:
                clean_json = content
                
            result = json.loads(clean_json)
            
            # Validate types to ensure integers
            for key in ['faithfulness_score', 'relevance_score', 'language_score']:
                if not isinstance(result.get(key), int):
                    result[key] = int(result.get(key, 0))
            return result
        except Exception as e:
            return {"faithfulness_score": 0, "relevance_score": 0, "language_score": 0, "reasoning": f"Hakem başarısız veya JSON parse hatası: {str(e)} | Ham Cevap: {content[:50]}"}

    def run_benchmark(self):
        print("\n" + "="*80)
        print("🚀 KAPSAMLI BELGE BAZLI LLM-AS-A-JUDGE (RAGAS) TESTİ BAŞLIYOR")
        print("="*80)
        
        report_lines = ["# TUSAŞ MVP RAG - Belge Bazlı Kapsamlı Değerlendirme Raporu\n"]
        
        global_total_score = 0
        global_total_tests = 0

        for doc_name, test_cases in TEST_SUITE.items():
            print(f"\n{'#'*60}")
            print(f"BELGE TEST SETİ: {doc_name}")
            print(f"{'#'*60}")
            
            report_lines.append(f"\n## 📄 BELGE: {doc_name}\n")
            doc_total_score = 0
            doc_tests = 0

            for case in test_cases:
                for lang in ["tr", "en"]:
                    query = case[lang]
                    expected_lang = "Türkçe" if lang == "tr" else "İngilizce"
                    test_title = f"Tip: {case['type']} | Dil: {lang.upper()}"
                    
                    print(f"\n[Test] {test_title} -> {query}")
                    
                    # 1. RAG'dan Bağlam ve Yanıt Al
                    contexts = self.rag_engine.search(query, top_k=6)
                    context_text = "\n".join([c["content"] for c in contexts])
                    answer, refs = self.rag_engine.generate_answer(query)
                    
                    # 2. LLM Hakeme (Judge) Değerlendirt
                    eval_res = self.evaluate(query, context_text, answer, expected_lang)
                    
                    # Skor Hesaplama
                    avg_score = (eval_res['faithfulness_score'] + eval_res['relevance_score'] + eval_res['language_score']) / 3.0
                    doc_total_score += avg_score
                    doc_tests += 1
                    
                    global_total_score += avg_score
                    global_total_tests += 1
                    
                    print(f"  > Skor: {avg_score:.1f}/10.0 (F:{eval_res['faithfulness_score']} R:{eval_res['relevance_score']} L:{eval_res['language_score']})")
                    
                    # Rapor Formatı
                    report_lines.append(f"### {test_title}")
                    report_lines.append(f"**Soru:** {query}\n")
                    report_lines.append(f"**RAG Yanıtı:**\n> {answer}\n")
                    report_lines.append(f"**Puan:** {avg_score:.1f}/10 (Faithfulness: {eval_res['faithfulness_score']}, Relevance: {eval_res['relevance_score']}, Language: {eval_res['language_score']})")
                    report_lines.append(f"**Hakem Analizi:** {eval_res['reasoning']}\n")
                    report_lines.append("---\n")
            
            doc_avg = doc_total_score / doc_tests if doc_tests > 0 else 0
            report_lines.insert(report_lines.index(f"\n## 📄 BELGE: {doc_name}\n") + 1, f"**Belge Başarı Puanı:** {doc_avg:.1f} / 10.0\n")
            print(f"\n>> {doc_name} Ortalaması: {doc_avg:.1f}/10.0")

        final_avg = global_total_score / global_total_tests if global_total_tests > 0 else 0
        report_lines.insert(1, f"**Sistem Genel Başarı Puanı:** {final_avg:.1f} / 10.0\n")
        
        with open("rag_evaluation_report.md", "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
            
        print("\n" + "="*80)
        print(f"✅ KAPSAMLI TEST TAMAMLANDI! Sistem Genel Skoru: {final_avg:.1f}/10.0")
        print("Tüm belgelerin detaylı analizi 'rag_evaluation_report.md' dosyasına kaydedildi.")
        print("="*80)

if __name__ == "__main__":
    judge = LLMasAJudge()
    judge.run_benchmark()