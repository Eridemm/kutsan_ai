# Qwen Türkçe Chatbot - Kurulum Rehberi

## Sistem Gereksinimleri

- **OS**: Windows 10+, Linux, macOS
- **RAM**: Minimum 16GB (önerilen 24GB+)
- **GPU**: NVIDIA CUDA Compute Capability 6.0+ (RTX 3060+)
  - VRAM: 6GB+ (4-bit quantization ile)
- **Python**: 3.9+
- **CUDA Toolkit**: 11.8+ (GPU kullanıyorsanız)

## Hızlı Kurulum (3 Adım)

### 1. Virtual Environment Oluştur ve Paketleri Yükle

\`\`\`bash
# Virtual environment oluştur
python -m venv qwen_env

# Aktifleştir
# Windows:
qwen_env\Scripts\activate
# Linux/macOS:
source qwen_env/bin/activate

# Requirements yükle
pip install -r requirements.txt

# PyTorch CUDA 11.8 ile yükle
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
\`\`\`

### 2. Token Ayarı (Zaten Hardcoded)

Token script'te hardcoded olarak gelir: `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`

Farklı token kullanmak istersen:
\`\`\`python
# qwen_chatbot.py satırı 225'te:
HF_TOKEN = "hf_YourTokenHere"
\`\`\`

### 3. Çalıştır

\`\`\`bash
python qwen_chatbot.py
\`\`\`

## İlk Çalıştırma

- Model ilk kez indirilecek (~8-12 GB)
- İnternet bağlantısı gerekli
- 10-20 dakika sürebilir
- Sonraki çalıştırmalar anlık açılacak

## CUDA Kurulumu (GPU Kullanıyorsanız)

### Windows:
1. CUDA Toolkit 11.8 indir: https://developer.nvidia.com/cuda-11-8-0-download-wizard
2. cuDNN indir: https://developer.nvidia.com/cudnn
3. cuDNN dosyalarını `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8` içine kopyala

### Linux (Ubuntu):
\`\`\`bash
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/3bf863cc.pub
sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
sudo apt-get update
sudo apt-get -y install cuda-11-8
\`\`\`

## Sorun Giderme

### Problem: "CUDA out of memory"
8-bit quantization kullan:
\`\`\`python
# qwen_chatbot.py satır 48-53'te:
bnb_config = BitsAndBytesConfig(
    load_in_8bit=True,  # 4bit yerine
    bnb_8bit_use_double_quant=True,
    bnb_8bit_quant_type="nf4",
    bnb_8bit_compute_dtype=torch.bfloat16
)
\`\`\`

### Problem: "Model not found"
- Token'ı kontrol et
- İnternet bağlantısını kontrol et
- Model var mı kontrol et: https://huggingface.co/X-D-Lab/MindChat-Qwen2-4B

### Problem: "CUDA not available"
GPU yüklemesi başarısız olursa CPU'da otomatik çalışır (yavaş olur):
\`\`\`bash
nvidia-smi  # GPU'nuzun tanındığını kontrol edin
\`\`\`

### Problem: Uzun yanıt süreleri
- Temperature değerini azalt (0.5-0.6)
- Top-P değerini azalt (0.7-0.8)
- `max_new_tokens` değerini küçült (qwen_chatbot.py satır 23, örn: 128)

## Performans İpuçları

1. **İlk çalıştırma**: Model cache'lenir, sonraki açılışlar anlık
2. **Temperature (0.7)**: Düşük = daha sabit, Yüksek = daha yaratıcı
3. **Top-P (0.9)**: Çeşitliliği kontrol eder (düşük = tekrarlı, yüksek = daha çeşitli)
4. **Chat History**: Son 50 mesaj tutulur, context-aware sohbet sağlanır

## GPU Kullanımını İzleme

\`\`\`bash
# Windows (PowerShell):
nvidia-smi -l 1

# Linux:
watch -n 1 nvidia-smi
\`\`\`

## Web'e Taşıma (Sonraki Aşama)

Daha sonra FastAPI kullanarak REST API'ye dönüştürülebilir:

\`\`\`python
from fastapi import FastAPI
app = FastAPI()
chatbot = QwenChatbot()

@app.post("/chat")
async def chat(message: str):
    response = chatbot.generate_response(message)
    return {"response": response}
\`\`\`

Sonrasında Docker ve Cloud Deploy (Vercel, Railway, Heroku) yapılabilir.

## Başladın mı?

1. `pip install -r requirements.txt`
2. `python qwen_chatbot.py`
3. Merhaba de!

Soruna yaşarsan direkt sor! 🚀
