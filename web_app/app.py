#!/usr/bin/env python3
"""
ReSpeaker XVF3800 Web Control Dashboard v2
Enhanced real-time visualization and control interface
"""

from flask import Flask, render_template, jsonify, request
import usb.core
import usb.util
import usb.backend.libusb1
import struct
import math
import time
from threading import Lock
from collections import deque

app = Flask(__name__)
device_lock = Lock()

# Set up libusb backend for macOS
usb_backend = usb.backend.libusb1.get_backend(
    find_library=lambda x: "/opt/homebrew/lib/libusb-1.0.dylib"
)

# History storage for beam energies (last 50 samples per beam)
beam_history = {i: deque(maxlen=50) for i in range(4)}

class ReSpeaker:
    """ReSpeaker XVF3800 USB control interface"""

    TIMEOUT = 100000
    VID = 0x2886
    PID = 0x001A

    # Parameter definitions (resid, cmdid, length, data_type)
    PARAMS = {
        'VERSION': (48, 0, 3, 'uint8'),
        'DOA_VALUE': (20, 18, 4, 'mixed'),
        'AEC_AZIMUTH_VALUES': (33, 75, 16, 'float'),
        'AEC_SPENERGY_VALUES': (33, 76, 16, 'float'),
        'LED_EFFECT': (20, 12, 1, 'uint8'),
        'LED_BRIGHTNESS': (20, 13, 1, 'uint8'),
        'LED_COLOR': (20, 16, 4, 'uint32'),
        'LED_SPEED': (20, 15, 1, 'uint8'),
        'GPI_READ_VALUES': (36, 0, 3, 'uint8'),
        'GPO_READ_VALUES': (20, 0, 5, 'uint8'),
        'AUDIO_MGR_MIC_GAIN': (35, 0, 4, 'float'),
        'PP_AGCMAXGAIN': (17, 10, 4, 'float'),
        'PP_AGCGAIN': (17, 13, 4, 'float'),
        'PP_MIN_NS': (17, 21, 4, 'float'),
        'PP_MIN_NN': (17, 22, 4, 'float'),
        'PP_AGCONOFF': (17, 9, 4, 'int32'),
        'PP_ECHOONOFF': (17, 23, 4, 'int32'),
    }

    def __init__(self):
        self.dev = usb.core.find(idVendor=self.VID, idProduct=self.PID, backend=usb_backend)
        if self.dev is None:
            raise RuntimeError("ReSpeaker not found")

    def read(self, param_name):
        """Read a parameter from the device"""
        if param_name not in self.PARAMS:
            raise ValueError(f"Unknown parameter: {param_name}")

        resid, cmdid, length, _ = self.PARAMS[param_name]

        result = self.dev.ctrl_transfer(
            usb.util.CTRL_IN | usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_DEVICE,
            0, 0x80 | cmdid, resid, length + 1, self.TIMEOUT
        )
        return result

    def write(self, param_name, data):
        """Write a parameter to the device"""
        if param_name not in self.PARAMS:
            raise ValueError(f"Unknown parameter: {param_name}")

        resid, cmdid, _, _ = self.PARAMS[param_name]

        self.dev.ctrl_transfer(
            usb.util.CTRL_OUT | usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_DEVICE,
            0, cmdid, resid, data, self.TIMEOUT
        )

# Global device instance
respeaker = None

def get_device():
    """Get or initialize ReSpeaker device"""
    global respeaker
    if respeaker is None:
        respeaker = ReSpeaker()
    return respeaker

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get complete device status"""
    try:
        with device_lock:
            dev = get_device()

            # Read DoA
            doa_result = dev.read('DOA_VALUE')
            doa_angle = struct.unpack_from('<H', doa_result, 1)[0]
            speech_detected = bool(doa_result[3])

            # Read azimuth values (4 beams in radians)
            azimuth_result = dev.read('AEC_AZIMUTH_VALUES')
            azimuths = struct.unpack_from('<4f', azimuth_result, 1)
            azimuths_deg = [math.degrees(a) % 360 for a in azimuths]

            # Read speech energy (4 beams)
            energy_result = dev.read('AEC_SPENERGY_VALUES')
            energies = struct.unpack_from('<4f', energy_result, 1)

            # Store energy history
            for i, energy in enumerate(energies):
                beam_history[i].append(energy)

            # Read GPIO
            gpi_result = dev.read('GPI_READ_VALUES')
            gpi_values = list(gpi_result[1:4])

            gpo_result = dev.read('GPO_READ_VALUES')
            gpo_values = list(gpo_result[1:6])

            # Read audio settings
            mic_gain_result = dev.read('AUDIO_MGR_MIC_GAIN')
            mic_gain = struct.unpack_from('<f', mic_gain_result, 1)[0]

            agc_max_result = dev.read('PP_AGCMAXGAIN')
            agc_max = struct.unpack_from('<f', agc_max_result, 1)[0]

            agc_current_result = dev.read('PP_AGCGAIN')
            agc_current = struct.unpack_from('<f', agc_current_result, 1)[0]

            noise_suppress_result = dev.read('PP_MIN_NS')
            noise_suppress = struct.unpack_from('<f', noise_suppress_result, 1)[0]

            noise_nonstat_result = dev.read('PP_MIN_NN')
            noise_nonstat = struct.unpack_from('<f', noise_nonstat_result, 1)[0]

            agc_enabled_result = dev.read('PP_AGCONOFF')
            agc_enabled = bool(struct.unpack_from('<i', agc_enabled_result, 1)[0])

            echo_enabled_result = dev.read('PP_ECHOONOFF')
            echo_enabled = bool(struct.unpack_from('<i', echo_enabled_result, 1)[0])

            return jsonify({
                'success': True,
                'doa': {
                    'angle': doa_angle,
                    'speech_detected': speech_detected
                },
                'beams': {
                    'azimuths': azimuths_deg,
                    'energies': list(energies),
                    'history': {i: list(beam_history[i]) for i in range(4)},
                    'labels': ['Beam 1 (Fixed)', 'Beam 2 (Fixed)', 'Free-Running', 'Auto-Select']
                },
                'gpio': {
                    'inputs': {
                        'mute_button': bool(gpi_values[0]),
                        'pin_13': bool(gpi_values[1]),
                        'pin_34': bool(gpi_values[2])
                    },
                    'outputs': {
                        'pin_11': bool(gpo_values[0]),
                        'mute_led': bool(gpo_values[1]),
                        'amp_enable': not bool(gpo_values[2]),  # Active low
                        'led_power': bool(gpo_values[3]),
                        'pin_39': bool(gpo_values[4])
                    }
                },
                'audio': {
                    'mic_gain': round(mic_gain, 2),
                    'agc_max': round(agc_max, 2),
                    'agc_current': round(agc_current, 2),
                    'agc_enabled': agc_enabled,
                    'noise_suppress_stationary': round(noise_suppress, 3),
                    'noise_suppress_nonstationary': round(noise_nonstat, 3),
                    'echo_suppression': echo_enabled
                }
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/led/effect', methods=['POST'])
def set_led_effect():
    """Set LED effect (0=off, 1=breath, 2=rainbow, 3=solid, 4=doa)"""
    try:
        effect = int(request.json.get('effect', 2))
        with device_lock:
            dev = get_device()
            dev.write('LED_EFFECT', [effect])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/led/brightness', methods=['POST'])
def set_led_brightness():
    """Set LED brightness (0-255)"""
    try:
        brightness = int(request.json.get('brightness', 128))
        with device_lock:
            dev = get_device()
            dev.write('LED_BRIGHTNESS', [brightness])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/led/color', methods=['POST'])
def set_led_color():
    """Set LED color (RGB) with brightness applied"""
    try:
        r = int(request.json.get('r', 255))
        g = int(request.json.get('g', 0))
        b = int(request.json.get('b', 255))
        brightness = float(request.json.get('brightness', 1.0))  # 0.0-1.0

        # Apply brightness to color values
        r = int(r * brightness)
        g = int(g * brightness)
        b = int(b * brightness)

        # Try different byte orders - WS2812 typically uses GRB
        # Pack as bytes: [G, R, B, 0]
        color_bytes = [g, r, b, 0]

        with device_lock:
            dev = get_device()
            dev.write('LED_COLOR', color_bytes)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/led/speed', methods=['POST'])
def set_led_speed():
    """Set LED animation speed"""
    try:
        speed = int(request.json.get('speed', 1))
        with device_lock:
            dev = get_device()
            dev.write('LED_SPEED', [speed])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/mic_gain', methods=['POST'])
def set_mic_gain():
    """Set microphone gain"""
    try:
        gain = float(request.json.get('gain', 90.0))
        with device_lock:
            dev = get_device()
            dev.write('AUDIO_MGR_MIC_GAIN', struct.pack('<f', gain))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/agc_max', methods=['POST'])
def set_agc_max():
    """Set AGC maximum gain"""
    try:
        gain = float(request.json.get('gain', 64.0))
        with device_lock:
            dev = get_device()
            dev.write('PP_AGCMAXGAIN', struct.pack('<f', gain))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/noise_suppress', methods=['POST'])
def set_noise_suppress():
    """Set noise suppression level (0.0-1.0)"""
    try:
        level = float(request.json.get('level', 0.0))
        with device_lock:
            dev = get_device()
            dev.write('PP_MIN_NS', struct.pack('<f', level))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/led/test_color', methods=['POST'])
def test_led_color():
    """Test different byte orders for LED color calibration"""
    try:
        r = int(request.json.get('r', 255))
        g = int(request.json.get('g', 0))
        b = int(request.json.get('b', 0))
        order = request.json.get('order', 'GRB')  # RGB, GRB, BGR, RBG, BRG, GBR

        # Map byte order
        orders = {
            'RGB': [r, g, b, 0],
            'GRB': [g, r, b, 0],
            'BGR': [b, g, r, 0],
            'RBG': [r, b, g, 0],
            'BRG': [b, r, g, 0],
            'GBR': [g, b, r, 0]
        }

        color_bytes = orders.get(order, [g, r, b, 0])

        with device_lock:
            dev = get_device()
            dev.write('LED_COLOR', color_bytes)

        return jsonify({'success': True, 'order_used': order, 'bytes': color_bytes})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting ReSpeaker Control Dashboard v2...")
    print("Open http://localhost:5001 in your browser")
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
