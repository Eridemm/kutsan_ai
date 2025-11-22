"""
RAG (Retrieval-Augmented Generation) Manager
PDF'lerden bilgi çıkarır, vektör database'e kaydeder ve ilgili içeriği getirir
"""

import os
import pickle
from pathlib import Path
from typing import List, Dict
import numpy as np

try:
    import PyPDF2
    from sentence_transformers import SentenceTransformer
    import faiss
except ImportError:
    print("[WARNING] RAG kütüphaneleri eksik. Yüklemek için: pip install PyPDF2 sentence-transformers faiss-cpu")


class RAGManager:
    def __init__(self, embedding_model="emrecan/bert-base-turkish-cased-mean-nli-stsb-tr"):  # Türkçe embedding modeli
        """
        RAG Manager - PDF'lerden bilgi çıkarma ve arama
        
        Args:
            embedding_model: Türkçe destekli sentence transformer modeli
        """
        self.embedding_model_name = embedding_model
        self.embedder = None
        self.index = None
        self.chunks = []
        self.metadata = []
        self.vector_db_path = "vector_db"
        self.chunk_size = 400  # 500'den 400'e düştü (daha spesifik context)
        self.chunk_overlap = 80  # 100'den 80'e düştü
        self.progress_callback = None
        
        self.filter_keywords = [
            "etkinlik", "alıştırma", "soru", "cevap", "yanıt",
            "aktivite", "ödev", "uygulama", "değerlendirme",
            "boşluk doldur", "doğru yanlış", "eşleştir",
            "aşağıdaki soruları", "verilen metni", "metni okuyun"
        ]
        
        # Vector DB klasörü oluştur
        Path(self.vector_db_path).mkdir(exist_ok=True)
        
        print("[INFO] RAG Manager başlatılıyor...")
        self._load_embedding_model()
        
        self._check_and_reset_database()
    
    def _load_embedding_model(self):
        """Embedding modelini yükle"""
        try:
            print(f"[INFO] Embedding modeli yükleniyor: {self.embedding_model_name}")
            self.embedder = SentenceTransformer(self.embedding_model_name)
            print("[SUCCESS] Embedding modeli yüklendi!")
        except Exception as e:
            print(f"[ERROR] Embedding modeli yükleme hatası: {str(e)}")
            raise
    
    def load_pdf(self, pdf_path: str) -> List[str]:
        """
        PDF dosyasını yükle ve parçalara böl
        
        Args:
            pdf_path: PDF dosya yolu
            
        Returns:
            List[str]: Metin parçaları
        """
        try:
            if self.progress_callback:
                self.progress_callback(0, f"PDF açılıyor: {Path(pdf_path).name}")
            
            print(f"[INFO] PDF yükleniyor: {pdf_path}")
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                full_text = ""
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    full_text += text + "\n"
                    
                    if self.progress_callback:
                        progress = (page_num + 1) / total_pages * 30  # 0-30% for PDF reading
                        self.progress_callback(progress, f"Sayfa {page_num + 1}/{total_pages} okunuyor...")
                    
                print(f"[SUCCESS] {total_pages} sayfa okundu")
                
                if self.progress_callback:
                    self.progress_callback(30, "Metin parçalanıyor...")
                
                # Metni parçalara böl
                chunks = self._chunk_text(full_text, pdf_path)
                print(f"[SUCCESS] {len(chunks)} parça oluşturuldu")
                
                return chunks
                
        except Exception as e:
            print(f"[ERROR] PDF okuma hatası: {str(e)}")
            return []
    
    def _chunk_text(self, text: str, source: str) -> List[Dict]:
        """
        Metni akıllı şekilde parçalara böl
        - Başlıklara göre böl (1., 2., I., II., gibi)
        - Etkinlik/alıştırma parçalarını filtrele
        """
        chunks = []
        text = text.strip()
        
        sections = self._split_by_headings(text)
        
        for section in sections:
            if self._is_activity_section(section):
                print(f"[DEBUG] Etkinlik parçası filtrelendi: {section[:80]}...")
                continue
            
            # Parça çok büyükse cümlelere böl
            if len(section) <= self.chunk_size:
                chunks.append({
                    "text": section.strip(),
                    "source": source,
                    "chunk_id": len(chunks)
                })
            else:
                # Büyük bölümleri cümlelere böl
                sub_chunks = self._split_to_sentences(section)
                chunks.extend(sub_chunks)
        
        # Chunk ID'lerini güncelle
        for i, chunk in enumerate(chunks):
            chunk["chunk_id"] = i
            chunk["source"] = source
        
        return chunks
    
    def _split_by_headings(self, text: str) -> List[str]:
        """
        Metni başlıklara göre böl
        Örnek: "1. Malazgirt Savaşı", "2. Osmanlı Devleti"
        """
        import re
        
        # Başlık patternleri: "1.", "1.1", "I.", "A.", vb.
        heading_pattern = r'(?:^|\n)(?:\d+\.|[A-Z]\.|\d+\.\d+|[IVX]+\.)\s+[A-ZÇĞIÖŞÜ]'
        
        matches = list(re.finditer(heading_pattern, text))
        
        if not matches:
            # Başlık bulunamadıysa paragraf paragraf böl
            return text.split('\n\n')
        
        sections = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section = text[start:end].strip()
            if section:
                sections.append(section)
        
        return sections
    
    def _is_activity_section(self, text: str) -> bool:
        """
        Bir parçanın etkinlik/alıştırma olup olmadığını kontrol et
        """
        text_lower = text.lower()
        
        # Anahtar kelime kontrolü
        for keyword in self.filter_keywords:
            if keyword in text_lower:
                return True
        
        # Soru işareti yoğunluğu (çok fazla soru varsa etkinliktir)
        question_count = text.count('?')
        if question_count > 3:  # 3'ten fazla soru işareti varsa
            return True
        
        # Numaralı liste kontrolü (1) 2) 3) ... gibi)
        numbered_list_pattern = r'\d+\)\s'
        import re
        if len(re.findall(numbered_list_pattern, text)) > 3:
            return True
        
        return False
    
    def _split_to_sentences(self, text: str) -> List[Dict]:
        """
        Metni cümlelere böl (eski yöntem, büyük parçalar için)
        """
        chunks = []
        sentences = text.replace('\n', ' ').split('. ')
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append({
                        "text": current_chunk.strip(),
                        "source": "",  # Sonra doldurulacak
                        "chunk_id": len(chunks)
                    })
                    
                    overlap_text = current_chunk[-self.chunk_overlap:]
                    current_chunk = overlap_text + " " + sentence
                else:
                    current_chunk = sentence
            else:
                current_chunk += ". " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunks.append({
                "text": current_chunk.strip(),
                "source": "",
                "chunk_id": len(chunks)
            })
        
        return chunks
    
    def add_documents(self, pdf_paths: List[str]):
        """
        PDF'leri yükle ve vektör database'e ekle
        
        Args:
            pdf_paths: PDF dosya yolları listesi
        """
        all_chunks = []
        
        total_pdfs = len(pdf_paths)
        
        # Tüm PDF'leri yükle
        for idx, pdf_path in enumerate(pdf_paths, 1):
            if self.progress_callback:
                self.progress_callback(
                    30 * (idx - 1) / total_pdfs, 
                    f"PDF {idx}/{total_pdfs} işleniyor..."
                )
            
            chunks = self.load_pdf(pdf_path)
            all_chunks.extend(chunks)
        
        if not all_chunks:
            print("[WARNING] Hiç metin parçası bulunamadı!")
            return
        
        if self.progress_callback:
            self.progress_callback(40, f"Embedding'ler oluşturuluyor... ({len(all_chunks)} parça)")
        
        print(f"[INFO] Toplam {len(all_chunks)} parça işleniyor...")
        
        # Chunk'ları kaydet
        self.chunks = all_chunks
        
        # Embedding'leri oluştur
        texts = [chunk["text"] for chunk in all_chunks]
        print("[INFO] Embedding'ler oluşturuluyor... (Bu birkaç dakika sürebilir)")
        
        embeddings_list = []
        batch_size = 32
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.embedder.encode(
                batch,
                show_progress_bar=False,
                batch_size=batch_size
            )
            embeddings_list.append(batch_embeddings)
            
            if self.progress_callback:
                current_batch = (i // batch_size) + 1
                progress = 40 + (current_batch / total_batches * 50)  # 40-90%
                self.progress_callback(
                    progress, 
                    f"Embedding: {current_batch}/{total_batches} batch"
                )
        
        embeddings = np.vstack(embeddings_list)
        
        if self.progress_callback:
            self.progress_callback(90, "FAISS index oluşturuluyor...")
        
        # FAISS index oluştur
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))
        
        print(f"[SUCCESS] {len(all_chunks)} parça vektör database'e eklendi!")
        
        if self.progress_callback:
            self.progress_callback(95, "Database kaydediliyor...")
        
        # Database'i kaydet
        self.save_database()
        
        if self.progress_callback:
            self.progress_callback(100, "Tamamlandı!")
    
    def search(self, query: str, top_k: int = 4) -> List[Dict]:  # top_k 3'ten 4'e çıktı
        """
        Sorguya en yakın parçaları bul
        
        Args:
            query: Kullanıcı sorusu
            top_k: Kaç parça döndürülecek
            
        Returns:
            List[Dict]: En benzer parçalar
        """
        if self.index is None or not self.chunks:
            print("[WARNING] Vektör database boş!")
            return []
        
        # Sorgu embedding'i
        query_embedding = self.embedder.encode([query])
        
        # En yakın parçaları bul
        distances, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.chunks):
                result = self.chunks[idx].copy()
                result["similarity_score"] = float(1 / (1 + distance))  # Similarity score
                results.append(result)
        
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        print(f"[DEBUG] RAG arama sonuçları (top {top_k}):")
        for i, r in enumerate(results, 1):
            print(f"  [{i}] Skor: {r['similarity_score']:.3f} - {r['text'][:100]}...")
        
        return results
    
    def get_context_for_query(self, query: str, top_k: int = 4) -> str:  # top_k parametresi güncellendi
        """
        Sorguya göre context metni oluştur
        
        Args:
            query: Kullanıcı sorusu
            top_k: Kaç parça kullanılacak
            
        Returns:
            str: Format edilmiş context
        """
        results = self.search(query, top_k)
        
        if not results:
            return ""
        
        filtered_results = [r for r in results if r['similarity_score'] > 0.3]
        
        if not filtered_results:
            print("[WARNING] Yeterince benzer context bulunamadı (skor < 0.3)")
            return ""
        
        context_parts = []
        for i, result in enumerate(filtered_results, 1):
            context_parts.append(f"[BELGE {i}]:\n{result['text']}\n")
        
        context = "\n".join(context_parts)
        return context
    
    def save_database(self):
        """Vektör database'i diske kaydet"""
        try:
            # FAISS index
            faiss.write_index(self.index, os.path.join(self.vector_db_path, "index.faiss"))
            
            # Chunks
            with open(os.path.join(self.vector_db_path, "chunks.pkl"), 'wb') as f:
                pickle.dump(self.chunks, f)
            
            print(f"[SUCCESS] Database kaydedildi: {self.vector_db_path}")
        except Exception as e:
            print(f"[ERROR] Database kaydetme hatası: {str(e)}")
    
    def load_database(self):
        """Vektör database'i diskten yükle"""
        try:
            index_path = os.path.join(self.vector_db_path, "index.faiss")
            chunks_path = os.path.join(self.vector_db_path, "chunks.pkl")
            
            if not os.path.exists(index_path) or not os.path.exists(chunks_path):
                print("[INFO] Kaydedilmiş database bulunamadı")
                return False
            
            # FAISS index
            self.index = faiss.read_index(index_path)
            
            # Chunks
            with open(chunks_path, 'rb') as f:
                self.chunks = pickle.load(f)
            
            print(f"[SUCCESS] Database yüklendi: {len(self.chunks)} parça")
            return True
            
        except Exception as e:
            print(f"[ERROR] Database yükleme hatası: {str(e)}")
            return False
    
    def _check_and_reset_database(self):
        """
        Mevcut database'in embedding boyutunu kontrol et.
        Uyumsuzluk varsa database'i sil ve yeniden oluşturmaya zorla.
        """
        try:
            index_path = os.path.join(self.vector_db_path, "index.faiss")
            
            if os.path.exists(index_path):
                # Mevcut index'i yükle
                temp_index = faiss.read_index(index_path)
                
                # Test embedding boyutunu al
                test_embedding = self.embedder.encode(["test"])
                current_dimension = test_embedding.shape[1]
                
                # Index boyutunu kontrol et
                if temp_index.d != current_dimension:
                    print(f"[WARNING] Embedding boyutu uyuşmuyor! Index: {temp_index.d}, Model: {current_dimension}")
                    print(f"[INFO] Eski database siliniyor ve yeniden oluşturulacak...")
                    
                    # Eski dosyaları sil
                    if os.path.exists(index_path):
                        os.remove(index_path)
                    chunks_path = os.path.join(self.vector_db_path, "chunks.pkl")
                    if os.path.exists(chunks_path):
                        os.remove(chunks_path)
                    
                    print("[SUCCESS] Eski database temizlendi. Lütfen PDF'leri yeniden yükleyin.")
                    return False
                else:
                    print(f"[INFO] Database boyutu uyumlu ({current_dimension} boyut)")
                    return True
        except Exception as e:
            print(f"[WARNING] Database kontrol hatası: {str(e)}")
            return False
    
    def clear_database(self):
        """
        Tüm database'i temizle (PDF'leri kalıcı olarak sil)
        
        Returns:
            bool: Başarılı ise True
        """
        try:
            index_path = os.path.join(self.vector_db_path, "index.faiss")
            chunks_path = os.path.join(self.vector_db_path, "chunks.pkl")
            
            # Dosyaları sil
            if os.path.exists(index_path):
                os.remove(index_path)
                print("[INFO] FAISS index silindi")
            
            if os.path.exists(chunks_path):
                os.remove(chunks_path)
                print("[INFO] Chunks silindi")
            
            # Memory'den temizle
            self.index = None
            self.chunks = []
            self.metadata = []
            
            print("[SUCCESS] Database tamamen temizlendi!")
            return True
            
        except Exception as e:
            print(f"[ERROR] Database temizleme hatası: {str(e)}")
            return False
