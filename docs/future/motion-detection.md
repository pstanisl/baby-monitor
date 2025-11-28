# Motion Detection (Planned)

Future implementation for motion detection alerts.

## Overview

Motion detection will notify you when your baby moves or wakes up.

## Planned Implementation

### Option 1: Software-based (Python + OpenCV)

```python
# Conceptual implementation
import cv2
import numpy as np

def detect_motion(frame1, frame2, threshold=25):
    """Compare two frames and detect significant changes."""
    diff = cv2.absdiff(frame1, frame2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, threshold, 255, cv2.THRESH_BINARY)

    # Count changed pixels
    changed = np.sum(thresh > 0)
    total = thresh.shape[0] * thresh.shape[1]

    return (changed / total) > 0.01  # 1% threshold
```

**Pros:**
- Full control over sensitivity
- Can define regions of interest (crib area only)
- Integrates with notification systems

**Cons:**
- Additional CPU usage on Pi Zero
- Requires OpenCV installation

### Option 2: MediaMTX + Motion Webhooks

MediaMTX can be configured to detect motion and trigger webhooks:

```yaml
paths:
  baby-monitor:
    runOnDemand: python3 /home/pi/baby-monitor/scripts/motion_detector.py
```

### Option 3: Separate Motion Service

Run a dedicated motion detection service:

```bash
# motion-detector.service
[Service]
ExecStart=/home/pi/baby-monitor/scripts/motion_detector.py
```

## Notification Options

### 1. Push Notifications (ntfy.sh)

Free, self-hostable push notifications:

```python
import requests

def send_alert(message):
    requests.post(
        "https://ntfy.sh/your-baby-monitor",
        data=message.encode('utf-8')
    )
```

### 2. Home Assistant Integration

```yaml
# configuration.yaml
rest_command:
  baby_motion:
    url: "http://192.168.1.14:8889/api/motion"
    method: GET
```

### 3. Email Alerts

```python
import smtplib
from email.message import EmailMessage

def send_email_alert():
    msg = EmailMessage()
    msg['Subject'] = 'Baby Monitor: Motion Detected'
    msg['From'] = 'monitor@home'
    msg['To'] = 'parent@email.com'
    msg.set_content('Motion detected in baby room!')

    with smtplib.SMTP('smtp.gmail.com', 587) as s:
        s.starttls()
        s.login('user', 'password')
        s.send_message(msg)
```

## Configuration UI

The web interface will include:

- [ ] Motion detection toggle
- [ ] Sensitivity slider (low/medium/high)
- [ ] Region of interest selection
- [ ] Quiet hours setting
- [ ] Notification preferences

## Resource Considerations

The Pi Zero 2 W has limited resources:

| Component | Without Motion | With Motion |
|-----------|---------------|-------------|
| CPU | ~30% | ~60% |
| RAM | ~150MB | ~250MB |

Consider:
- Running detection at lower FPS (5 fps vs 30 fps)
- Using grayscale only for detection
- Downscaling frames before analysis

## Files to Create

```
pi/
├── scripts/
│   └── motion_detector.py
├── config/
│   └── motion.yml
└── web/
    └── motion-settings.html
```

## Dependencies

```bash
# Will need to install
sudo apt-get install python3-opencv python3-numpy
pip3 install requests  # for notifications
```

## Timeline

This feature is planned for Phase 2, after:
- [x] Basic streaming works
- [x] Night mode implemented
- [ ] Audio monitoring (Phase 2a)
- [ ] Motion detection (Phase 2b)
