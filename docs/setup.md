# Setup Guide

Complete setup instructions for the baby monitor system.

## Prerequisites

### Hardware
- Raspberry Pi Zero 2 W
- Camera Module 3 (connected via ribbon cable)
- MicroSD card (8GB+) with Raspberry Pi OS
- Power supply (5V/2.5A recommended)

### Software (on Pi)
- Raspberry Pi OS Bookworm or newer
- rpicam-apps (pre-installed on recent OS)

### Network
- Pi connected to WiFi
- SSH access enabled

## Step 1: Verify Camera

SSH into your Pi and verify the camera is detected:

```bash
ssh raspberrypi-zero
rpicam-hello --list-cameras
```

Expected output:
```
Available cameras
-----------------
0 : imx708 [4608x2592 10-bit RGGB] (/base/soc/i2c0mux/i2c@1/imx708@1a)
    Modes: 'SRGGB10_CSI2P' : 1536x864 [120.13 fps]
                            2304x1296 [56.03 fps]
                            4608x2592 [14.35 fps]
```

## Step 2: Install MediaMTX

MediaMTX is a lightweight media server that handles video streaming.

```bash
# On the Raspberry Pi
cd ~

# Download MediaMTX for ARM (Pi Zero 2 W is armv7)
wget https://github.com/bluenviron/mediamtx/releases/download/v1.9.3/mediamtx_v1.9.3_linux_arm64v8.tar.gz

# Extract
tar -xzf mediamtx_v1.9.3_linux_arm64v8.tar.gz

# Move to system location
sudo mv mediamtx /usr/local/bin/
sudo chmod +x /usr/local/bin/mediamtx

# Clean up
rm mediamtx_v1.9.3_linux_arm64v8.tar.gz
```

## Step 3: Deploy Configuration

From your local machine:

```bash
cd ~/repos/personal/baby-monitor
./scripts/deploy.sh
```

This will:
1. Copy configuration files to the Pi
2. Install the systemd service
3. Start the baby monitor

## Step 4: Verify Installation

```bash
# Check service status
ssh raspberrypi-zero "sudo systemctl status baby-monitor"

# View logs
ssh raspberrypi-zero "sudo journalctl -u baby-monitor -f"
```

## Step 5: Access the Monitor

Open in your browser:
```
http://192.168.1.14:8889/baby-monitor
```

## Camera Module 3 Features

### Night Vision
The Camera Module 3 has excellent low-light performance. The web interface includes a night mode toggle that:
- Adjusts exposure settings for low light
- Increases gain for better visibility
- Optimizes for infrared (if using IR illuminator)

### Supported Resolutions

| Resolution | FPS | Use Case |
|------------|-----|----------|
| 1536x864 | 120 | High motion (not recommended for baby monitor) |
| 1280x720 | 30 | **Recommended** - good balance |
| 1920x1080 | 30 | Higher quality, more bandwidth |
| 640x480 | 30 | Low bandwidth situations |

## Firewall Configuration

If you have a firewall enabled:

```bash
sudo ufw allow 8889/tcp  # Web UI and WebRTC
sudo ufw allow 8554/tcp  # RTSP (optional)
```

## Updating

To update the configuration or web interface:

```bash
# From local machine
./scripts/deploy.sh
```

The deploy script will restart the service automatically.
