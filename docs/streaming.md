# Streaming Configuration

Technical details about how the video streaming works.

## Overview

The streaming uses MediaMTX with its native Raspberry Pi camera support (`rpiCamera` source). This approach is simpler and more efficient than using a separate rpicam-vid process.

## Pipeline Details

```
Camera (IMX708)
     │
     ▼ (raw RGGB via libcamera)
┌─────────────────────┐
│      MediaMTX       │
│ - Direct camera     │
│ - Hardware H264 enc │
│ - WebRTC server     │
│ - HLS server        │
└─────────────────────┘
     │
     ├──▶ WebRTC (low latency, ~500ms)
     ├──▶ HLS (higher latency, ~3-5s, better compatibility)
     └──▶ RTSP (for VLC, etc.)
```

## MediaMTX Configuration

Key settings in `mediamtx.yml`:

```yaml
paths:
  baby-monitor:
    source: rpiCamera

    # Resolution and framerate
    rpiCameraWidth: 1280
    rpiCameraHeight: 720
    rpiCameraFPS: 30

    # Video encoding
    rpiCameraCodec: auto        # Uses hardware H264
    rpiCameraBitrate: 2000000   # 2 Mbps
    rpiCameraProfile: baseline
    rpiCameraLevel: "4.1"

    # Auto white balance and autofocus
    rpiCameraAWB: auto
    rpiCameraAfMode: continuous

    # Exposure
    rpiCameraExposure: normal
```

### Available rpiCamera Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `rpiCameraWidth` | 1920 | Frame width in pixels |
| `rpiCameraHeight` | 1080 | Frame height in pixels |
| `rpiCameraFPS` | 30 | Frames per second |
| `rpiCameraCodec` | auto | Video codec (auto uses hardware H264) |
| `rpiCameraBitrate` | 5000000 | Target bitrate in bps |
| `rpiCameraProfile` | baseline | H264 profile |
| `rpiCameraLevel` | 4.1 | H264 level |
| `rpiCameraAWB` | auto | Auto white balance mode |
| `rpiCameraAfMode` | continuous | Autofocus mode |
| `rpiCameraExposure` | normal | Exposure mode (normal, long) |
| `rpiCameraEV` | 0 | Exposure compensation (-10 to 10) |
| `rpiCameraGain` | 0 | Manual gain (0 = auto) |
| `rpiCameraDenoise` | off | Denoise mode (off, cdn_off, cdn_fast, cdn_hq, auto) |
| `rpiCameraShutter` | 0 | Shutter speed in µs (0 = auto) |

## Night Mode

The control API (`camera_control.py`) switches between day and night presets:

### Day Mode (default)
```yaml
rpiCameraFPS: 30
rpiCameraExposure: normal
rpiCameraEV: 0
rpiCameraGain: 0
rpiCameraDenoise: off
```

### Night Mode
```yaml
rpiCameraFPS: 15          # Lower FPS for longer exposure
rpiCameraExposure: long   # Allow longer exposures
rpiCameraEV: 2            # Boost exposure
rpiCameraGain: 8          # Higher gain for low light
rpiCameraDenoise: auto    # Enable denoise
```

When switching modes, the API:
1. Writes a new `mediamtx.yml` with updated settings
2. Restarts the `baby-monitor` systemd service
3. Stream reconnects automatically (~3 seconds interruption)

## Protocol Support

| Protocol | Port | Latency | Use Case |
|----------|------|---------|----------|
| WebRTC | 8889 | ~500ms | Primary - modern browsers |
| HLS | 8888 | ~3-5s | Fallback - all browsers |
| RTSP | 8554 | ~1s | VLC, other players |

### Accessing the Stream

**WebRTC (recommended):**
```
http://192.168.1.14:8889/baby-monitor/
```

**HLS:**
```
http://192.168.1.14:8888/baby-monitor/
```

**RTSP (VLC):**
```
rtsp://192.168.1.14:8554/baby-monitor
```

## Bandwidth Requirements

| Resolution | FPS | Bitrate | Bandwidth |
|------------|-----|---------|-----------|
| 640x480 | 30 | 1 Mbps | ~125 KB/s |
| 1280x720 | 30 | 2 Mbps | ~250 KB/s |
| 1920x1080 | 30 | 4 Mbps | ~500 KB/s |

## Latency Optimization

For lowest latency:
1. Use WebRTC (not HLS)
2. Reduce resolution if needed
3. Use wired ethernet if possible (WiFi adds ~10-20ms)

## Troubleshooting

### Service Status
```bash
# Check service status
sudo systemctl status baby-monitor

# View live logs
sudo journalctl -u baby-monitor -f

# Restart service
sudo systemctl restart baby-monitor
```

### No video
```bash
# Check camera is detected
rpicam-hello --list-cameras

# Test camera directly
rpicam-hello -t 5000

# Check MediaMTX logs
journalctl -u baby-monitor -n 50
```

### High latency
- Ensure browser is using WebRTC (check console)
- Reduce resolution in config
- Check WiFi signal strength

### Choppy video
- Reduce framerate to 15
- Reduce resolution
- Check Pi CPU usage: `htop`

### API not responding
```bash
# Check API service
sudo systemctl status baby-monitor-api

# View API logs
journalctl -u baby-monitor-api -f
```
