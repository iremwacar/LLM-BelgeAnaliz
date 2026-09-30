Öncelikle sistem incelememe konuya uygun olan makaleleri incelemek ile başladım. Bu konuda incelediğim makaleler şu şekilde;
-LocalRAG: A Privacy-Preserving Offline Framework for Multi-PDF Question Answering https://www.researchgate.net/publication/399649031_LocalRAG_A_Privacy-Preserving_Offline_Framework_for_Multi-PDF_Question_Answering/link/69631f6ec906f117f2a2e63a/download?_tp=eyJjb250ZXh0Ijp7ImZpcnN0UGFnZSI6InB1YmxpY2F0aW9uIiwicGFnZSI6InB1YmxpY2F0aW9uIn19  --->  RAG mimarisinin lokalde herhangi bir API'ye bağlı olmadan nası kurgulanabileceğini anlatmaktadır. Burada OCR ve BGE-small embedding modeli ile ilk defa karşılaştım. Daha önceden farklı embedding modelleri ile çalışmıştım fakat bu modeli duymamıştım. Bu 2 konuyu araştırmalıyım.  !!! Test ederken yalnızca PDF türündeki belgeler ile test etmemeliyim. Fazla resim içeren PDF, içeriğinde sorunun cevabı şekillendirilmiş resim, konudan bağımsız bir resim, el yazısı içeren bir döküman... Sistem resimi de analiz edebilmeli belgeden soru- cevap yapılabilecek bir resim içeriği de olabilir. Örn: Bir manzara resminde ağaçların konumu sorulabilir
OCR: Dökümanlardaki metinleri okuyup işlenebilir hale getirme işlemi
BGE-small: Metinleri 384 boyutlu vektöre dönüştüren model

-LFRAG: Layout-oriented Fine-grained Retrieval-Augmented Generation https://arxiv.org/html/2605.22829v1 ---> OCR'nin parçalı pdflerdeki yetersizliğini anlatıyor. Yükarıda test etmek istediğim seneryolarda değindiğim gibi görselli ve tablolu dökümanlarda anlam eksikliğine yol açıyor. Bunun için LFRAG yönteminin çok daha başarılı olduğu gözlemlenmiş. LFRAG dökümanı bir bütün olarak değilde parçalanmış nloklar halinde grupluyor. Bu gruplama sayesinde dökümandaki bütünlük sağlanıyor. Küçük font ile yazılmış bilgilendirici paragraf ayrı bir konu olarak da algılanabiliyor.
![alt text](image.png) 
![alt text](image-1.png)

MAGE-RAG: Multigranular Adaptive Graph Evidence for Agentic Multimodal RAG in Long-Document QA https://arxiv.org/html/2606.15906v1 ---> Dökümani alt başlıklara ayırabilen bir ajan sistemi. Örneğin sayfalar, başlıklar, tablolar gibi alt başlıklar ile QA'yı hızlandııryor. En önemli noktaı bir K noktası vermiyor oluşu. Sabit bir k basit sorularda karmaşık cevaplar, karmaşık sorularda halisinasyon riskini arttırabilir.

VLM-RAG ---> Görseli anlamlandıran bir model. 

----
Bu noktada MARGE-RAG'da ki düğüm mantığı karmaşık sorular ve soru bağlamlarını çözme konusunda çok daha iyi fakat lokal modellerde devasa sorgular yapamayacağım için loopa girecektir. Bir diğer eksi noktası ise dökümandaki "resim2'de bahsettiğimiz gibi" şeklinde atıflar olduğunda bunu graf özelinde vermemiz gerekir fakat bizim dökümanımız anlık olarak değişebilir bizde bu grafı her defasında kurgulayamayız. 

OCR'nin tamamen eksik olduğunu düşünüyorum bu sebeple bu mimariyi diğerlerimne göre daha başarısız lkabul ettiğim içn denemeyeceğim. 

Bu aşamada LFRAG temelinde bir sistem geliştirmeyi düşünüyorum. Bu sisteme MARGE-RAG'da kullanılan graf ajan mantığını temel düzeyde entegre etmeye çalışacağım. Görselleri de VLM-RAG ile anlamlandırabileceğimi düşünmekteyim. 

---
Kodlamama öncelikle LFRAG ile konumlandırma yaptığı ve dökümanları bloklandırdacağı şekilde başlıyorum