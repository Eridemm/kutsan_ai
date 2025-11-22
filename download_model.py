"""
Qwen modelini lokal olarak indirmek ve offline kullanmak için
İlk kez çalıştırıldığında model indirilecek, sonra offline çalışacak
"""

import os
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Model konfigürasyonu
MODEL_ID = "Qwen/Qwen2-4B-Instruct"  # Qwen2-4B-Instruct dene
LOCAL_MODEL_DIR = "./models/qwen2-4b"  # Lokal kayıt yolu

def download_model():
    """Modeli indir ve lokal olarak kaydet"""
    print(f"Model indiriliyor: {MODEL_ID}")
    print(f"Kayıt yolu: {LOCAL_MODEL_DIR}")
    
    try:
        # Tokenizer indir
        print("Tokenizer indiriliyor...")
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_ID,
            trust_remote_code=True,
            cache_dir=LOCAL_MODEL_DIR
        )
        tokenizer.save_pretrained(LOCAL_MODEL_DIR)
        print("✓ Tokenizer kaydedildi")
        
        # Model indir (4-bit quantization ile)
        print("Model indiriliyor (bu biraz zaman alabilir)...")
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map="auto",
            cache_dir=LOCAL_MODEL_DIR,
            load_in_4bit=True,  # 4-bit quantization
            quantization_config={
                "load_in_4bit": True,
                "bnb_4bit_compute_dtype": torch.float16,
                "bnb_4bit_use_double_quant": True,
                "bnb_4bit_quant_type": "nf4"
            }
        )
        model.save_pretrained(LOCAL_MODEL_DIR)
        print("✓ Model kaydedildi")
        print(f"\nTamamlandı! Model şuraya kaydedildi: {LOCAL_MODEL_DIR}")
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        print("Çözüm önerileri:")
        print("1. Token yüklediysen kontrol et: hf_user login")
        print("2. Model ID'sini kontrol et (Qwen2-4B-Instruct)")
        print("3. İnternet bağlantısını kontrol et")

if __name__ == "__main__":
    download_model()
