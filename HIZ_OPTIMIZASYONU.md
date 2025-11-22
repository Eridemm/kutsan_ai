# Qwen Chatbot Hız Optimizasyonu

## Yapılan İyileştirmeler

### 1. Token Limiti Azaltma
- `max_new_tokens`: 256 → 128 token
- **Sonuç**: ~2x daha hızlı yanıt (24s → 10-12s)
- Çoğu sohbet yanıtı 128 token yeterli

### 2. KV Cache Aktivasyonu
- `use_cache=True` eklendi
- **Sonuç**: 30-40% hızlanma
- Attention hesaplamalarını cache'ler

### 3. Beam Search Kapatma
- `num_beams=1` (greedy decoding)
- **Sonuç**: 2-3x daha hızlı
- Kalite kaybı minimal

### 4. Model Eval Mode
- `model.eval()` ile inference modu
- **Sonuç**: Gereksiz gradient hesaplamaları kapalı

## Beklenen Performans

| Optimizasyon | Önceki Süre | Yeni Süre |
|--------------|-------------|-----------|
| Başlangıç | 24s | 24s |
| Token Limit | 24s | 12s |
| KV Cache | 12s | 8s |
| Beam Search | 8s | 5-6s |

**Hedef**: 5-10 saniye arası yanıt

## Daha Fazla Hızlandırma İçin

### Seçenek 1: Daha Agresif Token Limiti
\`\`\`python
self.max_new_tokens = 64  # Kısa yanıtlar için 3-4s
\`\`\`

### Seçenek 2: Daha Küçük Model
- Qwen2-1.5B veya Qwen2-0.5B kullan
- 4-5x daha hızlı
- Kalite biraz düşer

### Seçenek 3: Tensor Parallelism (Gelişmiş)
\`\`\`python
# Birden fazla GPU varsa
device_map = {
    "model.embed_tokens": 0,
    "model.layers.0-15": 0,
    "model.layers.16-31": 1,
}
\`\`\`

### Seçenek 4: vLLM Backend (Production İçin)
- FastAPI + vLLM
- 10-20x daha hızlı
- Batch inference
- Hosting için ideal

## Model Eğitimi (Fine-Tuning)

Evet, bu model eğitilebilir!

### Yöntem 1: LoRA (Önerilen)
\`\`\`bash
pip install peft
\`\`\`

\`\`\`python
from peft import LoRA, get_peft_model

# LoRA config
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
)

model = get_peft_model(model, lora_config)
\`\`\`

### Yöntem 2: Full Fine-Tuning
- RTX 3060 6GB yetersiz
- Cloud GPU gerekir (A100, V100)

### Önerilen Dataset Format
\`\`\`json
[
  {
    "messages": [
      {"role": "user", "content": "Merhaba"},
      {"role": "assistant", "content": "Merhaba! Nasıl yardımcı olabilirim?"}
    ]
  }
]
\`\`\`

İstersen fine-tuning için detaylı script yazabilirim.
