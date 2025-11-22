# Qwen 4B Türkçe Chatbot - Kurulum Kılavuzu

## Sistem Gereksinimleri
- GPU: RTX 3060 (6GB VRAM) veya üstü
- RAM: 16GB minimum
- CUDA: 11.8+ (NVIDIA GPU için)
- Python: 3.10+

## Kurulum Adımları

### 1. Virtual Environment Oluştur
\`\`\`bash
python -m venv qwen_env
source qwen_env/bin/activate  # Linux/Mac
# VEYA
qwen_env\Scripts\activate  # Windows
\`\`\`

### 2. Dependencies Yükle
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 3. CUDA Desteğini Doğrula (GPU için)
\`\`\`bash
python -c "import torch; print(torch.cuda.is_available())"
# Çıktısı True olmalı
\`\`\`

### 4. Botu Çalıştır
\`\`\`bash
python chatbot.py
\`\`\`

## Özellikler
✅ 4-bit quantization (VRAM optimizasyon)
✅ Chat history (son 50 mesaj)
✅ Context-aware responses
✅ Türkçe full support
✅ Threading (UI responsive kalır)
✅ Error handling

## Gerekli API Anahtarları

### 1. OpenRouter API Key (Mistral Small 24B - Ücretsiz)

1. https://openrouter.ai/ adresine git
2. "Sign Up" ile hesap oluştur (GitHub ile giriş yapabilirsin)
3. Dashboard'a git
4. "API Keys" bölümünden yeni key oluştur
5. Key'i kopyala

**Not:** Mistral Small 24B modeli ücretsiz tier'da mevcut. Günlük limit cömert (10,000+ istek).

### 2. Gemini API Key (Fallback)

1. https://ai.google.dev/ adresine git
2. "Get API Key" butonuna tıkla
3. Google hesabınla giriş yap
4. "Create API Key" ile key oluştur
5. Key'i kopyala

**Not:** Günlük 1,500 istek ücretsiz.

## v0'da Environment Variables Ayarlama

v0'da environment variable eklemek için:
1. Sol sidebar'dan "Vars" sekmesine tıkla
2. "+ Add Variable" butonuna bas
3. Aşağıdaki variable'ları ekle:

\`\`\`
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxx
GEMINI_API_KEY=AIzaSyxxxxxxxxx
NEXT_PUBLIC_SITE_URL=http://localhost:3000
\`\`\`

4. Save'e bas

## Nasıl Çalışır?

- **Primary Provider:** Mistral Small 24B (24B parametre, ücretsiz)
- **Fallback Provider:** Gemini 2.0 Flash (rate limit aşımında veya hata durumunda)
- **Automatic Switching:** Günlük limit dolduğunda otomatik Gemini'ye geçer
- **Cost:** Ayda ~$18-25 (çoğu sorgu Mistral'dan ücretsiz)

## Maliyet Tahmini (500 Kullanıcı, 20 Sorgu/Gün)

- Hosting (Hetzner CX31): $8/ay
- Mistral (ücretsiz): $0/ay
- Gemini (fallback): $18-25/ay
- **Toplam: $26-33/ay**

## Hızlı İpuçları
- İlk başlatmada ~5-10 dakika model indirilecek
- Daha hızlı cevap için TEMPERATURE=0.5 azaltabilirsin
- Memory az kalırsa MAX_NEW_TOKENS=128 ye düşür
- Offline çalışır, internet gerekmez

## İleri Ayarlamalar (chatbot.py içinde)
- MODEL_ID: Farklı Qwen modeli kullanmak için
- TEMPERATURE: 0.3-0.9 arası (düşük=tutarlı, yüksek=creative)
- TOP_P: 0.7-0.95 arası (diversity kontrol)
- MAX_NEW_TOKENS: Response uzunluğu
