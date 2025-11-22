import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import json
from datetime import datetime
from pathlib import Path
from collections import deque

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

class QwenChatbot:
    def __init__(self, model_name="X-D-Lab/MindChat-Qwen2-4B", hf_token=None):
        self.model_name = model_name
        self.hf_token = hf_token
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.chat_history = deque(maxlen=50)  # Son 50 mesajı tut
        self.is_loading = False
        self.max_new_tokens = 128  # 256'dan 128'e düşürüldü - 2x hızlı
        self.temperature = 0.8  # Daha çeşitli ama hızlı yanıtlar
        self.top_p = 0.95  # Daha geniş token seçimi
        self.repetition_penalty = 1.1  # Tekrar önleme
        
    def load_model(self):
        """Modeli float16 ile yükle (bitsandbytes CUDA hatası çözümü)"""
        try:
            print(f"[INFO] Cihaz: {self.device}")
            print(f"[INFO] Model yükleniyor: {self.model_name}")
            
            # Tokenizer yükle
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                token=self.hf_token,
                trust_remote_code=True
            )
            
            # 8-bit quantization RTX 3060 6GB için yeterli (~4-5GB VRAM kullanır)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                load_in_8bit=True,  # 8-bit quantization
                device_map="auto",  # Otomatik GPU memory yönetimi
                token=self.hf_token,
                trust_remote_code=True,
                attn_implementation="sdpa",  # scaled dot product attention (PyTorch 2.0+)
                use_cache=True,  # KV cache kullan - 30-40% hızlanma
                low_cpu_mem_usage=True  # RAM tasarrufu
            )
            
            self.model.eval()
            
            print("[SUCCESS] Model başarıyla yüklendi!")
            print(f"[INFO] VRAM kullanımı: ~4-5GB (8-bit quantization)")
            print(f"[INFO] KV cache: Aktif - Hızlı yanıtlar için optimize edildi")
            return True
            
        except Exception as e:
            print(f"[ERROR] Model yükleme hatası: {str(e)}")
            print("\n[INFO] Alternatif yükleme deneniyor (float16, quantization yok)...")
            
            try:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    device_map="auto",
                    token=self.hf_token,
                    trust_remote_code=True,
                    torch_dtype=torch.float16,
                    attn_implementation="sdpa",
                    use_cache=True,
                    low_cpu_mem_usage=True
                )
                self.model.eval()
                print("[SUCCESS] Model float16 ile yüklendi!")
                print("[WARNING] Quantization yok - VRAM kullanımı ~6-8GB")
                return True
            except Exception as e2:
                print(f"[ERROR] Float16 yükleme de başarısız: {str(e2)}")
                return False
    
    def add_to_history(self, role, content):
        """Chat geçmişine mesaj ekle"""
        self.chat_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_chat_context(self):
        """Chat geçmişinden format edilmiş context oluştur"""
        messages = []
        for msg in self.chat_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        return messages
    
    def generate_response(self, user_message):
        """Kullanıcı mesajına yanıt üret"""
        try:
            if self.model is None:
                return "[ERROR] Model henüz yüklenmedi!"
            
            # Geçmişe kullanıcı mesajını ekle
            self.add_to_history("user", user_message)
            
            # Context'i hazırla
            messages = self.get_chat_context()
            
            # Chat template uygula
            inputs = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_tensors="pt",
                return_dict=True
            ).to(self.model.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_new_tokens,  # 128 token - daha hızlı
                    temperature=self.temperature,
                    top_p=self.top_p,
                    do_sample=True,
                    repetition_penalty=self.repetition_penalty,  # Tekrar önleme
                    pad_token_id=self.tokenizer.eos_token_id,
                    use_cache=True,  # KV cache kullan
                    num_beams=1,  # Beam search yok - greedy daha hızlı
                )
            
            # Yanıtı decode et (sadece yeni token'ları al)
            response_text = self.tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[-1]:],
                skip_special_tokens=True
            ).strip()
            
            # Geçmişe bot yanıtını ekle
            self.add_to_history("assistant", response_text)
            
            return response_text
            
        except Exception as e:
            error_msg = f"[ERROR] Yanıt üretme hatası: {str(e)}"
            print(error_msg)
            return error_msg
    
    def save_chat(self, filepath="chat_history.json"):
        """Chat geçmişini dosyaya kaydet"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(list(self.chat_history), f, ensure_ascii=False, indent=2)
            print(f"[SUCCESS] Chat kaydedildi: {filepath}")
        except Exception as e:
            print(f"[ERROR] Chat kaydetme hatası: {str(e)}")


class ChatbotGUI:
    def __init__(self, root, hf_token):
        self.root = root
        self.root.title("Qwen Chatbot - Turkish")
        self.root.geometry("900x700")
        self.hf_token = hf_token
        
        # Chatbot instance
        self.chatbot = QwenChatbot(hf_token=hf_token)
        self.model_loaded = False
        
        # GUI Bileşenleri
        self.setup_ui()
        
        # Model yüklemesini başlat
        self.load_model_thread()
    
    def setup_ui(self):
        """GUI arayüzünü oluştur"""
        # Ana frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Başlık
        title_label = ttk.Label(
            main_frame, 
            text="Qwen 2 4B Türkçe Chatbot", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Durum etiketi
        self.status_label = ttk.Label(
            main_frame,
            text="⏳ Model yükleniyor...",
            font=("Arial", 10),
            foreground="orange"
        )
        self.status_label.pack()
        
        # Chat display alanı
        chat_frame = ttk.LabelFrame(main_frame, text="Sohbet", padding=10)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            height=20,
            width=80,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Arial", 10),
            bg="#f0f0f0"
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Mesaj giriş alanı
        input_frame = ttk.LabelFrame(main_frame, text="Mesaj Gönder", padding=10)
        input_frame.pack(fill=tk.X, pady=10)
        
        self.input_text = tk.Text(
            input_frame,
            height=3,
            width=70,
            font=("Arial", 10),
            wrap=tk.WORD
        )
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Gönder butonu
        self.send_button = ttk.Button(
            input_frame,
            text="GÖNDER\n(Ctrl+Enter)",
            command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT, fill=tk.BOTH)
        
        # Kontrol frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        # Ayarlar
        settings_frame = ttk.LabelFrame(control_frame, text="Ayarlar", padding=10)
        settings_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        ttk.Label(settings_frame, text="Temperature (0-2):").pack(side=tk.LEFT, padx=5)
        self.temp_scale = ttk.Scale(
            settings_frame,
            from_=0,
            to=2,
            orient=tk.HORIZONTAL,
            length=150
        )
        self.temp_scale.set(0.7)
        self.temp_scale.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(settings_frame, text="Top-P (0-1):").pack(side=tk.LEFT, padx=5)
        self.top_p_scale = ttk.Scale(
            settings_frame,
            from_=0,
            to=1,
            orient=tk.HORIZONTAL,
            length=150
        )
        self.top_p_scale.set(0.9)
        self.top_p_scale.pack(side=tk.LEFT, padx=5)
        
        # Butonlar
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.X)
        
        ttk.Button(button_frame, text="Temizle", command=self.clear_chat).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Kaydet", command=self.save_chat).pack(side=tk.LEFT, padx=5)
        
        # Keyboard binding
        self.root.bind("<Control-Return>", lambda e: self.send_message())
    
    def load_model_thread(self):
        """Modeli ayrı thread'de yükle"""
        def load():
            if self.chatbot.load_model():
                self.model_loaded = True
                self.status_label.config(
                    text="✓ Model hazır! Mesaj gönderebilirsiniz.",
                    foreground="green"
                )
                self.send_button.config(state=tk.NORMAL)
                self.input_text.config(state=tk.NORMAL)
            else:
                self.status_label.config(
                    text="✗ Model yükleme başarısız!",
                    foreground="red"
                )
                messagebox.showerror("Hata", "Model yükleme başarısız oldu!")
        
        self.send_button.config(state=tk.DISABLED)
        self.input_text.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=load, daemon=True)
        thread.start()
    
    def send_message(self, event=None):
        """Mesajı gönder ve yanıt al"""
        if not self.model_loaded:
            messagebox.showwarning("Uyarı", "Model henüz yüklenmedi!")
            return
        
        message = self.input_text.get("1.0", tk.END).strip()
        if not message:
            return
        
        # Temperature ve Top-P güncelle
        self.chatbot.temperature = float(self.temp_scale.get())
        self.chatbot.top_p = float(self.top_p_scale.get())
        
        # Chat ekranını güncelle
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"\n👤 Siz: {message}\n", "user")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        self.input_text.delete("1.0", tk.END)
        self.send_button.config(state=tk.DISABLED)
        
        # Yanıtı ayrı thread'de üret
        def generate():
            response = self.chatbot.generate_response(message)
            self.root.after(0, self.display_response, response)
            self.send_button.config(state=tk.NORMAL)
        
        thread = threading.Thread(target=generate, daemon=True)
        thread.start()
    
    def display_response(self, response):
        """Yanıtı ekranda göster"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"\n🤖 Bot: {response}\n", "assistant")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def clear_chat(self):
        """Sohbeti temizle"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.chatbot.chat_history.clear()
    
    def save_chat(self):
        """Sohbeti kaydet"""
        self.chatbot.save_chat()
        messagebox.showinfo("Başarılı", "Sohbet kaydedildi: chat_history.json")


if __name__ == "__main__":
    # TOKEN'İ BURAYA YAPISTIR (hardcoded)
    HF_TOKEN = "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"
    
    root = tk.Tk()
    gui = ChatbotGUI(root, HF_TOKEN)
    root.mainloop()
