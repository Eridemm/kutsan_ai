import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, filedialog
import threading
import json
import re
import time  # time modülü eklendi
from datetime import datetime
from pathlib import Path
from collections import deque

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from rag_manager import RAGManager
from config import HF_TOKEN, GENERATION_CONFIG, SYSTEM_PROMPTS


class QwenChatbot:
    def __init__(self, model_name="X-D-Lab/MindChat-Qwen2-4B", hf_token=None, use_rag=True):
        self.model_name = model_name
        self.hf_token = hf_token or HF_TOKEN
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.chat_history = deque(maxlen=50)
        self.is_loading = False
        self.max_new_tokens = GENERATION_CONFIG["max_new_tokens"]
        self.temperature = GENERATION_CONFIG["temperature"]
        self.top_p = GENERATION_CONFIG["top_p"]
        self.repetition_penalty = GENERATION_CONFIG["repetition_penalty"]
        
        self.use_rag = use_rag
        self.rag_manager = None
        if use_rag:
            try:
                self.rag_manager = RAGManager()
                if self.rag_manager.load_database():
                    print(f"[SUCCESS] Kaydedilmiş database yüklendi: {len(self.rag_manager.chunks)} parça hazır!")
                else:
                    print("[INFO] Yeni database oluşturulacak. PDF yükleyebilirsiniz.")
            except Exception as e:
                print(f"[WARNING] RAG başlatma hatası: {str(e)}")
                self.use_rag = False
        
    def load_model(self):
        """Modeli float16 ile yükle"""
        try:
            print(f"[INFO] Cihaz: {self.device}")
            print(f"[INFO] Model yükleniyor: {self.model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                token=self.hf_token,
                trust_remote_code=True
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                token=self.hf_token,
                trust_remote_code=True,
                attn_implementation="sdpa",
                use_cache=True,
                low_cpu_mem_usage=True
            )
            
            self.model.eval()
            
            print("[SUCCESS] Model başarıyla yüklendi!")
            print(f"[INFO] Model boyutu: ~{sum(p.numel() for p in self.model.parameters()) / 1e9:.2f}B parametreler")
            return True
            
        except Exception as e:
            print(f"[ERROR] Model yükleme hatası: {str(e)}")
            return False
    
    def load_pdfs(self, pdf_paths, progress_callback=None):
        """PDF'leri RAG sistemine yükle"""
        if not self.use_rag or not self.rag_manager:
            print("[ERROR] RAG sistemi aktif değil!")
            return False
        
        try:
            self.rag_manager.progress_callback = progress_callback
            self.rag_manager.add_documents(pdf_paths)
            return True
        except Exception as e:
            print(f"[ERROR] PDF yükleme hatası: {str(e)}")
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
    
    def clean_response(self, text):
        """
        Yanıtı temizle: Çince/Korece/Japonca karakterleri kaldır, Türkçe olmayan içerikleri filtrele
        """
        import re
        
        # Çince: \u4e00-\u9fff
        # Korece: \uac00-\ud7af, \u1100-\u11ff, \u3130-\u318f
        # Japonca: \u3040-\u309f, \u30a0-\u30ff
        text = re.sub(r'[\u4e00-\u9fff\uac00-\ud7af\u1100-\u11ff\u3130-\u318f\u3040-\u309f\u30a0-\u30ff]+', '', text)
        
        text = re.sub(r'\s+', ' ', text)
        
        # Yarım kalan cümleleri temizle (noktalama işaretine kadar kes)
        sentences = text.split('.')
        clean_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Çok kısa parçaları atla
                clean_sentences.append(sentence)
        
        if clean_sentences:
            result = '. '.join(clean_sentences) + '.'
        else:
            result = text.strip()
        
        return result
    
    def generate_response(self, user_message):
        """Kullanıcı mesajına yanıt üret (RAG destekli)"""
        try:
            if self.model is None:
                return "[ERROR] Model henüz yüklenmedi!"
            
            rag_context = ""
            avg_similarity = 0.0
            
            if self.use_rag and self.rag_manager and self.rag_manager.index is not None:
                rag_context = self.rag_manager.get_context_for_query(user_message, top_k=4)
                
                if rag_context:
                    print("[INFO] RAG context bulundu, ekleniyor...")
                    # Ortalama benzerlik skorunu hesapla
                    results = self.rag_manager.search(user_message, top_k=4)
                    if results:
                        avg_similarity = sum(r['similarity_score'] for r in results) / len(results)
                        print(f"[DEBUG] Ortalama benzerlik skoru: {avg_similarity:.3f}")
            
            if rag_context:
                enhanced_message = f"""Sen Türkçe tarih konularında uzman bir yapay zeka asistanısın. Sana bir TARİH KİTABI belgesi verildi.

KATÎ KURALLAR:
1. SADECE TÜRKÇE cevap ver - Hiçbir Çince (中文), İngilizce, Korece, Japonca karakteri KULLANMA
2. Aşağıdaki BELGE bilgilerine AYNEN dayanarak cevap ver
3. Belgede bilgi YOKSA: "Bu bilgi belgede mevcut değil" de, kesinlikle bilgi UYDURMA
4. Etkinlik/alıştırma soruları OLMASIN - sadece bilgi odaklı cevap
5. Cevabını EKSIKSIZ bitir, yarıda kesme
6. Kısa ve net cevap ver (2-4 cümle yeterli)

TARİH BELGESİ:
{rag_context}

Kullanıcı Sorusu: {user_message}

TÜRKÇE CevAP (SADECE BELGEDEN):"""
            else:
                enhanced_message = f"""Sen Türkçe tarih konularında uzman bir yapay zeka asistanısın.

KURALLAR:
1. SADECE TÜRKÇE cevap ver
2. Eğer belgede bu konu yoksa: "Bu konu hakkında yüklenen belgede bilgi bulamadım" de
3. Bilgi uydurma, sadece genel tarih bilgilerini kullan

Kullanıcı: {user_message}

TÜRKÇE CevAP:"""
            
            # Geçmişe ekle
            self.add_to_history("user", user_message)
            
            # Context hazırla (son 6 mesaj)
            messages = list(self.chat_history)[-6:]
            # Son mesajı RAG-enhanced ile değiştir
            messages[-1]["content"] = enhanced_message
            
            # Chat template
            inputs = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_tensors="pt",
                return_dict=True
            ).to(self.model.device)
            
            eos_token_ids = [self.tokenizer.eos_token_id]
            if hasattr(self.tokenizer, 'convert_tokens_to_ids'):
                newline_id = self.tokenizer.convert_tokens_to_ids("\n")
                if newline_id is not None:
                    eos_token_ids.append(newline_id)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=150,  # 180'den 150'ye (daha kısa, net cevaplar)
                    temperature=0.5,  # 0.6'dan 0.5'e (daha deterministik)
                    top_p=0.8,  # 0.85'ten 0.8'e (daha güvenli seçimler)
                    do_sample=True,
                    repetition_penalty=1.2,  # 1.15'ten 1.2'ye (tekrar azaltma)
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=eos_token_ids,
                    use_cache=True
                )
            
            # Yanıtı decode et
            response = self.tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[-1]:],
                skip_special_tokens=True
            )
            
            response = self.clean_response(response)
            
            if len(response) < 20:
                response = "Üzgünüm, bu soruya yeterli bir cevap üretemiyorum. Lütfen soruyu farklı şekilde sorar mısınız?"
            
            # Geçmişe ekle
            self.add_to_history("assistant", response)
            
            return response
            
        except Exception as e:
            print(f"[ERROR] Yanıt üretme hatası: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"[ERROR] Yanıt üretilirken hata: {str(e)}"


class ChatbotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Qwen Türkçe Chatbot (RAG Destekli)")
        self.root.geometry("900x700")
        
        self.chatbot = QwenChatbot(use_rag=True)
        self.is_model_loaded = False
        self.thinking_start_time = None
        self.thinking_label = None
        self.timer_id = None
        
        self.setup_ui()
        
        if self.chatbot.rag_manager and self.chatbot.rag_manager.index is not None:
            chunk_count = len(self.chatbot.rag_manager.chunks)
            self.display_message(
                "Sistem", 
                f"Kaydedilmiş database yüklendi: {chunk_count} parça hazır!\n"
                f"PDF'ler kalıcı olarak kaydedildi, yeniden yüklemenize gerek yok."
            )
        elif self.chatbot.rag_manager:
            self.display_message(
                "Sistem",
                "Database boş veya yenilendi. Lütfen 'PDF Yükle' butonu ile PDF'lerinizi yükleyin.\n"
                "PDF'ler bir kez yüklendikten sonra kalıcı olarak kaydedilir.",
                "system"
            )
        
        # Model yüklemeyi başlat
        threading.Thread(target=self.load_model_async, daemon=True).start()

    def setup_ui(self):
        # Ana frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            width=80,
            height=30,
            font=("Arial", 10),
            state=tk.DISABLED
        )
        self.chat_display.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Tags for styling
        self.chat_display.tag_config("user", foreground="blue", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("bot", foreground="green", font=("Arial", 10))
        self.chat_display.tag_config("system", foreground="gray", font=("Arial", 9, "italic"))
        self.chat_display.tag_config("thinking", foreground="orange", font=("Arial", 9, "italic"))
        self.chat_display.tag_config("time_info", foreground="purple", font=("Arial", 9, "italic"))
        
        # Input frame
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        # User input
        self.user_input = tk.Text(input_frame, height=3, width=70, font=("Arial", 10))
        self.user_input.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.user_input.bind("<Return>", lambda e: self.send_message() if not e.state & 0x1 else None)
        
        # Buttons frame
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=0, column=1)
        
        # Send button
        self.send_button = ttk.Button(button_frame, text="Gönder", command=self.send_message)
        self.send_button.grid(row=0, column=0, pady=(0, 5))
        
        # PDF yükleme butonu
        self.pdf_button = ttk.Button(button_frame, text="PDF Yükle", command=self.load_pdf)
        self.pdf_button.grid(row=1, column=0, pady=(0, 5))
        
        self.delete_pdf_button = ttk.Button(button_frame, text="PDF Sil", command=self.delete_pdfs)
        self.delete_pdf_button.grid(row=2, column=0)
        
        # Status bar
        self.status_label = ttk.Label(main_frame, text="Model yükleniyor...", foreground="orange")
        self.status_label.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # Progress bar (PDF yükleme için)
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate', length=400)
        self.progress_bar.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        self.progress_bar.grid_remove()  # Başlangıçta gizle
        
        # Grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

    def display_message(self, sender, message, tag="bot"):
        """Chat ekranına mesaj ekle"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{sender}: ", tag)
        self.chat_display.insert(tk.END, f"{message}\n\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def update_progress(self, progress, message):
        """Progress bar güncelle"""
        self.progress_bar['value'] = progress
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def load_model_async(self):
        """Modeli arka planda yükle"""
        self.display_message("Sistem", "Model yükleniyor, lütfen bekleyin...", "system")
        success = self.chatbot.load_model()
        
        if success:
            self.is_model_loaded = True
            self.status_label.config(text="Model hazır!", foreground="green")
            self.display_message("Sistem", "Model yüklendi! Sorularınızı sorabilirsiniz.", "system")
        else:
            self.status_label.config(text="Model yükleme başarısız!", foreground="red")
            self.display_message("Sistem", "Model yüklenemedi. Lütfen hata mesajlarını kontrol edin.", "system")
    
    def load_pdf(self):
        """PDF dosyalarını yükle"""
        if not self.chatbot.use_rag:
            messagebox.showerror("Hata", "RAG sistemi aktif değil!")
            return
        
        file_paths = filedialog.askopenfilenames(
            title="PDF Dosyalarını Seçin",
            filetypes=[("PDF files", "*.pdf")]
        )
        
        if not file_paths:
            return
        
        # Progress bar göster
        self.progress_bar.grid()
        self.progress_bar['value'] = 0
        
        def load_thread():
            try:
                success = self.chatbot.load_pdfs(list(file_paths), progress_callback=self.update_progress)
                
                if success:
                    self.display_message(
                        "Sistem", 
                        f"{len(file_paths)} PDF başarıyla yüklendi ve kaydedildi!\n"
                        f"Bu PDF'ler artık kalıcı olarak kaydedildi, tekrar yüklemenize gerek yok.",
                        "system"
                    )
                    self.status_label.config(text="PDF'ler yüklendi ve kaydedildi!", foreground="green")
                else:
                    self.display_message("Sistem", "PDF yükleme başarısız!", "system")
                    self.status_label.config(text="PDF yükleme başarısız", foreground="red")
            except Exception as e:
                self.display_message("Sistem", f"Hata: {str(e)}", "system")
            finally:
                self.progress_bar.grid_remove()
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def update_thinking_timer(self):
        """Düşünme süresini saniye saniye güncelle"""
        if self.thinking_start_time:
            elapsed = int(time.time() - self.thinking_start_time)
            
            # Chat ekranındaki zamanlayıcıyı güncelle
            self.chat_display.config(state=tk.NORMAL)
            # Son satırı bul ve güncelle
            try:
                last_line_start = self.chat_display.index("end-2l linestart")
                last_line_end = self.chat_display.index("end-2l lineend")
                current_text = self.chat_display.get(last_line_start, last_line_end)
                
                # Eğer "Düşünüyor" mesajıysa güncelle
                if "Düşünüyor" in current_text:
                    self.chat_display.delete(last_line_start, last_line_end)
                    self.chat_display.insert(last_line_start, f"Bot: Düşünüyor... ({elapsed} saniye)", "thinking")
                    self.chat_display.see(tk.END)
            except:
                pass
            
            self.chat_display.config(state=tk.DISABLED)
            
            if self.thinking_start_time:
                self.timer_id = self.root.after(1000, self.update_thinking_timer)
    
    def send_message(self):
        """Kullanıcı mesajını gönder"""
        if not self.is_model_loaded:
            messagebox.showwarning("Uyarı", "Model henüz yüklenmedi!")
            return
        
        user_message = self.user_input.get("1.0", tk.END).strip()
        if not user_message:
            return
        
        # Kullanıcı mesajını göster
        self.display_message("Siz", user_message, "user")
        self.user_input.delete("1.0", tk.END)
        
        self.thinking_start_time = time.time()
        self.display_message("Bot", "Düşünüyor... (0 saniye)", "thinking")
        self.update_thinking_timer()
        
        # Arka planda yanıt üret
        def generate_thread():
            response = self.chatbot.generate_response(user_message)
            
            elapsed_time = time.time() - self.thinking_start_time
            
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
                self.timer_id = None
            
            self.thinking_start_time = None
            
            self.chat_display.config(state=tk.NORMAL)
            # Son 2 satırı sil (Bot: Düşünüyor...\n\n)
            self.chat_display.delete("end-3l", "end-1l")
            self.chat_display.config(state=tk.DISABLED)
            
            self.display_message("Bot", f"{response}\n[{elapsed_time:.1f} saniye düşünüldü]", "bot")
        
        threading.Thread(target=generate_thread, daemon=True).start()
    
    def delete_pdfs(self):
        """Yüklü PDF'leri ve database'i sil"""
        if not self.chatbot.use_rag or not self.chatbot.rag_manager:
            messagebox.showerror("Hata", "RAG sistemi aktif değil!")
            return
        
        if not self.chatbot.rag_manager.chunks:
            messagebox.showinfo("Bilgi", "Silinecek PDF bulunamadı!")
            return
        
        # Onay al
        chunk_count = len(self.chatbot.rag_manager.chunks)
        confirm = messagebox.askyesno(
            "PDF Silme Onayı",
            f"Toplam {chunk_count} parça silinecek.\n"
            "Tüm yüklü PDF'ler kalıcı olarak silinecek.\n\n"
            "Devam etmek istiyor musunuz?"
        )
        
        if not confirm:
            return
        
        try:
            # Database'i temizle
            success = self.chatbot.rag_manager.clear_database()
            
            if success:
                self.display_message(
                    "Sistem",
                    "Tüm PDF'ler başarıyla silindi!\n"
                    "Yeni PDF'ler yükleyebilirsiniz.",
                    "system"
                )
                self.status_label.config(text="PDF'ler silindi", foreground="green")
            else:
                self.display_message("Sistem", "PDF silme işlemi başarısız!", "system")
                self.status_label.config(text="Silme başarısız", foreground="red")
        except Exception as e:
            messagebox.showerror("Hata", f"PDF silme hatası: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatbotGUI(root)
    root.mainloop()
