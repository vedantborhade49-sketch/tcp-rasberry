# AEROSAR Pi Video Sender (Production-Ready)

A robust, standalone Raspberry Pi 5 repository designed exclusively for capturing USB camera frames, encoding them to JPEG, and securely transmitting them over a TCP socket via the AEROSAR 16-byte protocol to the ground station.

It implements production-grade features including network keepalives, live video frame-dropping, auto-reconnection, and camera health recovery.

**NOTE: This repository strictly handles the `USB CAMERA -> TCP VIDEO` pipeline. It does not include YOLO, ROS, MAVLink, dashboards, or any analytics logic.**

## Architecture

```text
                  RASPBERRY PI 5

                  USB CAMERA
                       │
                       ▼
                Camera Manager
                       │
                       ▼
                OpenCV Frame
                       │
                       ▼
                  JPEG Encoder
                       │
                       ▼
                Frame Protocol
                       │
                       ▼
                  TCP Sender
                       │
                 Wi-Fi / LAN
                       │
                       ▼
              GROUND STATION IP
                    :5000
```

## Hardware Requirements
- Raspberry Pi 5
- USB camera connected directly to Pi
- Wi-Fi or LAN connection
- Ground station laptop running a compatible TCP server receiver

## Raspberry Pi Setup

```bash
# 1. Clone the repository onto the Raspberry Pi 5
git clone https://github.com/vedantborhade49-sketch/tcp-rasberry.git aerosar-pi-sender
cd aerosar-pi-sender

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install required dependencies
pip install -r requirements.txt
```

## Configuration

All configuration is strictly managed within `config.py`.

### Ground Station IP
Set `GROUND_STATION_IP` to match the exact LAN/Wi-Fi IP address of the ground station server.
```python
GROUND_STATION_IP = "192.168.1.105"
GROUND_STATION_PORT = 5000
```

### Camera Configuration
To find the correct `CAMERA_INDEX`, run:
```bash
ls /dev/video*
```
Adjust the parameters inside `config.py` if needed:
```python
CAMERA_INDEX = 0
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
TARGET_FPS = 15
```

## Running the Sender

Activate the environment and execute the script directly:
```bash
source .venv/bin/activate
python sender.py
```

### Expected Startup Output
```text
========================================
AEROSAR PI VIDEO SENDER - PRO
========================================
Camera index   : 0
Resolution     : 1280x720
Target FPS     : 15
JPEG quality   : 80
Ground station : 192.168.1.105:5000
========================================
[PI] INFO: State: CONNECTING
[PI] INFO: Connecting to ground station 192.168.1.105:5000
[PI] INFO: State: CONNECTED
[PI] INFO: Camera opened successfully
```

### Expected Streaming Output
```text
[PI] INFO: Starting camera capture loop
[PI] INFO: Starting network loop
[PI] INFO: State: STREAMING
[PI] INFO: STREAMING | FPS: 14.9 | Sent: 45 | Dropped: 0 | Data: 2.8 MB | Reconnects: 0
[PI] INFO: Latency -> Capture: 4.2 ms | JPEG: 8.1 ms | Send: 12.4 ms
```

## Testing Procedure

You can verify the system through these stages:

1. **Configuration validation:** Alter `config.py` with invalid types and observe `[PI] ERROR: CONFIGURATION ERROR`.
2. **USB camera detection & capture:** Watch the `Camera opened successfully` log ensure the correct `/dev/videoX` index is used.
3. **TCP Connection:** Bring the ground station online and offline to verify the transitions between `CONNECTING`, `CONNECTED`, and `STREAMING`.
4. **Auto-Reconnect:** Disconnect the ground station during streaming to verify it safely handles the socket drop (`Closing broken socket`) and resumes `CONNECTING`.
5. **Frame-drop policy:** While disconnected, the Pi avoids crashing by safely dropping stale frames, maintaining the `MAX_BUFFERED_FRAMES=1` policy.
6. **Clean Shutdown:** Hit `Ctrl+C` to test the orderly release of all threads, the camera, and the sockets.

## Behavior & Troubleshooting

- **Reconnection Behavior:** If the ground station server stops or Wi-Fi drops, the system state becomes `DISCONNECTED` and immediately begins retrying every `RECONNECT_DELAY` seconds. It will not leak memory; stale frames in the 1-frame queue are safely dropped to maintain live video prioritization.
- **Camera Recovery Behavior:** If the USB camera glitches or disconnects momentarily and 10 consecutive capture failures occur, the system triggers a camera recovery sequence (`[PI] Attempting camera recovery...`).
- **Network Troubleshooting:** Ensure the laptop firewall permits incoming TCP connections on the configured port (default `5000`).
- **Shutdown Procedure:** Press `Ctrl+C` to trigger a clean shutdown sequence that gracefully releases the camera hardware and closes active sockets.
