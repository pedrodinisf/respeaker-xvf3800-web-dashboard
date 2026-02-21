#!/usr/bin/env python3
"""
ReSpeaker XVF3800 Web Control Dashboard v2
Enhanced real-time visualization and control interface
"""

from flask import Flask, render_template, jsonify, request, send_file
import usb.core
import usb.util
import usb.backend.libusb1
import struct
import math
import time
import os
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write as write_wav
from datetime import datetime
from threading import Lock, Thread
from collections import deque

app = Flask(__name__)
device_lock = Lock()

# Set up libusb backend for macOS
usb_backend = usb.backend.libusb1.get_backend(
    find_library=lambda x: "/opt/homebrew/lib/libusb-1.0.dylib"
)

# History storage for beam energies (last 50 samples per beam)
beam_history = {i: deque(maxlen=50) for i in range(4)}

# Recording state
recording_state = {
    'is_recording': False,
    'data': [],
    'start_time': None,
    'sample_rate': 16000,  # ReSpeaker native sample rate
    'channels': 2,         # Stereo (processed output)
}
recording_lock = Lock()

# Create recordings directory
RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), 'recordings')
os.makedirs(RECORDINGS_DIR, exist_ok=True)

class ReSpeaker:
    """ReSpeaker XVF3800 USB control interface"""

    TIMEOUT = 100000
    VID = 0x2886
    PID = 0x001A

    # Parameter definitions (resid, cmdid, length, data_type)
    # Based on official xvf_host.py PARAMETERS dictionary
    PARAMS = {
        # Read-only status
        'VERSION': (48, 0, 3, 'uint8'),
        'DOA_VALUE': (20, 18, 4, 'mixed'),
        'AEC_AZIMUTH_VALUES': (33, 75, 16, 'float'),
        'AEC_SPENERGY_VALUES': (33, 76, 16, 'float'),
        'GPI_READ_VALUES': (36, 0, 3, 'uint8'),
        'GPO_READ_VALUES': (20, 0, 5, 'uint8'),
        'PP_AGCGAIN': (17, 13, 4, 'float'),  # Current AGC gain (read-only)

        # LED Control (resid=20)
        'LED_EFFECT': (20, 12, 1, 'uint8'),        # Range: 0-5
        'LED_BRIGHTNESS': (20, 13, 1, 'uint8'),    # Range: 0-255
        'LED_COLOR': (20, 16, 4, 'uint32'),
        'LED_SPEED': (20, 15, 1, 'uint8'),

        # Audio Manager (resid=35)
        'AUDIO_MGR_MIC_GAIN': (35, 0, 4, 'float'),      # Pre-SHF mic gain
        'AUDIO_MGR_REF_GAIN': (35, 1, 4, 'float'),      # Pre-SHF reference gain
        'AUDIO_MGR_SYS_DELAY': (35, 26, 4, 'int32'),    # System delay in samples

        # Post-Processing AGC (resid=17)
        'PP_AGCONOFF': (17, 10, 4, 'int32'),            # Range: 0,1
        'PP_AGCMAXGAIN': (17, 11, 4, 'float'),          # Range: [1.0 .. 1000.0]
        'PP_AGCDESIREDLEVEL': (17, 12, 4, 'float'),     # Range: [1e-8 .. 1.0]
        'PP_AGCTIME': (17, 14, 4, 'float'),             # Range: [0.5 .. 4.0] seconds
        'PP_AGCFASTTIME': (17, 15, 4, 'float'),         # Range: [0.05 .. 4.0] seconds

        # Post-Processing Limiter (resid=17)
        'PP_LIMITONOFF': (17, 19, 4, 'int32'),          # Range: 0,1
        'PP_LIMITPLIMIT': (17, 20, 4, 'float'),         # Range: [1e-8 .. 1.0]

        # Post-Processing Noise Suppression (resid=17)
        'PP_MIN_NS': (17, 21, 4, 'float'),              # Range: [0.0 .. 1.0]
        'PP_MIN_NN': (17, 22, 4, 'float'),              # Range: [0.0 .. 1.0]

        # Post-Processing Echo Suppression (resid=17)
        'PP_ECHOONOFF': (17, 23, 4, 'int32'),           # Range: 0,1
        'PP_GAMMA_E': (17, 24, 4, 'float'),             # Range: [0.0 .. 2.0]
        'PP_GAMMA_ETAIL': (17, 25, 4, 'float'),         # Range: [0.0 .. 2.0]
        'PP_GAMMA_ENL': (17, 26, 4, 'float'),           # Range: [0.0 .. 5.0]
        'PP_NLATTENONOFF': (17, 27, 4, 'int32'),        # Range: 0,1
        'PP_DTSENSITIVE': (17, 31, 4, 'int32'),         # Range: [0..5, 10..15]

        # AEC Settings (resid=33)
        'AEC_HPFONOFF': (33, 1, 4, 'int32'),            # Range: 0,1,2,3,4
        'AEC_ASROUTONOFF': (33, 35, 4, 'int32'),        # Range: 0,1
        'AEC_ASROUTGAIN': (33, 36, 4, 'float'),         # Range: [0.0 .. 1000.0]
        'AEC_FIXEDBEAMSONOFF': (33, 37, 4, 'int32'),    # Range: 0,1
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

            # Read Audio Manager settings
            mic_gain = struct.unpack_from('<f', dev.read('AUDIO_MGR_MIC_GAIN'), 1)[0]
            ref_gain = struct.unpack_from('<f', dev.read('AUDIO_MGR_REF_GAIN'), 1)[0]
            sys_delay = struct.unpack_from('<i', dev.read('AUDIO_MGR_SYS_DELAY'), 1)[0]

            # Read AGC settings
            agc_enabled = bool(struct.unpack_from('<i', dev.read('PP_AGCONOFF'), 1)[0])
            agc_max = struct.unpack_from('<f', dev.read('PP_AGCMAXGAIN'), 1)[0]
            agc_current = struct.unpack_from('<f', dev.read('PP_AGCGAIN'), 1)[0]
            agc_desired = struct.unpack_from('<f', dev.read('PP_AGCDESIREDLEVEL'), 1)[0]
            agc_time = struct.unpack_from('<f', dev.read('PP_AGCTIME'), 1)[0]
            agc_fasttime = struct.unpack_from('<f', dev.read('PP_AGCFASTTIME'), 1)[0]

            # Read Limiter settings
            limiter_enabled = bool(struct.unpack_from('<i', dev.read('PP_LIMITONOFF'), 1)[0])
            limiter_limit = struct.unpack_from('<f', dev.read('PP_LIMITPLIMIT'), 1)[0]

            # Read Noise Suppression settings
            noise_suppress = struct.unpack_from('<f', dev.read('PP_MIN_NS'), 1)[0]
            noise_nonstat = struct.unpack_from('<f', dev.read('PP_MIN_NN'), 1)[0]

            # Read Echo Suppression settings
            echo_enabled = bool(struct.unpack_from('<i', dev.read('PP_ECHOONOFF'), 1)[0])
            gamma_e = struct.unpack_from('<f', dev.read('PP_GAMMA_E'), 1)[0]
            gamma_etail = struct.unpack_from('<f', dev.read('PP_GAMMA_ETAIL'), 1)[0]
            gamma_enl = struct.unpack_from('<f', dev.read('PP_GAMMA_ENL'), 1)[0]
            nlatten_enabled = bool(struct.unpack_from('<i', dev.read('PP_NLATTENONOFF'), 1)[0])
            dt_sensitive = struct.unpack_from('<i', dev.read('PP_DTSENSITIVE'), 1)[0]

            # Read AEC settings
            hpf_mode = struct.unpack_from('<i', dev.read('AEC_HPFONOFF'), 1)[0]
            asr_enabled = bool(struct.unpack_from('<i', dev.read('AEC_ASROUTONOFF'), 1)[0])
            asr_gain = struct.unpack_from('<f', dev.read('AEC_ASROUTGAIN'), 1)[0]
            fixed_beams_enabled = bool(struct.unpack_from('<i', dev.read('AEC_FIXEDBEAMSONOFF'), 1)[0])

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
                    # Audio Manager
                    'mic_gain': round(mic_gain, 2),
                    'ref_gain': round(ref_gain, 2),
                    'sys_delay': sys_delay,

                    # AGC
                    'agc_enabled': agc_enabled,
                    'agc_max': round(agc_max, 2),
                    'agc_current': round(agc_current, 2),
                    'agc_desired': round(agc_desired, 6),
                    'agc_time': round(agc_time, 2),
                    'agc_fasttime': round(agc_fasttime, 2),

                    # Limiter
                    'limiter_enabled': limiter_enabled,
                    'limiter_limit': round(limiter_limit, 6),

                    # Noise Suppression
                    'noise_suppress_stationary': round(noise_suppress, 3),
                    'noise_suppress_nonstationary': round(noise_nonstat, 3),

                    # Echo Suppression
                    'echo_enabled': echo_enabled,
                    'gamma_e': round(gamma_e, 2),
                    'gamma_etail': round(gamma_etail, 2),
                    'gamma_enl': round(gamma_enl, 2),
                    'nlatten_enabled': nlatten_enabled,
                    'dt_sensitive': dt_sensitive,

                    # AEC
                    'hpf_mode': hpf_mode,
                    'asr_enabled': asr_enabled,
                    'asr_gain': round(asr_gain, 2),
                    'fixed_beams_enabled': fixed_beams_enabled
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
    """Set noise suppression stationary level (0.0-1.0)"""
    try:
        level = float(request.json.get('level', 0.0))
        with device_lock:
            dev = get_device()
            dev.write('PP_MIN_NS', struct.pack('<f', level))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/ref_gain', methods=['POST'])
def set_ref_gain():
    """Set reference gain"""
    try:
        gain = float(request.json.get('gain', 8.0))
        with device_lock:
            dev = get_device()
            dev.write('AUDIO_MGR_REF_GAIN', struct.pack('<f', gain))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/sys_delay', methods=['POST'])
def set_sys_delay():
    """Set system delay in samples"""
    try:
        delay = int(request.json.get('delay', 12))
        with device_lock:
            dev = get_device()
            dev.write('AUDIO_MGR_SYS_DELAY', struct.pack('<i', delay))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/agc_desired_level', methods=['POST'])
def set_agc_desired_level():
    """Set AGC desired level (1e-8 to 1.0)"""
    try:
        level = float(request.json.get('level', 0.001))
        with device_lock:
            dev = get_device()
            dev.write('PP_AGCDESIREDLEVEL', struct.pack('<f', level))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/agc_time', methods=['POST'])
def set_agc_time():
    """Set AGC time constant (0.5 to 4.0 seconds)"""
    try:
        time_val = float(request.json.get('time', 2.0))
        with device_lock:
            dev = get_device()
            dev.write('PP_AGCTIME', struct.pack('<f', time_val))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/agc_fasttime', methods=['POST'])
def set_agc_fasttime():
    """Set AGC fast time constant (0.05 to 4.0 seconds)"""
    try:
        time_val = float(request.json.get('time', 0.5))
        with device_lock:
            dev = get_device()
            dev.write('PP_AGCFASTTIME', struct.pack('<f', time_val))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/limiter_enable', methods=['POST'])
def set_limiter_enable():
    """Enable/disable limiter (0 or 1)"""
    try:
        enabled = int(request.json.get('enabled', 0))
        with device_lock:
            dev = get_device()
            dev.write('PP_LIMITONOFF', struct.pack('<i', enabled))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/limiter_limit', methods=['POST'])
def set_limiter_limit():
    """Set limiter limit (1e-8 to 1.0)"""
    try:
        limit = float(request.json.get('limit', 0.1))
        with device_lock:
            dev = get_device()
            dev.write('PP_LIMITPLIMIT', struct.pack('<f', limit))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/gamma_e', methods=['POST'])
def set_gamma_e():
    """Set echo over-subtraction factor (0.0 to 2.0)"""
    try:
        gamma = float(request.json.get('gamma', 1.0))
        with device_lock:
            dev = get_device()
            dev.write('PP_GAMMA_E', struct.pack('<f', gamma))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/gamma_etail', methods=['POST'])
def set_gamma_etail():
    """Set echo tail over-subtraction factor (0.0 to 2.0)"""
    try:
        gamma = float(request.json.get('gamma', 1.0))
        with device_lock:
            dev = get_device()
            dev.write('PP_GAMMA_ETAIL', struct.pack('<f', gamma))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/gamma_enl', methods=['POST'])
def set_gamma_enl():
    """Set non-linear echo over-subtraction factor (0.0 to 5.0)"""
    try:
        gamma = float(request.json.get('gamma', 1.5))
        with device_lock:
            dev = get_device()
            dev.write('PP_GAMMA_ENL', struct.pack('<f', gamma))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/nlatten_enable', methods=['POST'])
def set_nlatten_enable():
    """Enable/disable non-linear attenuation (0 or 1)"""
    try:
        enabled = int(request.json.get('enabled', 1))
        with device_lock:
            dev = get_device()
            dev.write('PP_NLATTENONOFF', struct.pack('<i', enabled))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/dt_sensitive', methods=['POST'])
def set_dt_sensitive():
    """Set doubletalk sensitivity (0-5 or 10-15)"""
    try:
        sensitivity = int(request.json.get('sensitivity', 3))
        with device_lock:
            dev = get_device()
            dev.write('PP_DTSENSITIVE', struct.pack('<i', sensitivity))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/hpf_mode', methods=['POST'])
def set_hpf_mode():
    """Set high-pass filter mode (0-4)"""
    try:
        mode = int(request.json.get('mode', 0))
        with device_lock:
            dev = get_device()
            dev.write('AEC_HPFONOFF', struct.pack('<i', mode))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/asr_enable', methods=['POST'])
def set_asr_enable():
    """Enable/disable ASR output (0 or 1)"""
    try:
        enabled = int(request.json.get('enabled', 0))
        with device_lock:
            dev = get_device()
            dev.write('AEC_ASROUTONOFF', struct.pack('<i', enabled))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/asr_gain', methods=['POST'])
def set_asr_gain():
    """Set ASR output gain (0.0 to 1000.0)"""
    try:
        gain = float(request.json.get('gain', 1.0))
        with device_lock:
            dev = get_device()
            dev.write('AEC_ASROUTGAIN', struct.pack('<f', gain))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/fixed_beams_enable', methods=['POST'])
def set_fixed_beams_enable():
    """Enable/disable fixed beams mode (0 or 1)"""
    try:
        enabled = int(request.json.get('enabled', 0))
        with device_lock:
            dev = get_device()
            dev.write('AEC_FIXEDBEAMSONOFF', struct.pack('<i', enabled))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/agc_enable', methods=['POST'])
def set_agc_enable():
    """Enable/disable AGC (0 or 1)"""
    try:
        enabled = int(request.json.get('enabled', 1))
        with device_lock:
            dev = get_device()
            dev.write('PP_AGCONOFF', struct.pack('<i', enabled))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/echo_enable', methods=['POST'])
def set_echo_enable():
    """Enable/disable echo suppression (0 or 1)"""
    try:
        enabled = int(request.json.get('enabled', 1))
        with device_lock:
            dev = get_device()
            dev.write('PP_ECHOONOFF', struct.pack('<i', enabled))
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

# ============================================================================
# Audio Recording Endpoints
# ============================================================================

def find_respeaker_device():
    """Find the ReSpeaker audio device index"""
    devices = sd.query_devices()
    for idx, device in enumerate(devices):
        if 'respeaker' in device['name'].lower() or 'xvf3800' in device['name'].lower():
            if device['max_input_channels'] > 0:
                return idx
    return None

@app.route('/api/audio/devices')
def get_audio_devices():
    """List available audio devices"""
    try:
        devices = sd.query_devices()
        device_list = []
        for idx, device in enumerate(devices):
            device_list.append({
                'index': idx,
                'name': device['name'],
                'inputs': device['max_input_channels'],
                'outputs': device['max_output_channels'],
                'sample_rate': int(device['default_samplerate'])
            })

        respeaker_idx = find_respeaker_device()

        return jsonify({
            'success': True,
            'devices': device_list,
            'respeaker_index': respeaker_idx
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/record/start', methods=['POST'])
def start_recording():
    """Start audio recording from ReSpeaker"""
    global recording_state

    try:
        with recording_lock:
            if recording_state['is_recording']:
                return jsonify({'success': False, 'error': 'Already recording'}), 400

            # Find ReSpeaker device
            device_idx = find_respeaker_device()
            if device_idx is None:
                return jsonify({'success': False, 'error': 'ReSpeaker device not found'}), 404

            # Get device info
            device_info = sd.query_devices(device_idx)
            sample_rate = int(device_info['default_samplerate'])
            channels = min(2, device_info['max_input_channels'])  # Stereo or mono

            # Reset recording state
            recording_state['data'] = []
            recording_state['is_recording'] = True
            recording_state['start_time'] = datetime.now()
            recording_state['sample_rate'] = sample_rate
            recording_state['channels'] = channels

            # Start recording in background thread
            def record_audio():
                try:
                    with sd.InputStream(
                        device=device_idx,
                        channels=channels,
                        samplerate=sample_rate,
                        dtype='int16',
                        blocksize=4096
                    ) as stream:
                        while recording_state['is_recording']:
                            data, overflowed = stream.read(4096)
                            if overflowed:
                                print("Audio buffer overflow!")
                            recording_state['data'].append(data.copy())
                except Exception as e:
                    print(f"Recording error: {e}")
                    recording_state['is_recording'] = False

            Thread(target=record_audio, daemon=True).start()

            return jsonify({
                'success': True,
                'sample_rate': sample_rate,
                'channels': channels,
                'device': device_info['name']
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/record/stop', methods=['POST'])
def stop_recording():
    """Stop recording and save to WAV file"""
    global recording_state

    try:
        with recording_lock:
            if not recording_state['is_recording']:
                return jsonify({'success': False, 'error': 'Not recording'}), 400

            # Stop recording
            recording_state['is_recording'] = False
            time.sleep(0.2)  # Wait for last chunks

            # Combine all recorded chunks
            if not recording_state['data']:
                return jsonify({'success': False, 'error': 'No data recorded'}), 400

            audio_data = np.concatenate(recording_state['data'], axis=0)

            # Generate filename with timestamp
            timestamp = recording_state['start_time'].strftime('%Y%m%d_%H%M%S')
            filename = f"recording_{timestamp}.wav"
            filepath = os.path.join(RECORDINGS_DIR, filename)

            # Save as WAV (lossless)
            write_wav(filepath, recording_state['sample_rate'], audio_data)

            # Calculate duration and file size
            duration = len(audio_data) / recording_state['sample_rate']
            file_size = os.path.getsize(filepath)

            return jsonify({
                'success': True,
                'filename': filename,
                'duration': round(duration, 2),
                'file_size': file_size,
                'sample_rate': recording_state['sample_rate'],
                'channels': recording_state['channels']
            })
    except Exception as e:
        recording_state['is_recording'] = False
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/record/status')
def get_recording_status():
    """Get current recording status"""
    with recording_lock:
        if recording_state['is_recording']:
            duration = (datetime.now() - recording_state['start_time']).total_seconds()
            return jsonify({
                'success': True,
                'is_recording': True,
                'duration': round(duration, 1),
                'sample_rate': recording_state['sample_rate'],
                'channels': recording_state['channels']
            })
        else:
            return jsonify({
                'success': True,
                'is_recording': False
            })

@app.route('/api/audio/recordings')
def list_recordings():
    """List all saved recordings"""
    try:
        recordings = []
        for filename in os.listdir(RECORDINGS_DIR):
            if filename.endswith('.wav'):
                filepath = os.path.join(RECORDINGS_DIR, filename)
                stat = os.stat(filepath)
                recordings.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

        # Sort by creation time (newest first)
        recordings.sort(key=lambda x: x['created'], reverse=True)

        return jsonify({
            'success': True,
            'recordings': recordings
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/recordings/<filename>')
def get_recording(filename):
    """Download/play a recording file"""
    try:
        # Security: prevent directory traversal
        if '..' in filename or '/' in filename:
            return jsonify({'success': False, 'error': 'Invalid filename'}), 400

        filepath = os.path.join(RECORDINGS_DIR, filename)

        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'File not found'}), 404

        return send_file(filepath, mimetype='audio/wav')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audio/recordings/<filename>', methods=['DELETE'])
def delete_recording(filename):
    """Delete a recording file"""
    try:
        # Security: prevent directory traversal
        if '..' in filename or '/' in filename:
            return jsonify({'success': False, 'error': 'Invalid filename'}), 400

        filepath = os.path.join(RECORDINGS_DIR, filename)

        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'File not found'}), 404

        os.remove(filepath)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting ReSpeaker Control Dashboard v2...")
    print("Open http://localhost:5001 in your browser")
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
