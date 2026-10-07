import socket
import time
import sys
import threading
import queue
import config
from camera import USBCamera
from protocol import AerosarProtocol

class State:
    OFFLINE = "OFFLINE"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    STREAMING = "STREAMING"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"

class AerosarSender:
    def __init__(self):
        # Configuration Validation
        config.validate_config()
        
        self.state = State.OFFLINE
        self.camera = USBCamera()
        self.protocol = AerosarProtocol()
        self.sock = None
        self.running = False
        self.frame_id = 0
        
        # Bounded frame queue
        self.frame_queue = queue.Queue(maxsize=config.MAX_BUFFERED_FRAMES)
        
        # Performance Monitoring
        self.stats = {
            "captured": 0,
            "encoded": 0,
            "transmitted": 0,
            "dropped": 0,
            "bytes_sent": 0,
            "reconnects": 0
        }
        self.last_stats_time = time.time()
        self.frames_since_stats = 0
        
        # Latency Tracking
        self.last_capture_ms = 0.0
        self.last_encode_ms = 0.0
        self.last_send_ms = 0.0
        
        # Network Health
        self.last_success_time = time.time()

    def set_state(self, new_state):
        if self.state != new_state:
            self.state = new_state
            print(f"[PI] INFO: State: {self.state}")

    def setup_keepalive(self):
        """Enables TCP Keepalive to quickly detect broken connections."""
        if self.sock is None:
            return
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # Linux specific TCP keepalive config
            if hasattr(socket, 'TCP_KEEPIDLE'):
                self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 5)
                self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 2)
                self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
        except Exception as e:
            # Safely ignore if not fully supported on the platform
            pass

    def print_startup_banner(self):
        print("========================================")
        print("AEROSAR PI VIDEO SENDER - PRO")
        print("========================================")
        print(f"Camera index   : {config.CAMERA_INDEX}")
        print(f"Resolution     : {config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT}")
        print(f"Target FPS     : {config.TARGET_FPS}")
        print(f"JPEG quality   : {config.JPEG_QUALITY}")
        print(f"Ground station : {config.GROUND_STATION_IP}:{config.GROUND_STATION_PORT}")
        print("========================================")

    def print_stats(self):
        now = time.time()
        elapsed = now - self.last_stats_time
        
        if elapsed >= config.STATS_INTERVAL:
            fps = self.frames_since_stats / elapsed
            mb_sent = self.stats['bytes_sent'] / (1024 * 1024)
            
            if self.state == State.STREAMING:
                print(f"[PI] INFO: STREAMING | FPS: {fps:.1f} | Sent: {self.stats['transmitted']} | "
                      f"Dropped: {self.stats['dropped']} | Data: {mb_sent:.1f} MB | "
                      f"Reconnects: {self.stats['reconnects']}")
                print(f"[PI] INFO: Latency -> Capture: {self.last_capture_ms:.1f} ms | "
                      f"JPEG: {self.last_encode_ms:.1f} ms | Send: {self.last_send_ms:.1f} ms")
                
                # Network health check
                if (now - self.last_success_time) > config.STATS_INTERVAL:
                    print(f"[PI] WARNING: No successful frame transmission recently")
                    
            self.last_stats_time = now
            self.frames_since_stats = 0

    def camera_loop(self):
        print("[PI] INFO: Starting camera capture loop")
        frame_delay = 1.0 / config.TARGET_FPS
        
        while self.running:
            loop_start = time.time()
            
            # Camera Health Monitoring & Recovery
            if self.camera.needs_recovery():
                if not self.camera.recover():
                    time.sleep(1.0)
                    continue
            
            # Capture
            ret, frame, cap_ms = self.camera.read_frame()
            if not ret:
                time.sleep(0.01)
                continue
                
            self.stats['captured'] += 1
            self.last_capture_ms = cap_ms
            
            # JPEG Encode
            ret, jpeg_bytes, enc_ms = self.camera.encode_jpeg(frame)
            if not ret:
                print("[PI] WARNING: JPEG encoding failed")
                continue
                
            self.stats['encoded'] += 1
            self.last_encode_ms = enc_ms
            
            # Enqueue for transmission (Live Video / Frame-Drop Policy)
            try:
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                        self.stats['dropped'] += 1
                    except queue.Empty:
                        pass
                self.frame_queue.put_nowait(jpeg_bytes)
            except queue.Full:
                self.stats['dropped'] += 1
                
            # Maintain Target FPS
            processing_time = time.time() - loop_start
            sleep_time = frame_delay - processing_time
            if sleep_time > 0:
                time.sleep(sleep_time)

    def network_loop(self):
        print("[PI] INFO: Starting network loop")
        
        while self.running:
            # Reconnect Logic
            if self.state in [State.OFFLINE, State.DISCONNECTED]:
                self.set_state(State.CONNECTING)
                print(f"[PI] INFO: Connecting to ground station {config.GROUND_STATION_IP}:{config.GROUND_STATION_PORT}")
                
                try:
                    if self.sock is not None:
                        self.sock.close()
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.setup_keepalive()
                    self.sock.connect((config.GROUND_STATION_IP, config.GROUND_STATION_PORT))
                    self.set_state(State.CONNECTED)
                    self.last_success_time = time.time()
                except socket.error as e:
                    print(f"[PI] ERROR: Connection failed: {e}")
                    self.set_state(State.DISCONNECTED)
                    self.stats['reconnects'] += 1
                    print(f"[PI] INFO: Retrying in {config.RECONNECT_DELAY} seconds...")
                    time.sleep(config.RECONNECT_DELAY)
                    continue
                    
            elif self.state in [State.CONNECTED, State.STREAMING]:
                try:
                    # Fetch next frame
                    jpeg_bytes = self.frame_queue.get(timeout=0.5)
                    
                    if self.state == State.CONNECTED:
                        self.set_state(State.STREAMING)
                    
                    # Pack AEROSAR Packet
                    packet = self.protocol.pack_frame(self.frame_id, jpeg_bytes)
                    
                    # Transmit
                    send_start = time.time()
                    self.sock.sendall(packet)
                    self.last_send_ms = (time.time() - send_start) * 1000.0
                    
                    # Frame successfully transmitted, so increment frame_id
                    self.frame_id += 1
                    self.stats['transmitted'] += 1
                    self.frames_since_stats += 1
                    self.stats['bytes_sent'] += len(packet)
                    self.last_success_time = time.time()
                    
                except queue.Empty:
                    # No frame ready, just timeout and verify connection state
                    pass
                except socket.error as e:
                    print(f"[PI] ERROR: TCP connection lost: {e}")
                    print(f"[PI] INFO: Closing broken socket")
                    self.set_state(State.DISCONNECTED)
                    self.stats['reconnects'] += 1
                    
            self.print_stats()

    def run(self):
        self.print_startup_banner()
        
        if not self.camera.open():
            print("[PI] ERROR: Cannot open USB camera")
            self.set_state(State.ERROR)
            sys.exit(1)
            
        print("[PI] INFO: Camera opened successfully")
        self.running = True
        
        cam_thread = threading.Thread(target=self.camera_loop, daemon=True)
        net_thread = threading.Thread(target=self.network_loop, daemon=True)
        
        cam_thread.start()
        net_thread.start()
        
        try:
            while self.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n[PI] INFO: Shutdown requested")
        finally:
            self.running = False
            print("[PI] INFO: Stopping stream")
            self.camera.release()
            print("[PI] INFO: Camera released")
            if self.sock:
                self.sock.close()
            print("[PI] INFO: TCP socket closed")
            print("[PI] INFO: Sender stopped")

if __name__ == "__main__":
    sender = AerosarSender()
    sender.run()
