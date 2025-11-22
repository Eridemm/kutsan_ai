# Vercel'e Deployment Kılavuzu

## Gereksinimler
- GitHub hesabı
- Gemini API key (https://ai.google.dev/)
- OpenRouter API key (https://openrouter.ai/)

## Adım 1: GitHub'a Yükle

1. GitHub'da yeni repository oluştur
2. Projeyi yükle:
\`\`\`bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/KULLANICI_ADINIZ/REPO_ADI.git
git push -u origin main
\`\`\`

## Adım 2: Vercel'e Deploy

1. **Vercel'e git:** https://vercel.com
2. **Sign Up with GitHub** butonuna tıkla
3. GitHub ile giriş yap (kredi kartı gerekmez)
4. **Add New Project** butonuna tıkla
5. Repository'ni seç (import et)
6. **Environment Variables** bölümünde şunları ekle:

### Gerekli Environment Variables:

**GEMINI_API_KEY**
- Value: https://ai.google.dev/ adresinden aldığın API key
- Örnek: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXX`

**OPENROUTER_API_KEY**
- Value: https://openrouter.ai/ adresinden aldığın API key
- Örnek: `sk-or-v1-XXXXXXXXXXXXXXXXXXXXXXXX`

**NEXT_PUBLIC_SITE_URL**
- Value: Vercel otomatik URL verecek, şimdilik boş bırak
- Deploy sonrası güncelleyeceksin

7. **Deploy** butonuna tıkla
8. 2-3 dakika bekle

## Adım 3: Site URL'sini Güncelle

1. Deploy tamamlandıktan sonra Vercel sana bir URL verecek
   - Örnek: `https://ai-chatbot-xyz123.vercel.app`

2. **Settings** → **Environment Variables** → **NEXT_PUBLIC_SITE_URL** değerini güncelle:
   - Value: `https://ai-chatbot-xyz123.vercel.app`

3. **Redeploy** et (Deployments sekmesinden son deployment'ın yanındaki 3 noktaya tıkla → Redeploy)

## API Key Nasıl Alınır?

### Gemini API Key (Ücretsiz)

1. https://ai.google.dev/ adresine git
2. **Get API Key** butonuna tıkla
3. **Create API Key** seç
4. Yeni API key oluştur
5. Key'i kopyala
6. Vercel'de GEMINI_API_KEY olarak ekle

**Limit:** Günlük 1,500 istek ücretsiz

### OpenRouter API Key (Ücretsiz)

1. https://openrouter.ai/ adresine git
2. **Sign Up** ile kayıt ol
3. Dashboard → **Keys** sekmesine git
4. **Create Key** butonuna tıkla
5. Key'i kopyala
6. Vercel'de OPENROUTER_API_KEY olarak ekle

**Limit:** Günlük 10,000 istek ücretsiz (Mistral Small 24B için)

## Sistem Nasıl Çalışır?

\`\`\`
Kullanıcı → Vercel (Frontend + API Routes)
              ↓
        Önce OpenRouter (Mistral Small 24B - Ücretsiz)
        Limit dolunca → Gemini 2.0 Flash (Fallback)
\`\`\`

**Günlük 10,000 sorgu → Tamamen ücretsiz**
**10,000+ sorgu → Gemini devreye girer**

## Maliyet Tahmini (500 Kullanıcı, 20 Sorgu/Gün)

- **İlk 10,000 sorgu/gün:** $0 (Mistral ücretsiz)
- **10,000+ sorgu:** ~$2/gün (Gemini)

**Aylık bütçe:** $0-60

## PDF Yükleme Nasıl Çalışır?

Sistem PDF'leri Gemini API kullanarak işler:
1. PDF dosyasını yüklersiniz
2. Gemini API PDF'den tüm metni çıkarır (OCR)
3. Çıkarılan metin bellekte context olarak saklanır
4. Her soruda bu context modele gönderilir
5. Model PDF'deki bilgilere göre cevap verir

**Önemli Notlar:**
- PDF'ler Vercel sunucusunda kalıcı olarak saklanmaz
- Sadece oturumunuz boyunca bellekte tutulur
- Sayfa yenilendiğinde PDF tekrar yüklenmelidir
- Maksimum PDF boyutu: ~10MB (Gemini API limiti)

## Fine-Tuning Yetenekleri

Bu chatbot PDF yükleyerek "eğitilebilir":
- Ders kitapları yükleyerek o konularda uzmanlaşır
- Notlar, dökümanlar yüklenebilir
- Model yüklenen belgelerdeki bilgilere göre cevap verir
- Her oturumda farklı PDF'ler yüklenebilir

**Not:** Bu gerçek fine-tuning değil, RAG (Retrieval-Augmented Generation) sistemidir. Model kendisi değişmez, sadece yüklenen belgelerden bilgi kullanır.

## Güncelleme (Git Push ile Otomatik Deploy)

\`\`\`bash
git add .
git commit -m "Updated feature"
git push
\`\`\`

Vercel otomatik olarak yeni versiyonu deploy eder (30-60 saniye).

## Sorun Giderme

**"API key geçersiz" hatası:**
- Environment variables'ı kontrol et
- API key'leri yeniden oluştur
- Redeploy et

**"Rate limit exceeded" hatası:**
- Günlük limit dolmuş
- Gemini fallback devreye girmelidir
- Eğer her iki API de limitli ise, ertesi gün saat 00:00'da reset olur

**"Site yavaş" şikayeti:**
- Vercel ücretsiz plan cold start'a sahiptir (ilk istek 2-3sn)
- Aktif kullanımda hız normaldir

## Avantajlar

✅ Kredi kartı gerekmez
✅ Sınırsız deployment
✅ Otomatik SSL (HTTPS)
✅ Global CDN
✅ 100 GB bandwidth/ay
✅ Git push ile otomatik deploy
✅ 500 kullanıcı için yeterli

## Vercel Dashboard

- **Deployments:** Tüm deployment geçmişi
- **Analytics:** Ziyaretçi istatistikleri
- **Logs:** Hata logları ve debug
- **Settings:** Domain, environment variables, vb.
