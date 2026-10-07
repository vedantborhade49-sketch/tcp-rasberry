# AEROSAR Pi Video Sender

This repository contains the standalone Raspberry Pi video sender for the AEROSAR project. Its ONLY responsibility is to capture frames from a USB camera, encode them as JPEG, and transmit them via TCP to the ground station using the AEROSAR binary frame protocol.

It is completely independent from the main ground-station dashboard, YOLO, ROS, and any other system logic.

## Hardware Required
- Raspberry Pi 5
- USB camera connected to the Pi
- Wi-Fi or LAN connection
- Ground station laptop

## Installation

Run these commands on the Raspberry Pi 5:

```bash
# 1. Clone or copy the repository onto the Raspberry Pi 5
cd aerosar-pi-sender

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Configuration

All configuration is done in `config.py`.

### Ground Station IP
Open `config.py` and modify `GROUND_STATION_IP` to match the actual IP address of the ground station laptop on the LAN/Wi-Fi network.

```python
GROUND_STATION_IP = "192.168.1.105" # Change this!
GROUND_STATION_PORT = 5000
```

### USB Camera Verification
The default camera index is `0` (which typically maps to `/dev/video0`). You can verify your camera index by running:
```bash
ls /dev/video*
```
If your USB camera is on a different index, modify `CAMERA_INDEX` in `config.py`:
```python
CAMERA_INDEX = 0
```

## Running

On the Raspberry Pi, activate the virtual environment and start the sender:

```bash
source .venv/bin/activate
python sender.py
```

### Expected Output

```
========================================
AEROSAR PI VIDEO SENDER
========================================
Camera index   : 0
Resolution     : 1280x720
Target FPS     : 15
JPEG quality   : 80
Ground station : 192.168.1.105:5000
========================================
[PI] Connecting to ground station 192.168.1.105:5000
[PI] Connected to ground station
[PI] Streaming started
[PI] Frames sent: 45 | FPS: 15.0 | Data sent: 2.8 MB
[PI] Frames sent: 90 | FPS: 15.0 | Data sent: 5.6 MB
```

## Testing Procedure

You can test this repository in stages:

- **TEST 1:** USB camera opens. (You should see `Streaming started` or an error if it fails).
- **TEST 2 & 3:** Frames are captured and JPEG encoded (It will not crash and will proceed to TCP transmission).
- **TEST 4 & 5:** TCP connection reaches the ground station and JPEG packets are transmitted continuously. (You should see the frames sent and data sent statistics increasing).
- **TEST 6:** Disconnect the ground station (stop the server script on the laptop). The sender will output `Ground station connection lost` and start attempting to reconnect.
- **TEST 7:** Restart the ground station. The sender should output `Connected to ground station` and resume streaming.
- **TEST 8:** Stop the sender with `Ctrl+C`. You should see the clean shutdown sequence.

## Troubleshooting

- **Camera not detected:** Ensure the USB camera is firmly plugged in. Check `dmesg` or `ls /dev/video*`.
- **Wrong camera index:** If the Pi has another camera module or multiple video devices, the USB camera might be `/dev/video1` or `/dev/video2`. Change `CAMERA_INDEX` in `config.py`.
- **Ground station unreachable:** Ensure the Pi and the laptop are on the same Wi-Fi network. Ping the laptop IP from the Pi to verify connectivity. Check firewall settings on the laptop.
- **TCP connection refused:** Ensure the ground station receiving script/server is running and listening on the specified port (default `5000`) before expecting a successful connection (the Pi will automatically keep trying to reconnect).
- **Low FPS:** The target FPS is limited to what the Pi can process and transmit. Check your Wi-Fi bandwidth. The script uses OpenCV VideoCapture and limits to `TARGET_FPS`.

## Architectural Notes

- This repository is completely standalone. It contains no YOLO, no OpenCV detection logic, no ROS, no SLAM, no dashboard, and no LLM.
- The only contract between this repository and the AEROSAR ground station is the TCP connection and the 16-byte AEROSAR binary frame protocol.
