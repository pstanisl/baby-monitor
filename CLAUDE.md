# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Baby monitor system for Raspberry Pi Zero 2 W with Camera Module 3. Code is developed locally and deployed to the Pi via SSH.

## Key Commands

```bash
# Deploy to Raspberry Pi (main workflow)
./scripts/deploy.sh

# Check service status on Pi
ssh raspberrypi-zero "sudo systemctl status baby-monitor"

# View logs
ssh raspberrypi-zero "sudo journalctl -u baby-monitor -f"

# Restart services
ssh raspberrypi-zero "sudo systemctl restart baby-monitor baby-monitor-api"

# Test night mode API
curl -X POST http://192.168.1.14:5000/api/night-mode \
  -H "Content-Type: application/json" -d '{"enabled": true}'
```

## Architecture

- **MediaMTX** (`pi/config/mediamtx.yml`): Handles camera capture and streaming via native `rpiCamera` source. Serves WebRTC (port 8889), HLS (8888), and RTSP (8554).

- **Camera Control API** (`pi/scripts/camera_control.py`): Python HTTP server (port 5000) that manages night mode by regenerating `mediamtx.yml` and restarting the MediaMTX service.

- **Web Interface** (`pi/web/index.html`): Single-page app using WebRTC to display stream, with night mode toggle that calls the control API.

- **Deployment** (`scripts/deploy.sh`): Rsync files to Pi, install/update systemd services, restart.

## MediaMTX Configuration Notes

When modifying `mediamtx.yml` or the generated config in `camera_control.py`:
- Use `rpiCameraCodec: auto` (not `h264`)
- String values need quotes: `rpiCameraExposure: "normal"`, `rpiCameraDenoise: "off"`
- Boolean values: use `false` not `no` for path settings
- Valid denoise values: `off`, `cdn_off`, `cdn_fast`, `cdn_hq` (not `auto`)

## Target Environment

- Pi hostname: `raspberrypi-zero` (accessible via SSH)
- Pi IP: `192.168.1.14`
- OS: Debian Trixie (aarch64)
- MediaMTX version: v1.9.3
