import tkinter as tk
from tkinter import scrolledtext, messagebox
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from collections import deque
import threading

# ============================================
# Konfigürasyon
# ============================================
MODEL_ID = "Qwen/Qwen2-4B"  # Qwen 4B Model
MAX_HISTORY = 50  # Son 50 mesaj
MAX_NEW_TOKENS = 256
TEMPERATURE = 0.7
TOP_P = 0.9

# ============================================
# 4-bit Quantization Ayarları
# ============================================
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16
)

# ============================================
# Model ve Tokenizer Yükleme
# ============================================
print("Model yükleniyor, lütfen bekleyin...")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )
    model.eval()
    print("Model başarıyla yüklendi!")
except Exception as e:
    print(f"Model yükleme hatası: {e}")
    exit(1)

# ============================================
# Chat History Yönetimi
# ============================================
class ChatHistory:
    def __init__(self, max_size=MAX_HISTORY):
        self.history = deque(maxlen=max_size)
    
    def add_message(self, role, content):
        """Sohbete mesaj ekle"""
        self.history.append({"role": role, "content": content})
    
    def get_context(self):
        """Context string oluştur (model tarafından kullanılacak)"""
        context = ""
        for msg in self.history:
            if msg["role"] == "user":
                context += f"Kullanıcı: {msg['content']}\n"
            else:
                context += f"Asistan: {msg['content']}\n"
        return context
    
    def clear(self):
        """Geçmişi temizle"""
        self.history.clear()

chat_history = ChatHistory(max_size=MAX_HISTORY)

# ============================================
# Model Inference (Context ile)
# ============================================
def generate_response(user_input):
    """Qwen modeli ile context-aware cevap üret"""
    try:
        # Geçmiş + yeni soru
        context = chat_history.get_context()
        full_prompt = f"{context}Kullanıcı: {user_input}\nAsistan:"
        
        # Tokenize
        inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Decode ve temizle
        full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Önceki konteksti çıkar, sadece yeni cevabı al
        response = full_response.split("Asistan:")[-1].strip()
        
        return response
    
    except Exception as e:
        return f"Hata oluştu: {str(e)}"

# ============================================
# Tkinter GUI
# ============================================
class ChatbotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Qwen 4B Sohbet Botu - Türkçe")
        self.root.geometry("800x600")
        
        # Chat Display
        self.chat_display = scrolledtext.ScrolledText(
            root, height=20, width=95, state=tk.DISABLED, wrap=tk.WORD
        )
        self.chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Input Frame
        input_frame = tk.Frame(root)
        input_frame.pack(padx=10, pady=5, fill=tk.X)
        
        self.user_input = tk.Entry(input_frame, width=70)
        self.user_input.pack(side=tk.LEFT, padx=(0, 5))
        self.user_input.bind("<Return>", lambda e: self.send_message())
        
        self.send_button = tk.Button(input_frame, text="Gönder", command=self.send_message)
        self.send_button.pack(side=tk.LEFT, padx=2)
        
        self.clear_button = tk.Button(input_frame, text="Geçmişi Temizle", command=self.clear_history)
        self.clear_button.pack(side=tk.LEFT, padx=2)
        
        self.exit_button = tk.Button(input_frame, text="Çıkış", command=self.exit_app)
        self.exit_button.pack(side=tk.LEFT, padx=2)
        
        self.is_generating = False
    
    def send_message(self):
        """Mesaj gönder ve cevap al"""
        if self.is_generating:
            messagebox.showwarning("Bekleyin", "Model cevap üretiyor...")
            return
        
        user_text = self.user_input.get().strip()
        if not user_text:
            return
        
        thread = threading.Thread(target=self._process_message, args=(user_text,))
        thread.daemon = True
        thread.start()
    
    def _process_message(self, user_text):
        """Backend işleme (ayrı thread'de)"""
        self.is_generating = True
        self.send_button.config(state=tk.DISABLED)
        
        # UI güncelle
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"Siz: {user_text}\n", "user")
        self.chat_display.insert(tk.END, "Model cevap üretiyor...\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        # Chat history'ye ekle
        chat_history.add_message("user", user_text)
        
        # Model cevabı üret
        response = generate_response(user_text)
        
        # Chat history'ye cevabı ekle
        chat_history.add_message("assistant", response)
        
        # UI güncelle (son satırı sil, cevapla değiştir)
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("end-2l", tk.END)
        self.chat_display.insert(tk.END, f"Model: {response}\n\n", "assistant")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        self.user_input.delete(0, tk.END)
        self.send_button.config(state=tk.NORMAL)
        self.is_generating = False
    
    def clear_history(self):
        """Chat geçmişini temizle"""
        if messagebox.askyesno("Onayla", "Sohbet geçmişini temizlemek istediğinize emin misiniz?"):
            chat_history.clear()
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.insert(tk.END, "Sohbet geçmişi temizlendi.\n")
            self.chat_display.config(state=tk.DISABLED)
    
    def exit_app(self):
        """Uygulamayı kapat"""
        self.root.destroy()

# ============================================
# Ana Program
# ============================================
if __name__ == "__main__":
    root = tk.Tk()
    gui = ChatbotGUI(root)
    root.mainloop()
