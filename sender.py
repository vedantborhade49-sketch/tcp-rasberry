import socket
import time
import sys
import config
from camera import USBCamera
from protocol import AerosarProtocol

def print_startup_banner():
    print("========================================")
    print("AEROSAR PI VIDEO SENDER")
    print("========================================")
    print(f"Camera index   : {config.CAMERA_INDEX}")
    print(f"Resolution     : {config.FRAME_WIDTH}x{config.FRAME_HEIGHT}")
    print(f"Target FPS     : {config.TARGET_FPS}")
    print(f"JPEG quality   : {config.JPEG_QUALITY}")
    print(f"Ground station : {config.GROUND_STATION_IP}:{config.GROUND_STATION_PORT}")
    print("========================================")

def main():
    print_startup_banner()
    
    # Initialize camera
    camera = USBCamera()
    if not camera.open():
        print("[PI] ERROR: Cannot open USB camera")
        sys.exit(1)
        
    # Initialize protocol
    protocol = AerosarProtocol()
    
    sock = None
    connected = False
    
    # Statistics
    frames_sent = 0
    total_bytes_sent = 0
    last_stats_time = time.time()
    frames_since_last_stats = 0
    
    # Calculate target frame delay
    frame_delay = 1.0 / config.TARGET_FPS
    
    try:
        while True:
            # Reconnection logic
            if not connected:
                print(f"[PI] Connecting to ground station {config.GROUND_STATION_IP}:{config.GROUND_STATION_PORT}")
                try:
                    if sock is not None:
                        sock.close()
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((config.GROUND_STATION_IP, config.GROUND_STATION_PORT))
                    connected = True
                    print("[PI] Connected to ground station")
                    print("[PI] Streaming started")
                    
                    # Reset stats on new connection
                    last_stats_time = time.time()
                    frames_since_last_stats = 0
                    
                except socket.error:
                    print(f"[PI] Connection failed")
                    print(f"[PI] Retrying in {config.RECONNECT_DELAY} seconds...")
                    time.sleep(config.RECONNECT_DELAY)
                    continue

            # Capture frame
            loop_start = time.time()
            ret, frame = camera.read_frame()
            
            if not ret:
                print("[PI] WARNING: Camera frame capture failed")
                time.sleep(0.1) # Brief pause before retrying
                continue
                
            # JPEG encode
            ret, jpeg_bytes = camera.encode_jpeg(frame)
            if not ret:
                print("[PI] WARNING: JPEG encoding failed")
                continue
                
            # Pack using AEROSAR protocol
            packet = protocol.pack_frame(jpeg_bytes)
            
            # Transmit
            try:
                # Use sendall to ensure complete packet transmission
                sock.sendall(packet)
                
                # Update statistics
                frames_sent += 1
                frames_since_last_stats += 1
                total_bytes_sent += len(packet)
                
                # Print statistics periodically
                current_time = time.time()
                time_elapsed = current_time - last_stats_time
                if time_elapsed >= config.STATS_INTERVAL:
                    fps = frames_since_last_stats / time_elapsed
                    mb_sent = total_bytes_sent / (1024 * 1024)
                    print(f"[PI] Frames sent: {frames_sent} | FPS: {fps:.1f} | Data sent: {mb_sent:.1f} MB")
                    last_stats_time = current_time
                    frames_since_last_stats = 0
                    
            except socket.error:
                print("[PI] Ground station connection lost")
                print("[PI] Reconnecting...")
                connected = False
                continue
                
            # Sleep to maintain target FPS (if processing was faster than frame_delay)
            processing_time = time.time() - loop_start
            sleep_time = frame_delay - processing_time
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n[PI] Shutdown requested")
        
    finally:
        # Clean shutdown
        camera.release()
        print("[PI] Camera released")
        
        if sock is not None:
            sock.close()
            print("[PI] TCP connection closed")
            
        print("[PI] Sender stopped")

if __name__ == "__main__":
    main()
