#!/usr/bin/env python3
"""
Camera Control API for Baby Monitor

Provides HTTP endpoints to control camera settings like night mode.
Modifies MediaMTX configuration and restarts the service.
"""

import subprocess
import json
import os
import shutil
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PORT = 5000
CONFIG_FILE = '/home/pi/baby-monitor/config/mediamtx.yml'
MEDIAMTX_SERVICE = 'baby-monitor'

# Camera presets for MediaMTX rpiCamera
CAMERA_PRESETS = {
    'day': {
        'rpiCameraWidth': 1280,
        'rpiCameraHeight': 720,
        'rpiCameraFPS': 30,
        'rpiCameraBitrate': 2000000,
        'rpiCameraExposure': 'normal',
        'rpiCameraAWB': 'auto',
        'rpiCameraAfMode': 'continuous',
        'rpiCameraEV': 0,
        'rpiCameraGain': 0,
        'rpiCameraDenoise': 'off',
    },
    'night': {
        'rpiCameraWidth': 1280,
        'rpiCameraHeight': 720,
        'rpiCameraFPS': 15,  # Lower FPS for longer exposure
        'rpiCameraBitrate': 2000000,
        'rpiCameraExposure': 'long',
        'rpiCameraAWB': 'auto',
        'rpiCameraAfMode': 'continuous',
        'rpiCameraEV': 2,  # Exposure compensation
        'rpiCameraGain': 8,  # Higher gain for low light
        'rpiCameraDenoise': 'cdn_hq',  # High quality denoise for low-light
    }
}

# Current state
current_mode = 'day'


def generate_mediamtx_config(preset_name):
    """Generate MediaMTX configuration for given preset."""
    preset = CAMERA_PRESETS.get(preset_name, CAMERA_PRESETS['day'])

    config = f'''# MediaMTX Configuration for Baby Monitor
# Auto-generated - Mode: {preset_name}

logLevel: info
logDestinations: [stdout]

api: yes
apiAddress: :9997

playback: no

rtsp: yes
rtspAddress: :8554

rtmp: no

hls: yes
hlsAddress: :8888
hlsAlwaysRemux: no

webrtc: yes
webrtcAddress: :8889
webrtcEncryption: no
webrtcICEServers2: []
webrtcLocalUDPAddress: :8189

srt: no

paths:
  baby-monitor:
    source: rpiCamera
    rpiCameraWidth: {preset['rpiCameraWidth']}
    rpiCameraHeight: {preset['rpiCameraHeight']}
    rpiCameraFPS: {preset['rpiCameraFPS']}
    rpiCameraCodec: auto
    rpiCameraBitrate: {preset['rpiCameraBitrate']}
    rpiCameraProfile: baseline
    rpiCameraLevel: "4.1"
    rpiCameraExposure: "{preset.get('rpiCameraExposure', 'normal')}"
    rpiCameraAWB: "{preset['rpiCameraAWB']}"
    rpiCameraAfMode: "{preset['rpiCameraAfMode']}"
    rpiCameraEV: {preset.get('rpiCameraEV', 0)}
    rpiCameraGain: {preset.get('rpiCameraGain', 0)}
    rpiCameraDenoise: "{preset.get('rpiCameraDenoise', 'off')}"
    record: false
'''
    return config


def write_config(preset_name):
    """Write MediaMTX configuration file."""
    try:
        config_content = generate_mediamtx_config(preset_name)

        # Backup existing config
        if os.path.exists(CONFIG_FILE):
            shutil.copy(CONFIG_FILE, f'{CONFIG_FILE}.bak')

        # Write new config
        with open(CONFIG_FILE, 'w') as f:
            f.write(config_content)

        logger.info(f'Wrote config for {preset_name} mode')
        return True
    except Exception as e:
        logger.error(f'Failed to write config: {e}')
        return False


def restart_mediamtx():
    """Restart MediaMTX service."""
    try:
        subprocess.run(
            ['sudo', 'systemctl', 'restart', MEDIAMTX_SERVICE],
            check=True,
            capture_output=True
        )
        logger.info('MediaMTX service restarted')
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f'Failed to restart MediaMTX: {e.stderr.decode()}')
        return False


class CameraControlHandler(BaseHTTPRequestHandler):
    """HTTP request handler for camera control API."""

    def send_json_response(self, data, status=200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        global current_mode

        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/api/status':
            self.send_json_response({
                'status': 'ok',
                'mode': current_mode,
                'night_mode': current_mode == 'night'
            })

        elif path == '/api/night-mode':
            self.send_json_response({
                'enabled': current_mode == 'night'
            })

        elif path == '/':
            # Redirect to web interface
            host = self.headers.get('Host', 'localhost:5000')
            new_host = host.replace(':5000', ':8889')
            self.send_response(301)
            self.send_header('Location', f'http://{new_host}/baby-monitor/')
            self.end_headers()

        else:
            self.send_json_response({'error': 'Not found'}, 404)

    def do_POST(self):
        """Handle POST requests."""
        global current_mode

        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/api/night-mode':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode()
                data = json.loads(body) if body else {}

                enabled = data.get('enabled', False)
                new_mode = 'night' if enabled else 'day'

                if new_mode != current_mode:
                    logger.info(f'Switching to {new_mode} mode')

                    if write_config(new_mode):
                        if restart_mediamtx():
                            current_mode = new_mode
                            self.send_json_response({
                                'success': True,
                                'enabled': enabled,
                                'mode': current_mode
                            })
                        else:
                            self.send_json_response({
                                'success': False,
                                'error': 'Failed to restart MediaMTX'
                            }, 500)
                    else:
                        self.send_json_response({
                            'success': False,
                            'error': 'Failed to write config'
                        }, 500)
                else:
                    self.send_json_response({
                        'success': True,
                        'enabled': enabled,
                        'mode': current_mode,
                        'message': 'No change needed'
                    })

            except json.JSONDecodeError:
                self.send_json_response({'error': 'Invalid JSON'}, 400)
            except Exception as e:
                logger.error(f'Error handling night-mode request: {e}')
                self.send_json_response({'error': str(e)}, 500)

        else:
            self.send_json_response({'error': 'Not found'}, 404)

    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info(f'{self.address_string()} - {format % args}')


def main():
    """Start the camera control API server."""
    server = HTTPServer(('0.0.0.0', PORT), CameraControlHandler)
    logger.info(f'Camera Control API listening on port {PORT}')
    logger.info('Endpoints:')
    logger.info('  GET  /api/status     - Get current status')
    logger.info('  GET  /api/night-mode - Get night mode state')
    logger.info('  POST /api/night-mode - Set night mode (body: {"enabled": true/false})')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info('Shutting down...')
        server.shutdown()


if __name__ == '__main__':
    main()
