from core.ingestion_pipeline import TusasIngestionPipeline

if __name__ == "__main__":
    # Ingestion boru hattını başlatıyoruz
    pipeline = TusasIngestionPipeline()
    
    # Analiz edilmesini istediğin PDF'in adı (PDF dosyan projenin ana klasöründe olmalı)
    pdf_dosya_adi = "data/Case_Study_TUSAŞ_LLM.pdf" 
    
    # Belgeyi İki Katmanlı (Macro + Micro) olarak işleyip Qdrant'a yüklüyoruz
    pipeline.ingest_document(pdf_dosya_adi)