import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from PIL import Image

class MultimodalQdrantDB:
    def __init__(self, collection_name="tusas_doc_collection", db_path="./qdrant_data"):
        print("[SİSTEM] Çok Modlu (Multimodal) Veritabanı başlatılıyor...")
        # LLaVA yerine saniyeler içinde çalışan, Türkçeyi anlayan CLIP modelini yüklüyoruz
        self.model = SentenceTransformer('sentence-transformers/clip-ViT-B-32-multilingual-v1')
        
        # Qdrant'ı yerel klasörde kalıcı (persistent) olarak çalıştırıyoruz
        self.client = QdrantClient(path=db_path)
        self.collection_name = collection_name
        self.vector_size = 512 # CLIP ViT-B-32 modelinin vektör boyutu
        
        self._create_collection_if_not_exists()

    def _create_collection_if_not_exists(self):
        """Koleksiyon yoksa baştan oluşturur."""
        collections = self.client.get_collections().collections
        if not any(col.name == self.collection_name for col in collections):
            print(f"[QDRANT] Yeni koleksiyon oluşturuluyor: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size, 
                    distance=models.Distance.COSINE # Benzerlik ölçümü için Kosinüs Uzaklığı
                )
            )
        else:
            print(f"[QDRANT] Koleksiyon zaten mevcut: {self.collection_name}")

    def index_blocks(self, document_blocks):
        """Metin, Tablo ve Görselleri vektörlere dönüştürüp Qdrant'a kaydeder."""
        points = []
        
        for idx, block in enumerate(document_blocks):
            payload = {
                "id": block.get("id"),
                "page": block.get("page"),
                "type": block.get("type"),
                "content": block.get("content", ""),
                "image_path": block.get("image_path", "")
            }
            
            print(f"Gömülüyor (Embedding): Sayfa {block['page']} - Tip: {block['type']}...", end=" ")
            
            try:
                # 1. Eğer blok Metin veya Tablo ise, içeriğindeki yazıyı vektörle
                if block['type'] in ['text', 'table']:
                    vector = self.model.encode(block['content']).tolist()
                    
                # 2. Eğer blok Görsel ise, doğrudan resmi vektörle (Hiçbir metne çevirmeden!)
                elif block['type'] == 'image':
                    image_path = block['image_path']
                    if os.path.exists(image_path):
                        img = Image.open(image_path)
                        vector = self.model.encode(img).tolist()
                    else:
                        print("HATA: Resim bulunamadı, atlanıyor.")
                        continue
                
                # Vektörü Qdrant'a eklenecek noktalar (points) listesine koy
                points.append(
                    models.PointStruct(
                        id=idx, # Benzersiz tam sayı ID
                        vector=vector,
                        payload=payload
                    )
                )
                print("Başarılı.")
                
            except Exception as e:
                print(f"HATA: {e}")
                
        # Tüm vektörleri tek seferde veritabanına yaz
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            print(f"\n[BAŞARILI] {len(points)} adet veri Qdrant'a gömüldü!")

# Test Bloğu
if __name__ == "__main__":
    from parser import extract_lfrag_blocks  # Kendi yazdığımız parser'ı çağırıyoruz
    
    # 1. Faz: Verileri Çıkar
    test_pdf = "data/Case_Study_TUSAŞ_LLM.pdf" # Kendi PDF'inin adını yaz
    print("FAZ 1: PDF Ayrıştırılıyor...")
    blocks = extract_lfrag_blocks(test_pdf)
    
    # 2. Faz: Vektör Veritabanına Göm
    print("\nFAZ 2: Vektör Veritabanı (Qdrant) İşlemleri...")
    db = MultimodalQdrantDB()
    db.index_blocks(blocks)