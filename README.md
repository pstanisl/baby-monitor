# Baby Monitor

A lightweight baby monitoring solution using Raspberry Pi Zero 2 W and Camera Module 3.

## Features

### Current
- [x] Live video streaming (HLS/WebRTC)
- [x] Night mode toggle (exposure/gain adjustment)
- [x] Web-based interface (works on any device)
- [x] Auto-start on boot

### Planned
- [ ] Motion detection alerts
- [ ] Audio monitoring (ReSpeaker 2-Mics Pi HAT)
- [ ] Recording capabilities
- [ ] Mobile notifications

## Hardware

| Component | Model | Notes |
|-----------|-------|-------|
| Computer | Raspberry Pi Zero 2 W | Quad-core, 512MB RAM |
| Camera | Camera Module 3 | IMX708, autofocus, good low-light |
| Audio (future) | ReSpeaker 2-Mics Pi HAT | Not yet connected |

## Quick Start

### Prerequisites

- Raspberry Pi Zero 2 W with Raspberry Pi OS (Bookworm/Trixie)
- Camera Module 3 connected and detected
- SSH access to the Pi (`ssh raspberrypi-zero`)

### Deployment

```bash
# From your local machine
cd ~/repos/personal/baby-monitor
./scripts/deploy.sh
```

### Access

Open in any browser on your network:
```
http://192.168.1.14:8889/baby-monitor/
```

Control API:
```
http://192.168.1.14:5000/api/status
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Raspberry Pi Zero 2 W                                      │
│                                                             │
│  ┌──────────┐    ┌─────────────────────────────────────┐   │
│  │ Camera   │───▶│         MediaMTX Server             │   │
│  │ IMX708   │    │  - Native rpiCamera source          │   │
│  └──────────┘    │  - Hardware H264 encoding           │   │
│                  │  - WebRTC/HLS/RTSP streaming        │   │
│                  └───────────────┬─────────────────────┘   │
│                                  │                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Camera Control API (port 5000)                     │   │
│  │  - Night mode toggle                                │   │
│  │  - Config management                                │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────────────────│──────────────────────────┘
                                   │
                    ┌──────────────┼─────────────┐
                    │              ▼             │
                    │  Browser (phone/tablet/PC) │
                    │  http://192.168.1.14:8889  │
                    │      Local Network         │
                    └────────────────────────────┘
```

## Project Structure

```
baby-monitor/
├── README.md                 # This file
├── docs/
│   ├── setup.md              # Initial setup guide
│   ├── streaming.md          # Streaming configuration details
│   └── future/
│       ├── motion-detection.md
│       └── audio-monitoring.md
├── scripts/
│   └── deploy.sh             # Deployment script
└── pi/                       # Files deployed to Raspberry Pi
    ├── config/
    │   └── mediamtx.yml      # MediaMTX configuration
    ├── scripts/
    │   └── camera_control.py # Night mode API
    ├── services/
    │   ├── baby-monitor.service
    │   └── baby-monitor-api.service
    └── web/
        └── index.html        # Web interface
```

## Documentation

- [Setup Guide](docs/setup.md) - Initial installation and configuration
- [Streaming Details](docs/streaming.md) - How the streaming works

### Future Features
- [Motion Detection](docs/future/motion-detection.md) - Planned implementation
- [Audio Monitoring](docs/future/audio-monitoring.md) - ReSpeaker integration

## Network Configuration

| Service | Port | Protocol | Description |
|---------|------|----------|-------------|
| WebRTC Stream | 8889 | HTTP/WS | Primary low-latency stream |
| HLS Stream | 8888 | HTTP | Fallback stream |
| RTSP | 8554 | RTSP | For VLC/ffplay |
| Control API | 5000 | HTTP | Night mode toggle |
| MediaMTX API | 9997 | HTTP | Internal MediaMTX API |

## API Endpoints

### Control API (port 5000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Current status and mode |
| `/api/night-mode` | GET | Get night mode state |
| `/api/night-mode` | POST | Set night mode `{"enabled": true/false}` |

## Troubleshooting

### Camera not detected
```bash
ssh raspberrypi-zero "rpicam-hello --list-cameras"
```

### Service status
```bash
ssh raspberrypi-zero "sudo systemctl status baby-monitor"
ssh raspberrypi-zero "sudo journalctl -u baby-monitor -f"
```

### Restart services
```bash
ssh raspberrypi-zero "sudo systemctl restart baby-monitor baby-monitor-api"
```

### Test night mode
```bash
# Enable night mode
curl -X POST http://192.168.1.14:5000/api/night-mode \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'

# Disable night mode
curl -X POST http://192.168.1.14:5000/api/night-mode \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

## License

MIT
