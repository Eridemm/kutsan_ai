"""
Qwen Chatbot Konfigürasyon Dosyası
"""

# Hugging Face Token (hardcoded)
HF_TOKEN = "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"

# Model Ayarları
MODEL_CONFIG = {
    "model_name": "X-D-Lab/MindChat-Qwen2-4B",
    "trust_remote_code": True,
    "device_map": "auto",
}

# Quantization Ayarları
QUANTIZATION_CONFIG = {
    "load_in_4bit": True,
    "bnb_4bit_use_double_quant": True,
    "bnb_4bit_quant_type": "nf4",
    "bnb_4bit_compute_dtype": "bfloat16",
}

# Generation Ayarları
GENERATION_CONFIG = {
    "max_new_tokens": 96,  # 128'den 96'ya - daha hızlı yanıt
    "temperature": 0.8,
    "top_p": 0.95,
    "do_sample": True,
    "repetition_penalty": 1.1,
    "num_beams": 1,
}

# Chat Ayarları
CHAT_CONFIG = {
    "max_history": 50,  # Son 50 mesajı tut
    "save_path": "chat_history.json",
}

# GUI Ayarları
GUI_CONFIG = {
    "window_width": 900,
    "window_height": 700,
    "font_size": 10,
    "theme": "default",
}

# Sistem Prompts
SYSTEM_PROMPTS = {
    "turkish_assistant": """Sen Türkçe konuşan yardımcı bir yapay zeka asistandın. 
SADECE TÜRKÇE yanıt ver. Başka dil kullanma.
Yanıtlarını tam olarak tamamla, yarıda kesme.
Cevaplarını net, kısa ve öz tut.
Bilinmediğini söylemekten korkmayın.""",
}
