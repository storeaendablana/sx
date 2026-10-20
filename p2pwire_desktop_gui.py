# P2Pwire Premium Desktop GUI Client (CustomTkinter)
# Installation: pip install customtkinter soundcard numpy websockets
import customtkinter as ctk
import asyncio
import threading
import soundcard as sc
import numpy as np
import websockets
import socket
import subprocess
import platform
import concurrent.futures
import urllib.request

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class P2PwireApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("P2Pwire Ultra-Low Latency Audio Streamer")
        self.geometry("640x540")
        self.resizable(False, False)

        self.is_streaming = False
        self.is_scanning = False
        self.thread = None
        self.loop = None

        # Title Header
        self.header_label = ctk.CTkLabel(
            self, 
            text="⚡ P2Pwire Desktop Bridge", 
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#38BDF8"
        )
        self.header_label.pack(pady=(16, 4))

        self.sub_label = ctk.CTkLabel(
            self, 
            text="Direct PC Audio to Android Phone (Continuous Non-Stop Streaming)", 
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8"
        )
        self.sub_label.pack(pady=(0, 12))

        # Main Controls Frame
        self.control_frame = ctk.CTkFrame(self, corner_radius=12)
        self.control_frame.pack(padx=20, pady=8, fill="x")

        # IP Entry & Auto-Detect Row
        self.ip_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        self.ip_frame.pack(padx=16, pady=(14, 8), fill="x")

        self.lbl_ip = ctk.CTkLabel(self.ip_frame, text="Android IP Address:", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_ip.pack(side="left", padx=(0, 10))

        self.ip_entry = ctk.CTkEntry(
            self.ip_frame, 
            placeholder_text="e.g. 192.168.43.1 or 10.119.76.208", 
            width=240,
            font=ctk.CTkFont(family="monospace", size=13)
        )
        self.ip_entry.pack(side="left", padx=(0, 8))

        self.btn_detect = ctk.CTkButton(
            self.ip_frame,
            text="🔍 Auto-Detect",
            width=110,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            command=self.start_auto_detect
        )
        self.btn_detect.pack(side="left")

        # Stream Toggle Button
        self.btn_toggle = ctk.CTkButton(
            self.control_frame,
            text="🔊 Start Streaming System Audio",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=46,
            fg_color="#06B6D4",
            hover_color="#0891B2",
            command=self.toggle_stream
        )
        self.btn_toggle.pack(padx=16, pady=(10, 14), fill="x")

        # Live Status Card
        self.status_card = ctk.CTkFrame(self, corner_radius=10, fg_color="#1E293B")
        self.status_card.pack(padx=20, pady=6, fill="x")

        self.status_label = ctk.CTkLabel(
            self.status_card, 
            text="● Status: Ready to Connect", 
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#34D399"
        )
        self.status_label.pack(pady=8)

        # Activity Logs Box
        self.log_box = ctk.CTkTextbox(
            self, 
            height=210, 
            corner_radius=10,
            font=ctk.CTkFont(family="monospace", size=11),
            activate_scrollbars=True
        )
        self.log_box.pack(padx=20, pady=(6, 16), fill="both", expand=True)
        self.log("P2Pwire Desktop Bridge Initialized.")
        self.log("Click 'Auto-Detect' or 'Start Streaming' for 1-click automatic connection.")

        # Background auto-detect on startup
        threading.Thread(target=self.detect_android_device, args=(True,), daemon=True).start()

    def log(self, message):
        self.after(0, lambda: self._append_log(message))

    def _append_log(self, message):
        self.log_box.insert("end", f"{message}\n")
        self.log_box.see("end")

    def probe_ip(self, ip):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.06)
            res = sock.connect_ex((ip, 8080))
            sock.close()
            if res == 0:
                url = f"http://{ip}:8080/api/session"
                req = urllib.request.Request(url, headers={'User-Agent': 'P2PwireDesktop'})
                with urllib.request.urlopen(req, timeout=0.15) as response:
                    if response.status == 200:
                        return ip
        except Exception:
            pass
        return None

    def start_auto_detect(self):
        if self.is_scanning:
            return
        threading.Thread(target=self.detect_android_device, args=(False,), daemon=True).start()

    def detect_android_device(self, silent_startup=False):
        self.is_scanning = True
        self.after(0, lambda: self.btn_detect.configure(text="Scanning...", state="disabled"))
        if not silent_startup:
            self.after(0, lambda: self.status_label.configure(text="● Scanning local network for Android Phone...", text_color="#22D3EE"))
            self.log("Scanning network for P2Pwire Android device...")

        found_ip = None

        # 1. Hotspot Gateway Detection
        try:
            gateways = []
            if platform.system() == "Windows":
                out = subprocess.check_output("ipconfig", creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0).decode(errors="ignore")
                for line in out.splitlines():
                    if "Default Gateway" in line or "gateway" in line.lower():
                        parts = line.split(":")
                        if len(parts) > 1:
                            gw = parts[1].strip()
                            if gw and gw != "0.0.0.0" and not gw.startswith("::"):
                                gateways.append(gw)
            else:
                out = subprocess.check_output(["ip", "route"]).decode(errors="ignore")
                for line in out.splitlines():
                    if line.startswith("default via"):
                        gateways.append(line.split()[2])

            for gw in gateways:
                if self.probe_ip(gw):
                    found_ip = gw
                    break
        except Exception:
            pass

        # 2. Fast Common Subnet Probing
        if not found_ip:
            common_candidates = [
                "192.168.43.1",
                "192.168.43.2",
                "192.168.43.149",
                "192.168.1.1",
                "192.168.0.1",
                "10.119.76.208"
            ]
            for cand in common_candidates:
                if self.probe_ip(cand):
                    found_ip = cand
                    break

        # 3. Parallel Subnet Scan
        if not found_ip:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                my_ip = s.getsockname()[0]
                s.close()
                prefix = ".".join(my_ip.split(".")[:3])
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                    futures = [executor.submit(self.probe_ip, f"{prefix}.{i}") for i in range(1, 255)]
                    for future in concurrent.futures.as_completed(futures):
                        res = future.result()
                        if res:
                            found_ip = res
                            break
            except Exception:
                pass

        self.is_scanning = False
        if found_ip:
            self.after(0, lambda: self.ip_entry.delete(0, "end"))
            self.after(0, lambda: self.ip_entry.insert(0, found_ip))
            self.after(0, lambda: self.status_label.configure(text=f"● Android Phone Found: {found_ip}", text_color="#34D399"))
            self.log(f"Auto-Detected Android Device IP: {found_ip}")
        else:
            if not silent_startup:
                self.after(0, lambda: self.status_label.configure(text="● Phone not found on network. Enter IP manually.", text_color="#F87171"))
                self.log("Auto-detection finished: No active P2Pwire phone found on local subnet.")

        self.after(0, lambda: self.btn_detect.configure(text="🔍 Auto-Detect", state="normal"))
        return found_ip

    def toggle_stream(self):
        if not self.is_streaming:
            ip = self.ip_entry.get().strip()
            if not ip:
                self.status_label.configure(text="● Auto-Detecting Android IP...", text_color="#22D3EE")
                ip = self.detect_android_device(silent_startup=False)
                if not ip:
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
            reconnect_attempts = 0
            max_reconnects = 3

            while self.is_streaming:
                try:
                    self.log(f"Opening WebSocket connection to {uri}...")
                    # 20s Ping-Pong Heartbeat prevents Wi-Fi AP, hotspot NAT, and router idle drops
                    async with websockets.connect(
                        uri,
                        ping_interval=20,
                        ping_timeout=15,
                        close_timeout=5,
                        max_size=None
                    ) as ws:
                        reconnect_attempts = 0
                        self.after(0, lambda: self.status_label.configure(text="● Connected! Initializing Audio Loopback...", text_color="#34D399"))
                        self.log("WebSocket connection established successfully!")

                        speaker = sc.default_speaker()
                        self.log(f"Default speaker detected: {speaker.name}")
                        mic = sc.get_microphone(id=speaker.name, include_loopback=True)
                        self.log("Loopback audio capture device initialized successfully.")

                        self.after(0, lambda: self.status_label.configure(text="● Streaming Live 48kHz System Audio...", text_color="#34D399"))

                        # Decoupled Queue: Network delay won't stutter system audio
                        audio_queue = asyncio.Queue(maxsize=15)
                        stop_capture_event = threading.Event()

                        # Dedicated OS Thread for 48kHz audio capture (960 frames = 20ms chunks)
                        def audio_producer():
                            try:
                                with mic.recorder(samplerate=48000, channels=2) as recorder:
                                    while self.is_streaming and not stop_capture_event.is_set():
                                        data = recorder.record(numframes=960)
                                        mono = np.mean(data, axis=1)
                                        d = np.clip(mono, -1.0, 1.0)
                                        pcm16 = (d * 32767).astype(np.int16).tobytes()

                                        # If network buffer is full, drop oldest chunk to ensure absolute zero-lag
                                        if audio_queue.full():
                                            try:
                                                audio_queue.get_nowait()
                                            except Exception:
                                                pass
                                        self.loop.call_soon_threadsafe(audio_queue.put_nowait, pcm16)
                            except Exception as capture_err:
                                if self.is_streaming and not stop_capture_event.is_set():
                                    self.log(f"[CAPTURE ERROR] {capture_err}")

                        capture_thread = threading.Thread(target=audio_producer, daemon=True)
                        capture_thread.start()

                        seq = 0
                        stopped_by_phone = False
                        while self.is_streaming:
                            pcm16 = await audio_queue.get()
                            h = bytearray(8)
                            h[0], h[1], h[2] = 0xAB, 0x46, 0x01
                            h[3], h[4] = (seq >> 8) & 0xFF, seq & 0xFF
                            seq = (seq + 1) & 0xFFFF
                            try:
                                await ws.send(bytes(h) + pcm16)
                            except websockets.exceptions.ConnectionClosedOK:
                                stopped_by_phone = True
                                self.log("Audio playback stopped by Android phone.")
                                break
                            except Exception as send_ex:
                                self.log(f"Stream send interrupted: {send_ex}")
                                break

                        stop_capture_event.set()
                        if stopped_by_phone or not self.is_streaming:
                            self.is_streaming = False
                            break

                except Exception as e:
                    err_msg = str(e)
                    self.log(f"[STATUS] {err_msg}")

                if not self.is_streaming:
                    break

                # If connection dropped unexpectedly (router/Wi-Fi transient glitch), auto-reconnect
                reconnect_attempts += 1
                if reconnect_attempts <= max_reconnects and self.is_streaming:
                    self.log(f"Connection lost. Reconnecting in 1s (Attempt {reconnect_attempts}/{max_reconnects})...")
                    self.after(0, lambda: self.status_label.configure(text=f"● Reconnecting ({reconnect_attempts}/{max_reconnects})...", text_color="#FBBF24"))
                    await asyncio.sleep(1.0)
                else:
                    self.is_streaming = False
                    break

            self.after(0, lambda: self.status_label.configure(text="● Stopped / Ready to Connect", text_color="#FBBF24"))
            self.after(0, lambda: self.btn_toggle.configure(text="🔊 Start Streaming System Audio", fg_color="#06B6D4", hover_color="#0891B2"))
            self.after(0, lambda: self.status_label.configure(text="● Status: Ready to Connect", text_color="#34D399"))

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(stream())
        except Exception as ex:
            self.log(f"[FATAL] {ex}")

if __name__ == "__main__":
    app = P2PwireApp()
    app.mainloop()
