import cv2
import time
import config

class USBCamera:
    def __init__(self):
        self.cap = None
        self.failure_count = 0
        
    def open(self):
        """Opens the USB camera and configures it."""
        if self.cap is not None:
            self.release()
            
        self.cap = cv2.VideoCapture(config.CAMERA_INDEX)
        
        if not self.cap.isOpened():
            return False
            
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, config.TARGET_FPS)
        self.failure_count = 0
        return True
        
    def read_frame(self):
        """
        Captures a single frame, tracks capture latency and health.
        Returns:
            bool, frame, latency_ms
        """
        if self.cap is None or not self.cap.isOpened():
            return False, None, 0.0
            
        start_time = time.time()
        ret, frame = self.cap.read()
        latency_ms = (time.time() - start_time) * 1000.0
        
        if not ret:
            self.failure_count += 1
            print(f"[PI] WARNING: Camera frame capture failed ({self.failure_count}/{config.MAX_CONSECUTIVE_CAMERA_FAILURES})")
            return False, None, 0.0
            
        self.failure_count = 0
        return True, frame, latency_ms
        
    def needs_recovery(self):
        """Checks if consecutive failures exceeded threshold."""
        return self.failure_count >= config.MAX_CONSECUTIVE_CAMERA_FAILURES
        
    def recover(self):
        """Attempts to recover the camera connection."""
        print("[PI] WARNING: Camera appears unavailable")
        print("[PI] INFO: Attempting camera recovery...")
        self.release()
        time.sleep(1.0)
        if self.open():
            print("[PI] INFO: Camera reopened successfully")
            return True
        return False
        
    def encode_jpeg(self, frame):
        """
        Encodes frame to JPEG.
        Returns:
            bool, jpeg_bytes, latency_ms
        """
        start_time = time.time()
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), config.JPEG_QUALITY]
        ret, jpeg = cv2.imencode('.jpg', frame, encode_param)
        latency_ms = (time.time() - start_time) * 1000.0
        
        if not ret:
            return False, None, 0.0
            
        return True, jpeg.tobytes(), latency_ms
        
    def release(self):
        """Releases the camera safely."""
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        self.cap = None
