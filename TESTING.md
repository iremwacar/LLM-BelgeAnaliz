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