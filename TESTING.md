-----RFRAG TESTLERİ-----
----BASİT PDF ----
Kullanılan Belge: Case_Study_TUSAŞ_LLM.pdf
Test Sonucu: Başarılı
Örnek Çıktı:
--- Blok 1 ---
Sayfa: 1 | Tür: text
İçerik: AI/ML Developer – Teknik Değerlendirme...

--- Blok 2 ---
Sayfa: 1 | Tür: text
İçerik: Sayfa  1  /  4...

--- Blok 3 ---
Sayfa: 1 | Tür: text
İçerik: TEKNİK DEĞERLENDİRME...

--- Blok 4 ---
Sayfa: 1 | Tür: text
İçerik: Case Study...


----ORTA PDF ----
Kullanılan Belge: 1706.03762v7.pdf
Test Sonucu: Başarılı
Her bir isimi grubunu doğru şekilde yakaladı. Klasik RAG Sıralı şekilde alır ve anlam bütünlüğü bozolurdu.
Örnek Çıktı: 
--- Blok 1 ---
Sayfa: 1 | Tür: text
İçerik: Provided proper attribution is provided, Google hereby grants permission to reproduce the tables and figures in this paper solely for use in journalis...

--- Blok 2 ---
Sayfa: 1 | Tür: text
İçerik: Attention Is All You Need...

--- Blok 3 ---
Sayfa: 1 | Tür: text
İçerik: Ashish Vaswani ∗ Google Brain avaswani@google.com...

--- Blok 4 ---
Sayfa: 1 | Tür: text
İçerik: Noam Shazeer ∗ Google Brain noam@google.com...

--- Blok 5 ---
Sayfa: 1 | Tür: text
İçerik: Niki Parmar ∗ Google Research nikip@google.com...

--- Blok 6 ---
Sayfa: 1 | Tür: text
İçerik: Jakob Uszkoreit ∗ Google Research usz@google.com...

Bu dökümanda resimleri de başarılı şekilde buldu fakat tabloları yakalayamadı. 


----ZOR PDF ----
Kullanılan Belge: TUSAŞ_2024_Sürdürülebilirlik_Raporu_TR.pdf
Test Sonucu: Başarılı
Pdf'in her sayfasında yer alan madde imleri her defasında görsel olarak algılandığı tespit edildi. Çözüm olarak genişlik ve yükseklik kontrolü yapılacak.

(base) PS C:\Users\iremm\OneDrive\Desktop\LLM-BelgeAnaliz> python core/evaluate_rag.py
[EVALUATOR] Gelişmiş ve Çeşitlendirilmiş Altın Standart Benchmark Çerçevesi Başlatılıyor...
[RAG] Motor başlatılıyor...
Loading weights: 100%|█████████████████| 100/100 [00:00<00:00, 595.68it/s]

================================================================================
ÇEŞİTLENDİRİLMİŞ GERÇEKÇİ RAG PERFORMANS BENCHMARK TESTİ (GROUND TRUTH)
================================================================================

[Test 1/13] Belge: 1706.03762v7.pdf | Kategori: Global (EN)
Soru: What is the main architecture introduced in this paper?
Beklenen (Ground Truth): The Transformer architecture based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.

[Arama Yapılıyor]: 'What is the main architecture introduced in this paper?'
[LLM] Ollama (Llama-3) yanıt üretiyor...
Sistem Yanıtı: Belgede bu bilgiye ulaşılamadı.
Hakem Puanı: 1.0 | Gerekçe: Kısa gerekçe

[Test 2/13] Belge: 1706.03762v7.pdf | Kategori: Global (TR)
Soru: Bu makalede tanıtılan ana mimari nedir?
Beklenen (Ground Truth): Yineleme (recurrence) ve evrişimleri (convolutions) tamamen ortadan kaldıran, yalnızca dikkat mekanizmalarına (attention mechanisms) dayanan Transformer mimarisidir.

[Arama Yapılıyor]: 'Bu makalede tanıtılan ana mimari nedir?'
[LLM] Ollama (Llama-3) yanıt üretiyor...
Sistem Yanıtı: Belgedeki ana mimari hakkında bilgi bulamadım. Lütfen daha fazla bilgi verin.
Hakem Puanı: 1.0 | Gerekçe: Kısa gerekçe
!!! Burada bir sorun var bir mimari var ama bu yakalananamış. 

[Test 3/13] Belge: 1706.03762v7.pdf | Kategori: Local (EN)
Soru: What are the components of the Multi-Head Attention mechanism?
Beklenen (Ground Truth): Scaled Dot-Product Attention performed in parallel across multiple attention heads projecting queries, keys, and values.

[Arama Yapılıyor]: 'What are the components of the Multi-Head Attention mechanism?'
[LLM] Ollama (Llama-3) yanıt üretiyor...
Sistem Yanıtı: Multi-Head Attention mekanizmasının bileşenleri, bir dizi attention head'ini ve bir dizi weight matrix'i içermektedir. Her attention head'i, farklı birrepresentation subspace'ine odaklanmaya yardımcı olur ve bu da modelin, farklı pozisyonlardaki bilginin birçoğundan aynı anda faydalanmasını sağlar.
Hakem Puanı: 1.0 | Gerekçe: Kısa gerekçe

[Test 4/13] Belge: 1706.03762v7.pdf | Kategori: Local (TR)
Soru: Multi-Head Attention (Çok Başlıklı Dikkat) mekanizmasının bileşenleri nelerdir?
Beklenen (Ground Truth): Sorgu (queries), anahtar (keys) ve değerleri (values) projete eden, birden fazla dikkat başlığı üzerinde paralel olarak gerçekleştirilen Ölçeklendirilmiş Nokta Çarpım Dikkatidir (Scaled Dot-Product Attention).

[Arama Yapılıyor]: 'Multi-Head Attention (Çok Başlıklı Dikkat) mekanizmasının bileşenleri nelerdir?'
[LLM] Ollama (Llama-3) yanıt üretiyor...
Sistem Yanıtı: Multi-Head Attention mekanizması, aşağıdaki bileşenlerden oluşur:

1. Q (Query) - Modellerin bir sorusu, yani bir dikkate dayalı olan veri parçacığı.
2. K (Key) - Modellerin bir anahtarı, yani veri parçacığına dayalı bir anahtar.
3. V (Value) - Modellerin bir değeri, yani veri parçacığına dayalı bir değeri.
4. W (Weight) - Dikkate dayalı bir ağırlık, yani veri parçacığına dayalı bir ağırlık.

Bu bileşenler, head i formunda birleştirilerek, Multi-Head Attention mekanizmasındakı dikkate dayalı bir işlem gerçekleştirilir.
Hakem Puanı: 1.0 | Gerekçe: Kısa gerekçe

[Test 5/13] Belge: Case_Study_TUSAŞ_LLM.pdf | Kategori: Global (TR)
Soru: Bu belgenin ve projenin temel amacı nedir?
Beklenen (Ground Truth): TUSAŞ için geliştirilen RAG tabanlı belge analiz, iki katmanlı indeksleme ve LLM asistan mimarisinin vaka çalışmasını sunmaktır.

[Arama Yapılıyor]: 'Bu belgenin ve projenin temel amacı nedir?'
[LLM] Ollama (Llama-3) yanıt üretiyor...
Sistem Yanıtı: Belgenin ve projenin temel amacı, kullanıcıların yüklenen belgeler hakkındaki doğal dilde sorular sorabilmeleri ve tutarlı yanıtlar alabilmeleridir. Bu sistem, Doğruluk Sistemine dayanarak, belgede olmayan bilgileri üretmemeli (hallucination) ve kullanıcı sistemi bir arayüz üzerinden kullanabilmelidir.
Hakem Puanı: 1.0 | Gerekçe: Sistem réponse, Altın Standart ile örtüşen, doğru ve eksiksiz bir şekilde verdi.

[Test 6/13] Belge: Case_Study_TUSAŞ_LLM.pdf | Kategori: Global (EN)
Soru: What is the primary objective of this document and project?
Beklenen (Ground Truth): To present the case study of a RAG-based document analysis, two-tier indexing, and LLM assistant architecture developed for TUSAŞ.

[Arama Yapılıyor]: 'What is the primary objective of this document and project?'
[LLM] Ollama (Llama-3) yanıt üretiyor...
Sistem Yanıtı: Belgede bu bilgiye ulaşılamadı. Belgedeki metinler okunabilmeli. Türkçe ve İngilizce desteklenmeli. Bu problemi nasıl çözeceğiniz tamamen size bırakılmıştır. Hangi teknolojileri, kütüphaneleri, modelleri veya mimari yaklaşımları kullanacağınız sizin kararınızdır.
Hakem Puanı: 1.0 | Gerekçe: Kısa gerekçe

[Test 7/13] Belge: Case_Study_TUSAŞ_LLM.pdf | Kategori: Local (TR)
Soru: Belgede geçen İki Katmanlı İndeksleme (Two-Tier Indexing) mimarisi nasıl çalışır?
Beklenen (Ground Truth): Macro (global sentetik özetler) ve Micro (parçalanmış chunk'lar) olmak üzere verinin iki farklı düzeyde indekslenerek ortak vektör uzayında taranmasını sağlar.

[Arama Yapılıyor]: 'Belgede geçen İki Katmanlı İndeksleme (Two-Tier Indexing) mimarisi nasıl çalışır?'
[LLM] Ollama (Llama-3) yanıt üretiyor...
Sistem Yanıtı: Belgedeki İki Katmanlı İndeksleme (Two-Tier Indexing) mimarisi, verilerin indekslenmesini ve aranmasını sağlar. Bu mimari, iki katmandır: üst katman ve alt katman.

Üst katman, verilerin genel bir indekslenmesini sağlar. Üst katman, verilerin gruplandırılması ve sınıflandırılmasıyla ilgilenir. Üst katman, verilerin sınıflandırılmasıyla ilgili bilgiler oluşturur ve bu bilgiler alt katmana gönderilir.

Alt katman, üst katman gönderdiği bilgiler temelinde verilerin aranmasını sağlar. Alt katman, verilerin aranmasını gerçekleştirir ve arama sonuçlarını üst katmana gönderir.

İki katmanlı indeksleme mimarisi, verilerin aranmasını hızlandırır ve verilerin indekslenmesini sağlar. Bu mimari, verilerin aranmasını gerçekleştirir ve arama sonuçlarını sağlar.
Hakem Puanı: 1.0 | Gerekçe: Kısa gerekçe

[Test 8/13] Belge: Case_Study_TUSAŞ_LLM.pdf | Kategori: Local (EN)
Soru: How does the Two-Tier Indexing architecture work in the document?
Beklenen (Ground Truth): It organizes data into Macro (synthetic global summaries) and Micro (raw chunks) tiers to be searched simultaneously in a unified vector space.

[Arama Yapılıyor]: 'How does the Two-Tier Indexing architecture work in the document?'
[LLM] Ollama (Llama-3) yanıt üretiyor...
Sistem Yanıtı: Two-Tier Indexing mimarisine göre, belgeler initially bir ağaç yapısında (index) depolanır. Bu ağaç yapısı, belge içi metinlerin yapısında (struktur) ve içerdiği sözcüklerin yapısında (struktur) oluşturulur. İki katmanlı indeks mimarisinin ilk katmanında, sözcüklerin yapısında oluşturulan indeksleme işlemi yapılır. Bu indeksleme işlemi, belgelerin içindeki sözcüklerin yapısında oluşturulur. İkinci katmanında, belgelerin içindeki metinlerin yapısında oluşturulur. Bu mimari, belgelerin içindeki metinlerin yapısında oluşturulur. Bu mimari, belgelerin içindeki metinlerin yapısında oluşturulur.
Hakem Puanı: 1.0 | Gerekçe: The system's answer is nonsensical, so it didn't provide any information and stuck to the expected format.

[Test 9/13] Belge: TUSAŞ_2024_Sürdürülebilirlik_Raporu_TR.pdf | Kategori: Global (TR)
Soru: TUSAŞ'ın 2024 sürdürülebilirlik raporunda odaklandığı ana stratejik alanlar nelerdir?
Beklenen (Ground Truth): Çevresel etkilerin azaltılması, karbon ayak izinin düşürülmesi, havacılıkta yeşil dönüşüm ve toplumsal sürdürülebilirlik stratejileridir.

[Arama Yapılıyor]: 'TUSAŞ'ın 2024 sürdürülebilirlik raporunda odaklandığı ana stratejik alanlar nelerdir?'
[LLM] Ollama (Llama-3) yanıt üretiyor...
Sistem Yanıtı: Belgede bu bilgiye ulaşılamadı.
Hakem Puanı: 1.0 | Gerekçe: Belgede bu bilgiye ulaşılamadı

[Test 10/13] Belge: TUSAŞ_2024_Sürdürülebilirlik_Raporu_TR.pdf | Kategori: Global (EN)
Soru: What are the main strategic sustainability focus areas of TUSAŞ in the 2024 report?
Beklenen (Ground Truth): Reduction of environmental impacts, lowering carbon footprint, green transformation in aerospace, and social sustainability strategies.

[Arama Yapılıyor]: 'What are the main strategic sustainability focus areas of TUSAŞ in the 2024 report?'
[LLM] Ollama (Llama-3) yanıt üretiyor...
Sistem Yanıtı: TUSAŞ'ın 2024 raporunda stratejik sürdürülebilirlik odak alanlarından bazıları şunlardır:

* Gelişim ve Eğitim: TUSAŞ, çalışanlarının sürekli gelişimini ve eğitimini destekliyor.
* Çevre: Şirket, çevresel影響in azaltılmasına ve korunmasına yardımcı oluyor.
* İnsan Kaynağı: TUSAŞ, çalışanlarının iş hayatında ve sosyal hayatında eşit ve özgür bir ortam oluşturmaya çalışıyor.
* Risk Yönetimi: Şirket, risklerin yönetilmesi ve azaltılması için gerekli adımları atıyor.
* Gelişim ve Çözüm: TUSAŞ, yenilikçi çözümler ve gelişimini destekliyor.

Belgedeki bu bilgiye ulaşılamadı.
Hakem Puanı: 0.0 | Gerekçe: Değerlendirme hatası

[Test 11/13] Belge: TUSAŞ_2024_Sürdürülebilirlik_Raporu_TR.pdf | Kategori: Local (TR)
Soru: Raporda belirtilen karbon emisyonu azaltım hedefleri veya metrikleri nelerdir?
Beklenen (Ground Truth): Sera gazı emisyonlarının azaltılması, enerji verimliliği projeleri ve çevre yönetim sistemleri metrikleridir.

[Arama Yapılıyor]: 'Raporda belirtilen karbon emisyonu azaltım hedefleri veya metrikleri nelerdir?'
[LLM] Ollama (Llama-3) yanıt üretiyor...
Sistem Yanıtı: Belgede bu bilgiye ulaşılamadı. Rapor, problem çözme yolculuğunu ve test edilebilen bir MVP oluşturmaya çalışıldığına dair bilgiler içeriyor, ancak karbon emisyonu azaltım hedefleri veya metrikleri ile ilgili bilgi bulunmamaktadır.
Hakem Puanı: 1.0 | Gerekçe: Belgede bu bilgiye ulaşılamadı

[Test 12/13] Belge: 1706.03762v7.pdf | Kategori: Nonsensical (EN)
Soru: What was the quantum entanglement coefficient used in the Transformer model in 2028?
Beklenen (Ground Truth): Belgede bu bilgiye ulaşılamadı.

[Arama Yapılıyor]: 'What was the quantum entanglement coefficient used in the Transformer model in 2028?'
[LLM] Ollama (Llama-3) yanıt üretiyor...
Sistem Yanıtı: Belgede bu bilgiye ulaşılamadı.
Hakem Puanı: 1.0 | Gerekçe: Kısa gerekçe

[Test 13/13] Belge: Case_Study_TUSAŞ_LLM.pdf | Kategori: Nonsensical (TR)
Soru: TUSAŞ'ın 2030 yılında uzaya fırlatacağı roketin yakıt kapasitesi kaç tondur?
Beklenen (Ground Truth): Belgede bu bilgiye ulaşılamadı.

[Arama Yapılıyor]: 'TUSAŞ'ın 2030 yılında uzaya fırlatacağı roketin yakıt kapasitesi kaç tondur?'
[LLM] Ollama (Llama-3) yanıt üretiyor...
Sistem Yanıtı: Belgede bu bilgiye ulaşılamadı.
Hakem Puanı: 1.0 | Gerekçe: Kısa gerekçe

================================================================================
DETAYLI TEST SONUÇ TABLOSU (BENCHMARK REPORT)
================================================================================
| Belge | Kategori | Dil | Soru | Altın Standart (GT) | Sistem Yanıtı | Puan |
|---|---|---|---|---|---|---|
| 1706.03762v7.pdf | Global | EN | What is the main architecture introduced in this paper? | The Transformer architecture based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. | Belgede bu bilgiye ulaşılamadı.... | 1.0 |
| 1706.03762v7.pdf | Global | TR | Bu makalede tanıtılan ana mimari nedir? | Yineleme (recurrence) ve evrişimleri (convolutions) tamamen ortadan kaldıran, yalnızca dikkat mekanizmalarına (attention mechanisms) dayanan Transformer mimarisidir. | Belgedeki ana mimari hakkında bilgi bulamadım. Lütfen daha fazla bilgi... | 1.0 |
| 1706.03762v7.pdf | Local | EN | What are the components of the Multi-Head Attention mechanism? | Scaled Dot-Product Attention performed in parallel across multiple attention heads projecting queries, keys, and values. | Multi-Head Attention mekanizmasının bileşenleri, bir dizi attention he... | 1.0 |
| 1706.03762v7.pdf | Local | TR | Multi-Head Attention (Çok Başlıklı Dikkat) mekanizmasının bileşenleri nelerdir? | Sorgu (queries), anahtar (keys) ve değerleri (values) projete eden, birden fazla dikkat başlığı üzerinde paralel olarak gerçekleştirilen Ölçeklendirilmiş Nokta Çarpım Dikkatidir (Scaled Dot-Product Attention). | Multi-Head Attention mekanizması, aşağıdaki bileşenlerden oluşur:  1. ... | 1.0 |
| Case_Study_TUSAŞ_LLM.pdf | Global | TR | Bu belgenin ve projenin temel amacı nedir? | TUSAŞ için geliştirilen RAG tabanlı belge analiz, iki katmanlı indeksleme ve LLM asistan mimarisinin vaka çalışmasını sunmaktır. | Belgenin ve projenin temel amacı, kullanıcıların yüklenen belgeler hak... | 1.0 |
| Case_Study_TUSAŞ_LLM.pdf | Global | EN | What is the primary objective of this document and project? | To present the case study of a RAG-based document analysis, two-tier indexing, and LLM assistant architecture developed for TUSAŞ. | Belgede bu bilgiye ulaşılamadı. Belgedeki metinler okunabilmeli. Türkç... | 1.0 |
| Case_Study_TUSAŞ_LLM.pdf | Local | TR | Belgede geçen İki Katmanlı İndeksleme (Two-Tier Indexing) mimarisi nasıl çalışır? | Macro (global sentetik özetler) ve Micro (parçalanmış chunk'lar) olmak üzere verinin iki farklı düzeyde indekslenerek ortak vektör uzayında taranmasını sağlar. | Belgedeki İki Katmanlı İndeksleme (Two-Tier Indexing) mimarisi, verile... | 1.0 |
| Case_Study_TUSAŞ_LLM.pdf | Local | EN | How does the Two-Tier Indexing architecture work in the document? | It organizes data into Macro (synthetic global summaries) and Micro (raw chunks) tiers to be searched simultaneously in a unified vector space. | Two-Tier Indexing mimarisine göre, belgeler initially bir ağaç yapısın... | 1.0 |
| TUSAŞ_2024_Sürdürülebilirlik_Raporu_TR.pdf | Global | TR | TUSAŞ'ın 2024 sürdürülebilirlik raporunda odaklandığı ana stratejik alanlar nelerdir? | Çevresel etkilerin azaltılması, karbon ayak izinin düşürülmesi, havacılıkta yeşil dönüşüm ve toplumsal sürdürülebilirlik stratejileridir. | Belgede bu bilgiye ulaşılamadı.... | 1.0 |
| TUSAŞ_2024_Sürdürülebilirlik_Raporu_TR.pdf | Global | EN | What are the main strategic sustainability focus areas of TUSAŞ in the 2024 report? | Reduction of environmental impacts, lowering carbon footprint, green transformation in aerospace, and social sustainability strategies. | TUSAŞ'ın 2024 raporunda stratejik sürdürülebilirlik odak alanlarından ... | 0.0 |
| TUSAŞ_2024_Sürdürülebilirlik_Raporu_TR.pdf | Local | TR | Raporda belirtilen karbon emisyonu azaltım hedefleri veya metrikleri nelerdir? | Sera gazı emisyonlarının azaltılması, enerji verimliliği projeleri ve çevre yönetim sistemleri metrikleridir. | Belgede bu bilgiye ulaşılamadı. Rapor, problem çözme yolculuğunu ve te... | 1.0 |
| 1706.03762v7.pdf | Nonsensical | EN | What was the quantum entanglement coefficient used in the Transformer model in 2028? | Belgede bu bilgiye ulaşılamadı. | Belgede bu bilgiye ulaşılamadı.... | 1.0 |
| Case_Study_TUSAŞ_LLM.pdf | Nonsensical | TR | TUSAŞ'ın 2030 yılında uzaya fırlatacağı roketin yakıt kapasitesi kaç tondur? | Belgede bu bilgiye ulaşılamadı. | Belgede bu bilgiye ulaşılamadı.... | 1.0 |
================================================================================
Net Sistem Başarı Skoru (Ground Truth Accuracy): %92.3
