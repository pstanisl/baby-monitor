# Audio Monitoring (Planned)

Integration with ReSpeaker 2-Mics Pi HAT for audio monitoring.

## Hardware

### ReSpeaker 2-Mics Pi HAT

- **Microphones:** 2x digital MEMS microphones
- **Audio Codec:** WM8960
- **Interface:** I2S
- **LEDs:** 3x APA102 RGB LEDs (can be used for status)
- **Button:** 1x user button

## Installation

### Step 1: Physical Connection

1. Power off the Raspberry Pi
2. Align the ReSpeaker HAT with the GPIO header
3. Press down firmly until seated
4. Power on the Pi

### Step 2: Software Setup

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y git

# Clone the seeed-voicecard repository
cd ~
git clone https://github.com/respeaker/seeed-voicecard.git
cd seeed-voicecard

# Install the driver
sudo ./install.sh

# Reboot
sudo reboot
```

### Step 3: Verify Installation

```bash
# Check sound cards
arecord -l

# Expected output:
# card 1: seeed2micvoicec [seeed-2mic-voicecard], device 0: bcm2835-i2s-wm8960-hifi wm8960-hifi-0 [bcm2835-i2s-wm8960-hifi wm8960-hifi-0]
```

## Audio Streaming Integration

### Option 1: Combine with Video in MediaMTX

```bash
# Capture audio and video together
ffmpeg \
    -f v4l2 -input_format h264 -i /dev/video0 \
    -f alsa -i plughw:1,0 \
    -c:v copy \
    -c:a aac -b:a 128k \
    -f rtsp rtsp://localhost:8554/baby-monitor
```

### Option 2: Separate Audio Stream

```bash
# Audio-only stream
ffmpeg \
    -f alsa -i plughw:1,0 \
    -c:a aac -b:a 64k \
    -f rtsp rtsp://localhost:8554/baby-audio
```

### Option 3: WebRTC with Audio (Preferred)

MediaMTX configuration with audio:

```yaml
paths:
  baby-monitor:
    source: publisher
    # Audio will be handled by a combined rpicam-vid + ffmpeg pipeline
```

## Web Interface Changes

The web interface will be updated to include:

- [ ] Audio toggle (mute/unmute)
- [ ] Volume slider
- [ ] Audio level indicator
- [ ] Push-to-talk (future: talk to baby)

```html
<!-- Audio controls to add -->
<div class="audio-controls">
    <button id="mute-toggle">🔊</button>
    <input type="range" id="volume" min="0" max="100" value="80">
    <div id="audio-level"></div>
</div>
```

## Cry Detection (Advanced)

Future enhancement: detect baby crying and send alerts.

### Using TensorFlow Lite

```python
import tflite_runtime.interpreter as tflite
import numpy as np

# Load pre-trained cry detection model
interpreter = tflite.Interpreter(model_path="cry_detector.tflite")
interpreter.allocate_tensors()

def detect_cry(audio_chunk):
    """Analyze audio for baby crying."""
    # Preprocess audio
    features = extract_features(audio_chunk)

    # Run inference
    interpreter.set_tensor(input_index, features)
    interpreter.invoke()
    output = interpreter.get_tensor(output_index)

    return output[0] > 0.8  # 80% confidence threshold
```

### Using Simple Volume Threshold

```python
import numpy as np

def detect_loud_noise(audio_data, threshold=0.7):
    """Simple volume-based detection."""
    rms = np.sqrt(np.mean(np.square(audio_data)))
    return rms > threshold
```

## LED Status Indicators

The ReSpeaker HAT has 3 APA102 LEDs that can show status:

```python
from apa102 import APA102

leds = APA102(num_led=3)

# Status colors
def set_status(status):
    colors = {
        'streaming': (0, 255, 0),    # Green - all good
        'motion': (255, 255, 0),     # Yellow - motion detected
        'crying': (255, 0, 0),       # Red - baby crying
        'night': (0, 0, 50),         # Dim blue - night mode
    }
    r, g, b = colors.get(status, (0, 0, 0))
    for i in range(3):
        leds.set_pixel(i, r, g, b)
    leds.show()
```

## Resource Impact

| Feature | CPU Impact | RAM Impact |
|---------|------------|------------|
| Audio capture | +5% | +20MB |
| Audio streaming | +10% | +30MB |
| Cry detection | +25% | +100MB |

## Dependencies

```bash
# Audio tools
sudo apt-get install -y alsa-utils ffmpeg

# Python audio libraries
pip3 install pyaudio numpy

# For LED control
pip3 install apa102-pi

# For cry detection (optional)
pip3 install tflite-runtime
```

## Files to Create

```
pi/
├── scripts/
│   ├── audio_stream.py
│   └── cry_detector.py
├── config/
│   └── audio.yml
└── models/
    └── cry_detector.tflite  # Pre-trained model
```

## Timeline

This feature is planned for Phase 2a:

1. [ ] Connect ReSpeaker HAT
2. [ ] Install drivers
3. [ ] Add audio to video stream
4. [ ] Update web interface
5. [ ] (Optional) Add cry detection
