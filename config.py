import sys

# ==============================================================================
# AEROSAR PI SENDER CONFIGURATION
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. GROUND STATION CONNECTION
# ------------------------------------------------------------------------------
# Replace this IP with the actual IP address of the ground station laptop
# running on the same LAN/Wi-Fi network. Do not use 127.0.0.1 or localhost.
GROUND_STATION_IP = "192.168.1.105"
GROUND_STATION_PORT = 5000

# Seconds to wait before reconnecting if connection is lost
RECONNECT_DELAY = 2.0

# ------------------------------------------------------------------------------
# 2. CAMERA SETTINGS
# ------------------------------------------------------------------------------
# Index of the USB camera (typically 0 for the first connected camera, e.g. /dev/video0)
CAMERA_INDEX = 0

# Target resolution
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

# Target frame rate
TARGET_FPS = 15

# JPEG encoding quality (1-100)
JPEG_QUALITY = 80

# Camera health monitoring
MAX_CONSECUTIVE_CAMERA_FAILURES = 10

# ------------------------------------------------------------------------------
# 3. STREAMING & LOGGING SETTINGS
# ------------------------------------------------------------------------------
# Bound the frame queue to prefer new frames over stale buffered frames
MAX_BUFFERED_FRAMES = 1

# Interval in seconds to print statistics (frames sent, data sent, latency, etc.)
STATS_INTERVAL = 3.0


def validate_config():
    """Validates configuration types and ranges before startup."""
    errors = []
    
    if not isinstance(GROUND_STATION_IP, str) or not GROUND_STATION_IP:
        errors.append("GROUND_STATION_IP must be a valid IP string.")
        
    if not isinstance(GROUND_STATION_PORT, int) or not (1 <= GROUND_STATION_PORT <= 65535):
        errors.append("GROUND_STATION_PORT must be an integer between 1 and 65535.")
        
    if not isinstance(CAMERA_INDEX, int) or CAMERA_INDEX < 0:
        errors.append("CAMERA_INDEX must be an integer >= 0.")
        
    if not isinstance(CAMERA_WIDTH, int) or CAMERA_WIDTH <= 0:
        errors.append("CAMERA_WIDTH must be > 0.")
        
    if not isinstance(CAMERA_HEIGHT, int) or CAMERA_HEIGHT <= 0:
        errors.append("CAMERA_HEIGHT must be > 0.")
        
    if not isinstance(TARGET_FPS, (int, float)) or TARGET_FPS <= 0:
        errors.append("TARGET_FPS must be > 0.")
        
    if not isinstance(JPEG_QUALITY, int) or not (1 <= JPEG_QUALITY <= 100):
        errors.append("JPEG_QUALITY must be between 1 and 100.")
        
    if not isinstance(RECONNECT_DELAY, (int, float)) or RECONNECT_DELAY < 0:
        errors.append("RECONNECT_DELAY must be >= 0.")
        
    if errors:
        for error in errors:
            print(f"[PI] ERROR: CONFIGURATION ERROR: {error}")
        sys.exit(1)
