# 🚀 Akıllı Belge Analiz Sistemi (Multimodal RAG MVP)

Bu proje, kurumların karmaşık PDF'lerini ve doküman görsellerini anlayabilen, **%100 yerel (offline) çalışan**, halüsinasyon yapmayan ve veri gizliliğini merkeze alan bir **Multimodal RAG (Retrieval-Augmented Generation)** sistemidir. Standart sohbet botlarının aksine, gelişmiş indeksleme stratejileri ve katı LLM kısıtlamaları kullanarak yüksek doğrulukta bilgi çıkarımı yapar.


## 🎥 Proje Demo Videosu
Sistemin baştan sona nasıl çalıştığını, LFRAG ve OCR mimarisinin zorlu PDF'ler ve resimler üzerindeki performansını aşağıdaki videoya tıklayarak izleyebilirsiniz:

[![Akıllı Belge Analiz Sistemi Demo](https://img.youtube.com/vi/ko-SpwnbCjA/maxresdefault.jpg)](https://youtu.be/ko-SpwnbCjA)

> *Videoyu izlemek için yukarıdaki görsele veya [buraya](https://youtu.be/ko-SpwnbCjA) tıklayın.*


## ✨ Öne Çıkan Özellikler

### ❌ Klasik RAG Neden Çöker? (Körü Körüne Parçalama)
Geleneksel RAG sistemleri bir belgeyi alır ve sadece karakter sayısına (örn. her 1000 karakterde bir) göre acımasızca keser. Bu yöntem;
*   Paragrafın ortasını bıçak gibi ikiye böler, **anlam bütünlüğünü paramparça eder.**
*   Tabloları düz metin gibi okumaya çalışır, hücreler birbirine girer ve veriler çöp olur.
*   "Bu belgenin genel amacı nedir?" gibi global (büyük resmi soran) sorularda çuvallar çünkü sadece kopuk parçalara bakar.

### ✅ Bizim Çözümümüz: LFRAG (Layout-oriented Fine-grained RAG)
Biz metni sadece "okumuyoruz", belgenin **geometrisini ve tasarım dilini anlıyoruz.**
*   **Font ve Yapı Analizi:** Sistem (`fitz` üzerinden) pdf içerisindeki her bir harfin *font büyüklüğüne (size)* ve *kalınlığına (bold)* bakar. Bir metnin sıradan bir paragraf mı yoksa bir "Ana Başlık" mı olduğunu insan gibi görerek anlar ve metni karakter sayısına göre değil, **mantıksal bloklara ve başlıklara göre** granüler olarak ayırır.
*   **Kusursuz Tablo Farkındalığı:** PDF'lerdeki en büyük kabus olan tablolar için `pdfplumber` ile çapraz denetim yapar. Tabloların koordinatlarını (Bounding Box) tespit eder, içlerindeki veriyi izole eder ve veritabanına Markdown tablosu olarak pırıl pırıl kaydeder. Rakamlar asla birbirine karışmaz.

### 🌳 RAPTOR: Hiyerarşik Bilgi Ağacı 
LFRAG'ın çıkardığı akıllı bloklar, **RAPTOR** (Recursive Abstractive Processing for Tree-Organized Retrieval) mimarisiyle birleştirilir.
*   Bloklar bir araya getirilerek "Bölüm Özetleri" (Section Summaries) oluşturulur.
*   Bölüm özetleri sentezlenerek "Küresel Belge Vizyonu" (Root/Global Summary) çıkarılır.
*   Böylece sistem, spesifik bir teknik detayı sorarken en alt yaprağa (chunk) inerken, "Bu rapor ne anlatıyor?" dendiğinde en üst tepe noktasına (global vizyon) çıkar. 

### 👁️ EasyOCR ile Akıllı Geometri
Sistem, içerisindeki `EasyOCR` destekli görüntü işleme motoruyla karmaşık görselleri okur. 
Standart OCR motorları ekrandaki kelimeleri darmadağınık harf yığınları olarak verirken, bizim geliştirdiğimiz **Yatay ve Dikey Kutu Birleştirme (Heuristic Bounding Box Merging)** tolerans algoritmaları sayesinde görseldeki harfler nizami paragraflara ve cümlelere dikilir.


## 🛠️ Teknoloji Yığını (Tech Stack)

*   **Backend:** FastAPI, Python 3.10+
*   **LLM (Sentez):** Qwen2.5 (7B-Instruct) via Ollama
*   **Embedding Motoru:** BGE-M3 (BAAI) via SentenceTransformers
*   **Vektör Veritabanı:** Qdrant (Local disk-based)
*   **OCR & Doküman İşleme:** EasyOCR (Görseller), PyMuPDF & pdfplumber (PDF Tablo/Metin)
*   **Değerlendirme (QA):** LLM-as-a-Judge metoduyla izole edilmiş Ragas benzeri lokal test altyapısı.

---

## ⚙️ Kurulum ve Çalıştırma Adımları

Sistemi kendi bilgisayarınızda veya sunucunuzda ayağa kaldırmak için aşağıdaki adımları sırasıyla uygulayın.

### 1. Ön Koşullar
*   Bilgisayarınızda **Python 3.9 veya üzeri** bir sürüm kurulu olmalıdır.
*   Lokal dil modellerini çalıştırabilmek için bilgisayarınızda [Ollama](https://ollama.com/) kurulu olmalıdır.

### 2. Dil Modelinin İndirilmesi
Terminalinizi (veya Komut İstemini) açın ve sistemin kalbi olan Qwen2.5 modelini indirin:
```bash ollama pull qwen2.5:7b-instruct

### 3. Gerekli Kütüphanelerin Yüklenmesi
Proje dizininde bir terminal açın ve Python kütüphanelerini kurun.

Bash
pip install -r requirements.txt
pip install "numpy<2"

### 4. Sistemin Başlatılması
Tüm kurulumlar tamamlandıktan sonra, kök dizinde aşağıdaki komutu çalıştırarak FastAPI sunucusunu başlatın:

Bash
python app.py

### 5. Arayüze Erişim
Sunucu başarıyla ayağa kalktığında, tarayıcınızı açın ve şu adrese gidin:
👉 http://127.0.0.1:8000