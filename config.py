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
RECONNECT_DELAY = 2

# ------------------------------------------------------------------------------
# 2. CAMERA SETTINGS
# ------------------------------------------------------------------------------
# Index of the USB camera (typically 0 for the first connected camera, e.g. /dev/video0)
CAMERA_INDEX = 0

# Target resolution
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# Target frame rate
TARGET_FPS = 15

# JPEG encoding quality (0-100)
JPEG_QUALITY = 80

# ------------------------------------------------------------------------------
# 3. LOGGING SETTINGS
# ------------------------------------------------------------------------------
# Interval in seconds to print statistics (frames sent, data sent, etc.)
STATS_INTERVAL = 3
