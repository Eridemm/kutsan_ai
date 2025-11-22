# GitHub'a Yükleme ve Vercel Deployment Kılavuzu

## Adım 1: GitHub Hesabı ve Repository Oluşturma

### 1.1 GitHub Hesabı Açın (Yoksa)
1. https://github.com adresine gidin
2. "Sign Up" butonuna tıklayın
3. Email, şifre belirleyin ve hesabı oluşturun
4. Email doğrulaması yapın

### 1.2 Yeni Repository Oluşturun
1. GitHub'da oturum açın
2. Sağ üstteki "+" ikonuna tıklayın
3. "New repository" seçin
4. Repository ayarları:
   - **Repository name:** `ai-chatbot` (istediğiniz isim)
   - **Description:** "Gemini ve Mistral destekli AI chatbot"
   - **Public** veya **Private** seçin (Public öneririm)
   - ✅ **"Add a README file" işaretlemeyin**
   - ✅ **".gitignore" eklemeyin**
   - "Create repository" butonuna tıklayın

### 1.3 Repository URL'sini Kopyalayın
Repository oluştuktan sonra sayfada göreceğiniz URL'yi kopyalayın:
\`\`\`
https://github.com/KullaniciAdiniz/ai-chatbot.git
\`\`\`

---

## Adım 2: Projeyi GitHub'a Yükleme

### 2.1 Git Kurulumunu Kontrol Edin
Terminal/CMD açın ve şunu yazın:
\`\`\`bash
git --version
\`\`\`

Eğer "command not found" hatası alırsanız:
- Windows: https://git-scm.com/download/win indirip kurun
- Kurulum sonrası terminali kapatıp yeniden açın

### 2.2 Git Yapılandırması (İlk Kez)
\`\`\`bash
git config --global user.name "Adınız Soyadınız"
git config --global user.email "github@email.com"
\`\`\`

### 2.3 v0 Projesini İndirin
1. v0'da projenizin sağ üst köşesindeki **3 nokta menüsüne** tıklayın
2. **"Download ZIP"** seçin
3. ZIP dosyasını masaüstüne çıkarın

### 2.4 Terminal ile Proje Klasörüne Gidin
\`\`\`bash
cd Desktop/ai-chatbot
# veya ZIP'i nereye çıkardıysanız oraya
\`\`\`

### 2.5 Git Repository Oluşturun ve GitHub'a Yükleyin
\`\`\`bash
# Git repository başlat
git init

# Tüm dosyaları ekle
git add .

# İlk commit
git commit -m "İlk commit: AI chatbot projesi"

# GitHub repository'sine bağlan (URL'inizi buraya yapıştırın)
git remote add origin https://github.com/KullaniciAdiniz/ai-chatbot.git

# Main branch oluştur
git branch -M main

# GitHub'a yükle
git push -u origin main
\`\`\`

### 2.6 GitHub Token Gerekirse
Eğer şifre sorarsa (artık şifre kabul etmiyor):
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token" → "Generate new token (classic)"
3. Note: "Vercel deployment"
4. Expiration: 90 days
5. ✅ **"repo"** kutusunu işaretleyin
6. "Generate token" butonuna tıklayın
7. Token'ı kopyalayın (bir daha görmeyeceksiniz!)
8. Terminal'de şifre yerine bu token'ı yapıştırın

---

## Adım 3: Vercel'e Deployment

### 3.1 Vercel Hesabı Açın
1. https://vercel.com adresine gidin
2. **"Sign Up"** butonuna tıklayın
3. **"Continue with GitHub"** seçin
4. GitHub ile giriş yapın ve Vercel'e izin verin

### 3.2 Projeyi Import Edin
1. Vercel dashboard'una gidin
2. **"Add New..."** → **"Project"** tıklayın
3. GitHub repository'leriniz listelenecek
4. Az önce yüklediğiniz **"ai-chatbot"** repository'sini bulun
5. **"Import"** butonuna tıklayın

### 3.3 Proje Ayarları
**Framework Preset:** Next.js (otomatik algılanır)
**Root Directory:** `.` (değiştirmeyin)
**Build Command:** `npm run build` (otomatik)
**Output Directory:** `.next` (otomatik)

### 3.4 Environment Variables Ekleyin
**"Environment Variables"** bölümüne şunları ekleyin:

**1. GEMINI_API_KEY**
\`\`\`
Name: GEMINI_API_KEY
Value: AIzaSy... (Google AI Studio'dan aldığınız key)
\`\`\`

**2. OPENROUTER_API_KEY**
\`\`\`
Name: OPENROUTER_API_KEY
Value: sk-or-v1-... (OpenRouter'dan aldığınız key)
\`\`\`

**3. NEXT_PUBLIC_SITE_URL**
\`\`\`
Name: NEXT_PUBLIC_SITE_URL
Value: https://your-project.vercel.app
# (İlk deployment sonrası size verilecek URL'yi buraya yazacaksınız)
\`\`\`

**İlk deployment için NEXT_PUBLIC_SITE_URL boş bırakabilirsiniz, sonra güncelleriz.**

### 3.5 Deploy Edin
1. Tüm environment variables'ları ekledikten sonra
2. **"Deploy"** butonuna tıklayın
3. 2-3 dakika bekleyin (build işlemi)
4. ✅ Deployment başarılı olduğunda URL görünecek

### 3.6 NEXT_PUBLIC_SITE_URL'yi Güncelleyin
1. Vercel size bir URL verecek: `https://ai-chatbot-xyz123.vercel.app`
2. Vercel dashboard → Projeniz → **"Settings"** → **"Environment Variables"**
3. `NEXT_PUBLIC_SITE_URL` değerini bu yeni URL ile güncelleyin
4. **"Save"** butonuna tıklayın
5. **"Redeploy"** yapın (veya yeni commit atın)

---

## Adım 4: API Anahtarlarını Alın

### 4.1 Gemini API Key
1. https://ai.google.dev/ adresine gidin
2. **"Get API Key"** butonuna tıklayın
3. Google hesabı ile giriş yapın
4. **"Create API Key"** tıklayın
5. Key'i kopyalayın ve Vercel'de `GEMINI_API_KEY` olarak ekleyin

### 4.2 OpenRouter API Key (Mistral İçin - Ücretsiz)
1. https://openrouter.ai/ adresine gidin
2. Sağ üstten **"Sign In"** tıklayın
3. Google veya GitHub ile giriş yapın
4. Dashboard → **"API Keys"** → **"Create New Key"**
5. Key'i kopyalayın ve Vercel'de `OPENROUTER_API_KEY` olarak ekleyin

---

## Adım 5: Güncelleme Yapmak İsterseniz

### Kod değişikliği yaptığınızda:
\`\`\`bash
# Değişiklikleri ekle
git add .

# Commit oluştur
git commit -m "Güncelleme açıklaması"

# GitHub'a yükle
git push origin main
\`\`\`

Vercel otomatik olarak yeni commit'i algılayıp deploy edecektir.

---

## Sorun Giderme

### "git: command not found"
- Git yüklü değil. https://git-scm.com/downloads adresinden indirin

### "Permission denied (publickey)"
- GitHub token kullanın (yukarıda anlatıldı)

### Vercel Build Hatası
1. Vercel → Deployment → **"View Function Logs"**
2. Hatayı görün ve düzeltin
3. `git push` ile yeniden deploy edin

### Environment Variables Çalışmıyor
1. Vercel → Settings → Environment Variables
2. Değerleri kontrol edin
3. **"Redeploy"** yapın

---

## Başarılı Deployment Sonrası

Artık şu URL'den erişebilirsiniz:
\`\`\`
https://your-project.vercel.app
\`\`\`

- ✅ 500 kullanıcı destekler
- ✅ Mistral 24B ücretsiz (ilk 10k istek/gün)
- ✅ Gemini 2.0 Flash fallback
- ✅ Otomatik HTTPS
- ✅ Kredi kartı gerektirmez

Tebrikler! 🎉
