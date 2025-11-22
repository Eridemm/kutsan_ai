# Web Chatbot Deployment Rehberi

## 1. Gemini API Key Alma (2 dakika)

1. https://ai.google.dev/ adresine git
2. "Get API Key" butonuna tıkla
3. Google hesabınla giriş yap
4. API key'i kopyala

## 2. Local Çalıştırma

\`\`\`bash
# Bağımlılıkları yükle
npm install

# .env.local dosyası oluştur
cp .env.local.example .env.local

# .env.local dosyasına Gemini API key ekle
GEMINI_API_KEY=your_actual_key_here

# Geliştirme sunucusunu başlat
npm run dev
\`\`\`

Tarayıcıda http://localhost:3000 aç

## 3. Vercel'e Deploy (5 dakika)

1. GitHub'a push et
2. https://vercel.com adresine git
3. "Import Project" ile repo'yu seç
4. Environment Variables bölümünde ekle:
   - Key: `GEMINI_API_KEY`
   - Value: `your_gemini_api_key`
5. "Deploy" butonuna tıkla

## 4. Backend (PDF RAG) için FastAPI (Opsiyonel)

Gerçek PDF işleme için Python backend gerekiyor:

\`\`\`bash
# Railway.app veya Render.com'a deploy et
# Backend repo'su ayrı oluşturulmalı (gerekirse yapabilirim)
\`\`\`

## Özellikler

- Gemini 1.5 Flash API (ücretsiz tier)
- Chat history (son 50 mesaj)
- PDF yükleme (UI hazır, backend TODO)
- Gerçek zamanlı düşünme sayacı
- Responsive tasarım
- Dark mode desteği

## Sınırlamalar

- Günlük 1500 istek (Gemini ücretsiz limit)
- PDF işleme henüz aktif değil (FastAPI backend gerekli)

## Sonraki Adımlar

1. FastAPI backend ekle (Python RAG sistemi)
2. PDF parsing ekle (pdf-parse veya PyPDF2)
3. Vector database entegrasyonu
4. Kullanıcı authentication (opsiyonel)
