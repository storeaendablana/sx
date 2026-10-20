# P2Pwire Premium Desktop GUI Client (CustomTkinter)
# Run: pip install customtkinter soundcard numpy websockets
import customtkinter as ctk
import asyncio
import threading
import traceback
import soundcard as sc
import numpy as np
import websockets

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class P2PwireApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("P2Pwire - Desktop System Audio Bridge")
        self.geometry("480x420")
        self.resizable(False, False)
        
        self.is_streaming = False
        self.loop = None
        self.thread = None

        self.title_label = ctk.CTkLabel(self, text="🚀 P2Pwire System Audio Bridge", font=ctk.CTkFont(size=18, weight="bold"))
        self.title_label.pack(pady=(20, 10))

        self.subtitle_label = ctk.CTkLabel(self, text="Stream 100% pure system audio to your Android phone", font=ctk.CTkFont(size=12), text_color="#94A3B8")
        self.subtitle_label.pack(pady=(0, 15))

        self.ip_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.ip_frame.pack(fill="x", padx=30, pady=5)

        self.ip_label = ctk.CTkLabel(self.ip_frame, text="Android Phone IP (from app screen):", font=ctk.CTkFont(size=13, weight="bold"))
        self.ip_label.pack(anchor="w", padx=5)

        self.ip_entry = ctk.CTkEntry(self.ip_frame, placeholder_text="e.g. 192.168.1.15", height=38, font=ctk.CTkFont(size=13))
        self.ip_entry.pack(fill="x", pady=(5, 0))
        self.ip_entry.insert(0, "192.168.43.1")

        self.status_label = ctk.CTkLabel(self, text="● Status: Ready to Connect", font=ctk.CTkFont(size=12, weight="bold"), text_color="#FBBF24")
        self.status_label.pack(pady=12)

        self.btn_toggle = ctk.CTkButton(self, text="🔊 Start Streaming System Audio", command=self.toggle_stream, height=45, fg_color="#06B6D4", hover_color="#0891B2", font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_toggle.pack(fill="x", padx=30, pady=10)

        # Log box for debugging
        self.log_box = ctk.CTkTextbox(self, height=80, font=ctk.CTkFont(size=11), text_color="#38BDF8")
        self.log_box.pack(fill="x", padx=30, pady=(0, 15))
        self.log_box.insert("0.0", "Logs & Connection Status will appear here...\n")

    def log(self, msg):
        print(msg)
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")

    def toggle_stream(self):
        if not self.is_streaming:
            ip = self.ip_entry.get().strip()
            if not ip:
                self.status_label.configure(text="● Error: Enter valid IP address", text_color="#F87171")
                return
            self.is_streaming = True
            self.btn_toggle.configure(text="⏹️ Stop Streaming", fg_color="#EF4444", hover_color="#DC2626")
            self.status_label.configure(text=f"● Connecting to {ip}...", text_color="#22D3EE")
            self.log(f"Attempting connection to ws://{ip}:8080/ws/upload_audio...")
            
            self.thread = threading.Thread(target=self.run_async_stream, args=(ip,), daemon=True)
            self.thread.start()
        else:
            self.is_streaming = False
            self.btn_toggle.configure(text="🔊 Start Streaming System Audio", fg_color="#06B6D4", hover_color="#0891B2")
            self.status_label.configure(text="● Status: Disconnected", text_color="#FBBF24")
            self.log("Streaming stopped by user.")

    def run_async_stream(self, ip):
        async def stream():
            uri = f"ws://{ip}:8080/ws/upload_audio"
            try:
                self.log(f"Opening WebSocket connection to {uri}...")
                # ping_interval=None prevents keepalive timeout disconnects
                async with websockets.connect(uri, ping_interval=None, ping_timeout=None) as ws:
                    self.after(0, lambda: self.status_label.configure(text="● Connected! Initializing Audio Loopback...", text_color="#34D399"))
                    self.log("WebSocket connection established successfully!")
                    
                    speaker = sc.default_speaker()
                    self.log(f"Default speaker detected: {speaker.name}")
                    mic = sc.get_microphone(id=speaker.name, include_loopback=True)
                    self.log("Loopback audio capture device initialized successfully.")
                    
                    self.after(0, lambda: self.status_label.configure(text="● Streaming Live 48kHz System Audio...", text_color="#34D399"))
                    seq = 0
                    # numframes=256 and channels=2 for zero stutter and unsupported format fix
                    with mic.recorder(samplerate=48000, channels=2) as recorder:
                        while self.is_streaming:
                            data = recorder.record(numframes=256)
                            mono = np.mean(data, axis=1)
                            d = np.clip(mono, -1.0, 1.0)
                            pcm16 = (d * 32767).astype(np.int16).tobytes()
                            h = bytearray(8)
                            h[0], h[1], h[2] = 0xAB, 0x46, 0x01
                            h[3], h[4] = (seq >> 8) & 0xFF, seq & 0xFF
                            seq = (seq + 1) & 0xFFFF
                            await ws.send(bytes(h) + pcm16)
            except Exception as e:
                err_msg = str(e)
                self.log(f"[ERROR] {err_msg}")
                traceback.print_exc()
                if self.is_streaming:
                    self.after(0, lambda: self.status_label.configure(text=f"● Error: {err_msg[:35]}", text_color="#F87171"))
                    self.after(0, self.toggle_stream)

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(stream())
        except Exception as ex:
            self.log(f"[FATAL] {ex}")

if __name__ == "__main__":
    app = P2PwireApp()
    app.mainloop()
