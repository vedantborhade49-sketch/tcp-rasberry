import cv2
import config

class USBCamera:
    def __init__(self):
        self.cap = None
        self.camera_index = config.CAMERA_INDEX
        
    def open(self):
        """Opens the USB camera using OpenCV VideoCapture."""
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            return False
            
        # Set resolution and FPS
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, config.TARGET_FPS)
        
        return True
        
    def read_frame(self):
        """
        Captures a single frame from the camera.
        
        Returns:
            bool, frame: (True, BGR frame) if successful, (False, None) otherwise.
        """
        if self.cap is None or not self.cap.isOpened():
            return False, None
            
        ret, frame = self.cap.read()
        if not ret:
            return False, None
            
        return True, frame
        
    def encode_jpeg(self, frame):
        """
        Encodes a BGR frame into JPEG format.
        
        Args:
            frame: OpenCV BGR image.
            
        Returns:
            bool, bytes: (True, JPEG bytes) if successful, (False, None) otherwise.
        """
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), config.JPEG_QUALITY]
        ret, jpeg = cv2.imencode('.jpg', frame, encode_param)
        
        if not ret:
            return False, None
            
        return True, jpeg.tobytes()
        
    def release(self):
        """Releases the camera resources cleanly."""
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
