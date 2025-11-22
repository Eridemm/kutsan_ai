"""
Lokal olarak kaydedilen Qwen modelini kullanarak
chat history'li, context-aware chatbot
"""

import tkinter as tk
from tkinter import scrolledtext, ttk
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from collections import deque
import threading

class QwenChatbot:
    def __init__(self, model_dir="./models/qwen2-4b"):
        self.model_dir = model_dir
        self.chat_history = deque(maxlen=50)  # Son 50 mesaj
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def load_model(self):
        """Lokal modeli yükle"""
        print(f"Model yükleniyor: {self.model_dir}")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_dir,
                trust_remote_code=True
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_dir,
                trust_remote_code=True,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            print("✓ Model başarıyla yüklendi")
            return True
        except Exception as e:
            print(f"❌ Model yükleme hatası: {e}")
            print(f"Önce download_model.py çalıştır")
            return False
    
    def generate_response(self, user_input):
        """Context'i göz önüne alarak cevap üret"""
        # Chat history'yi formatlı şekilde oluştur
        context = ""
        for msg_type, msg in self.chat_history:
            if msg_type == "user":
                context += f"Kullanıcı: {msg}\n"
            else:
                context += f"Asistan: {msg}\n"
        
        # Son kullanıcı mesajını ekle
        full_prompt = context + f"Kullanıcı: {user_input}\nAsistan:"
        
        # Tokenize et
        inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.device)
        
        # Üret
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.7,
                top_p=0.95,
                do_sample=True,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Prompt'u kaldırıp sadece cevabı al
        response = response.replace(full_prompt, "").strip()
        
        # Chat history'ye ekle
        self.chat_history.append(("user", user_input))
        self.chat_history.append(("bot", response))
        
        return response


class ChatbotUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Qwen Chatbot (Offline)")
        self.root.geometry("600x700")
        
        self.chatbot = QwenChatbot()
        
        # Model yükleme
        if not self.chatbot.load_model():
            tk.messagebox.showerror("Hata", "Model yüklenemedi. download_model.py çalıştır.")
            return
        
        # Chat kutusu
        self.chat_box = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, height=25, state=tk.DISABLED
        )
        self.chat_box.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Giriş kutusu
        input_frame = ttk.Frame(root)
        input_frame.pack(padx=10, pady=10, fill=tk.X)
        
        self.input_field = ttk.Entry(input_frame)
        self.input_field.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.input_field.bind("<Return>", lambda e: self.send_message())
        
        self.send_btn = ttk.Button(input_frame, text="Gönder", command=self.send_message)
        self.send_btn.pack(side=tk.LEFT)
    
    def send_message(self):
        user_input = self.input_field.get().strip()
        if not user_input:
            return
        
        # UI'ı güncelle
        self.update_chat("Kullanıcı", user_input, "user")
        self.input_field.delete(0, tk.END)
        self.send_btn.config(state=tk.DISABLED)
        
        # Thread'de cevap üret
        thread = threading.Thread(target=self.generate_and_display)
        thread.daemon = True
        thread.start()
    
    def generate_and_display(self):
        try:
            response = self.chatbot.generate_response(
                self.chat_box.get("end-2c", tk.END).split("Kullanıcı: ")[-1]
            )
            self.root.after(0, self.update_chat, "Asistan", response, "bot")
        finally:
            self.send_btn.config(state=tk.NORMAL)
    
    def update_chat(self, sender, message, msg_type):
        self.chat_box.config(state=tk.NORMAL)
        self.chat_box.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_box.see(tk.END)
        self.chat_box.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    ui = ChatbotUI(root)
    root.mainloop()
