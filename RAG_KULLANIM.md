# RAG (Retrieval-Augmented Generation) Kullanım Rehberi

## RAG Nedir?

RAG, modeli eğitmeden PDF'lerden bilgi ekleyerek chatbot'a özel bilgi kazandırma yöntemidir.

**Nasıl Çalışır?**
1. PDF'i yüklersin
2. PDF parçalara bölünür (chunking)
3. Her parça vektöre çevrilir (embedding)
4. Kullanıcı soru sorunca, ilgili parçalar bulunur
5. Bu parçalar modele context olarak verilir
6. Model bu bilgiyle yanıt üretir

---

## Kurulum

\`\`\`bash
pip install -r requirements.txt
\`\`\`

---

## Kullanım

### 1. Chatbot'u Başlat

\`\`\`bash
python qwen_chatbot_rag.py
\`\`\`

### 2. PDF Yükle

- GUI'de "PDF Yükle" butonuna tıkla
- Ders kitabı veya döküman seç (birden fazla PDF seçilebilir)
- İlk yükleme 2-5 dakika sürebilir (embedding oluşturma)

### 3. Soru Sor

PDF yüklendikten sonra içeriği hakkında soru sorabilirsin:

**Örnek:**
- "Bu kitapta yapay zeka hakkında ne yazıyor?"
- "Makine öğrenmesi algoritmaları nelerdir?"
- "Derin öğrenme nasıl çalışır?"

---

## Avantajlar

- Model eğitimi yok (hızlı)
- İstediğin zaman PDF ekle/çıkar
- Offline çalışır
- Kaynak gösterir (hangi PDF'ten geldiği)

---

## Dezavantajlar

- Her soru için PDF'i arar (biraz yavaş olabilir)
- PDF kötü taranmışsa OCR gerekir
- Çok büyük PDF'ler (1000+ sayfa) yavaşlatabilir

---

## Optimizasyon İpuçları

### Hız İçin:
- `top_k=2` (daha az parça getir)
- `chunk_size=300` (daha küçük parçalar)

### Kalite İçin:
- `top_k=5` (daha fazla context)
- `chunk_size=700` (daha büyük parçalar)

---

## Sorun Giderme

**PDF yüklenmiyor:**
- PDF şifreli mi? Şifreyi kaldır
- OCR gerekli mi? (Taranmış görüntü PDF ise)

**Yanlış bilgi veriyor:**
- top_k değerini artır (daha fazla context)
- chunk_overlap değerini artır (rag_manager.py)

**Çok yavaş:**
- top_k değerini azalt
- Daha küçük PDF'ler kullan
- embedding modelini değiştir (daha hızlı ama düşük kalite)

---

## İleri Seviye: LoRA Fine-tuning

Eğer model PDF bilgisini "öğrenmeli" diyorsan (RAG yerine), LoRA fine-tuning gerekir.

**Ne zaman kullan?**
- PDF'siz çalışması gerekiyorsa
- Her soru için PDF aramak istemiyorsan
- Model bilgiyi içselleştirmeli

**Dezavantajları:**
- Zaman alır (2-5 saat eğitim)
- GPU gerekli
- Yeni bilgi eklemek için tekrar eğitim

Eğer LoRA fine-tuning istersen, detaylı rehber yazabilirim.
