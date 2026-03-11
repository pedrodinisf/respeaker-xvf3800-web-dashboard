# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project works with the **ReSpeaker XVF3800 USB 4-Mic Circular Array** — a professional voice capture device built on the XMOS XVF3800 processor with TLV320AIC3104 audio codec, 12x WS2812 RGB LEDs, and dual operation modes (USB and I2S).

## Hardware Reference

### Key Specs
- **Processor**: XMOS XVF3800
- **Audio Codec**: TLV320AIC3104 (I2C address `0x18`)
- **XVF3800 I2C address**: `0x2C`
- **Microphones**: 4-mic circular array, 360° far-field up to 5m
- **Audio capabilities**: AEC, AGC, DoA, beamforming, VAD, noise suppression, de-reverberation
- **LEDs**: 12x WS2812 addressable RGB (power controlled via GPIO X0D33)
- **Connectors**: USB-C, 3.5mm AUX, JST speaker (5W amplified)
- **I2S pins (ESP32S3)**: BCK=GPIO8, WS=GPIO7, TX=GPIO44, RX=GPIO43
- **I2C pins (ESP32S3)**: SDA=GPIO5, SCL=GPIO6

### GPIO Pin Map
| Pin | Direction | Function |
|-----|-----------|----------|
| X1D09 | Input | Mute button (high=released) |
| X1D13 | Input | Floating |
| X1D34 | Input | Floating |
| X0D11 | Output | Floating |
| X0D30 | Output | Mute LED + mic mute (high=mute) |
| X0D31 | Output | Amplifier enable (low=enabled) |
| X0D33 | Output | WS2812 LED power (high=on) |
| X0D39 | Output | Floating |

### USB-C Port Layout
The board has **two USB-C ports**:
- **XMOS USB-C** (near 3.5mm jack) — for USB audio mode, firmware flashing
- **XIAO ESP32S3 USB-C** (opposite side) — for programming ESP32 only

## Current Setup (Mac Mini)

The device is configured for **USB audio mode** and connected to a Mac Mini M4.

### Status
- **Firmware**: USB DFU v2.0.7 (2-channel processed audio)
- **Detection**: Appears as "reSpeaker XVF3800 4-Mic Array" (Seeed Studio)
- **Audio**: 16 kHz, 24-bit, 2-channel stereo, USB Audio Class 2.0
- **Default device**: Set as default input in macOS
- **LED behavior**: Rainbow on boot → DoA mode after 2 seconds

### Verification Commands
```bash
# Check audio device detection
system_profiler SPAudioDataType | grep -A 8 "reSpeaker"

# Check USB device (when in normal mode)
ioreg -p IOUSB -w0 | grep -i "respeaker"

# Check DFU mode (when in safe mode)
dfu-util -l
```

## Two Operation Modes

### USB Mode (plug-and-play)
The device appears as a USB Audio Class 2.0 device. Use the `xvf_host` binary for control (LED effects, GPIO, DoA, configuration). Audio recording at 16kHz, 24-bit.

**Firmware variants:**
- 2-channel (processed audio only)
- 6-channel (processed + raw mic data)

### I2S Mode (embedded with XIAO ESP32S3)
Requires flashing I2S firmware. The XVF3800 acts as I2S master generating its own 12.288 MHz MCLK. Communication via I2C at address `0x2C`.

**I2S firmware**: `respeaker_xvf3800_i2s_master_dfu_firmware_v1.0.7_48k_test5.bin`

## Firmware Flashing

```bash
# Install dfu-util
brew install dfu-util          # macOS
sudo apt install dfu-util      # Linux

# Enter safe mode: hold Mute button while reconnecting USB power
# Flash firmware:
dfu-util -R -e -a 1 -D <firmware_file.bin>
```

Safe mode also enables USB DFU and I2C DFU flashing. Recovery image: `4mb_all_ff.bin`.

### DFU Partitions
- `alt=0` — Factory (safe mode firmware, don't touch)
- `alt=1` — Upgrade (active firmware, flash here)
- `alt=2` — DataPartition (configuration storage)

### Safe Mode Procedure
1. Unplug USB-C cable
2. Press and hold Mute button
3. Plug USB-C cable back in while holding Mute
4. Wait for red LED blinking
5. Release Mute button
6. Device is now in DFU mode

### Common Issue: Wrong Firmware Loaded
**Symptom**: Device not detected as USB audio, LEDs flash green/blue
**Cause**: I2S firmware loaded instead of USB firmware
**Fix**: Enter safe mode and flash USB firmware (v2.0.7 for 2-channel or v2.0.8 for 6-channel)

## Repositories and Resources

### Official Seeed repo
- **GitHub**: https://github.com/respeaker/reSpeaker_XVF3800_USB_4MIC_ARRAY
- **Local clone**: `reSpeaker_XVF3800_USB_4MIC_ARRAY/` (cloned in project directory)
- `host_control/` — platform-specific `xvf_host` binaries (mac_arm64, rpi_64bit, linux_x86_64, win32, jetson)
- `python_control/` — Python USB control scripts (uses `pyusb`, vendor=0x2886, product=0x001A)
- `xmos_firmwares/` — USB and I2S firmware binaries
  - `usb/respeaker_xvf3800_usb_dfu_firmware_v2.0.7.bin` — currently flashed (2-channel)
  - `usb/respeaker_xvf3800_usb_dfu_firmware_6chl_v2.0.8.bin` — 6-channel variant
  - `i2s/respeaker_xvf3800_i2s_master_dfu_firmware_v1.0.7_48k_test5.bin` — I2S mode
  - `recover/4mb_all_ff.bin` — recovery image (full erase)

### ESPHome integration (by formatBCE)
- **GitHub**: https://github.com/formatBCE/Respeaker-XVF3800-ESPHome-integration
- Custom ESPHome components: `respeaker_xvf3800`, `aic3104`
- I2S firmware: `application_xvf3800_inthost-lr48-sqr-i2c-v1.0.7-release.bin`
- Example YAML: `config/respeaker-xvf-satellite-example.yaml`

### Xiaozhi voice assistant
- **GitHub**: https://github.com/Seeed-Projects/Xiaozhi_Esp32S3_reSpeaker
- Uses ESP-IDF: `idf.py set-target esp32s3 && idf.py build && idf.py flash`

## I2C Command Protocol (for XIAO ESP32S3 sketches)

All I2C communication goes through address `0x2C`. The protocol uses resource IDs and command IDs:

### LED Control (Resource ID: 20)
| Function | Command ID | Payload |
|----------|-----------|---------|
| LED Effect | 12 | 1 byte (effect ID) |
| LED Brightness | 13 | 1 byte (0-255) |
| LED Speed | 15 | 1 byte |
| LED Color | 16 | 4 bytes (RGB + 0x00, little-endian) |

### GPIO Control
| Operation | Resource ID | Command ID |
|-----------|------------|-----------|
| Read GPO (5 pins) | 20 | 0 (with 0x80 read flag) |
| Write GPO | 20 | 1 (payload: [pin_index, value]) |
| Read GPI (3 pins) | 36 | 0 (with 0x80 read flag) |
| Read all GPI | 36 | 6 |

### I2C Write Helper Pattern
```cpp
void xmos_write_bytes(uint8_t resid, uint8_t cmd, uint8_t *value, uint8_t write_byte_num) {
  Wire.beginTransmission(0x2C);
  Wire.write(resid);
  Wire.write(cmd);
  Wire.write(write_byte_num);
  for (uint8_t i = 0; i < write_byte_num; i++) Wire.write(value[i]);
  Wire.endTransmission();
}
```

## Audio Codec (TLV320AIC3104) Volume Control

I2C address `0x18`. Key registers:
| Register | Address | Purpose |
|----------|---------|---------|
| Page Control | 0x00 | Bank selection |
| Left DAC Vol | 0x2B | Digital volume |
| Right DAC Vol | 0x2C | Digital volume |
| HPLOUT Level | 0x33 | Headphone left |
| HPROUT Level | 0x41 | Headphone right |
| Left LOP | 0x56 | Line out left |
| Right LOP | 0x5D | Line out right |

18-level volume system: levels 0-8 use DAC attenuation (0dB to -72dB, 9dB steps), levels 9-17 add output gain boost (+1dB to +9dB).

## Arduino Development (XIAO ESP32S3)

**Board Manager URL**: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`

**Common libraries**: `Wire.h` (I2C), AudioTools (I2S audio)

**Standard audio config**: 16kHz sample rate, stereo, 32-bit, I2S full-duplex

## ESPHome / Home Assistant Integration

The ESPHome YAML config uses external components from formatBCE's repos:
- `i2s_audio` from `github.com/formatBCE/esphome` (ref: respeaker_microphone)
- `respeaker_xvf3800` + `aic3104` from the integration repo
- Audio: 48kHz, 32-bit, I2S secondary mode
- Wake words: "Okay Nabu", "Hey Jarvis", "Hey Mycroft" via micro_wake_word
- LED ring controlled via `respeaker_xvf3800` component (not standard ESPHome light platform)
- I2C bus: 100kHz on GPIO5/GPIO6

## xvf_host CLI (USB Mode)

Platform-specific binary from `host_control/` directory. Usage: `./xvf_host COMMAND [values...]`

On macOS ARM64, requires: `libcommand_map.dylib`, `libdevice_usb.dylib`, `libusb-1.0.0.dylib`

### LED Effect IDs
| ID | Effect |
|----|--------|
| 0 | Off |
| 1 | Breath |
| 2 | Rainbow |
| 3 | Single color |
| 4 | DoA tracking |
| 5 | Ring |

Default behavior: rainbow on boot, switches to DoA mode after 2 seconds.

### LED Pattern Reference
| Pattern | Meaning |
|---------|---------|
| Rainbow → DoA | Normal USB mode boot sequence |
| Green/blue flashing | I2S firmware loaded (not USB audio mode) |
| Red LED (near mute) | Microphone muted |
| Red blinking | Safe mode / DFU mode active |
| DoA pointing | Direction of detected sound (0-359°) |

### Audio Output Routing (`AUDIO_MGR_OP_L` / `AUDIO_MGR_OP_R`)
Category/source pairs for channel routing:
- Category 0: Silence
- Category 1-3: Raw/unpacked/amplified mic channels 0-3
- Category 4-5: Far-end reference
- Category 6: Processed beams (slow 0-1, fast 2, auto-select 3)
- Category 7: AEC residual/ASR output
- Category 8: User channels (auto-select copies)

### Default Tuning Parameters
- `AUDIO_MGR_REF_GAIN`: 8.0
- `AUDIO_MGR_MIC_GAIN`: 90
- `AUDIO_MGR_SYS_DELAY`: 12
- `PP_AGCMAXGAIN`: 64.0
- `PP_AGCGAIN`: 2.0

## Python USB Control

Uses `pyusb` with USB vendor control transfers. Device identifiers: vendor `0x2886`, product `0x001A`.

### USB Protocol
- **Write**: `bRequest=0`, `wValue=cmdid`, `wIndex=resid`, payload in data
- **Read**: `bRequest=0`, `wValue=0x80|cmdid`, `wIndex=resid`, response starts with status byte
- Status byte: 0=success, 64=retry (up to 100 attempts with 10ms delay)

### Key Parameter Resource IDs
| Resource ID | Module | Examples |
|-------------|--------|----------|
| 48 | APPLICATION | VERSION, REBOOT, SAVE_CONFIGURATION, USB_BIT_DEPTH |
| 33 | AEC | AEC_AZIMUTH_VALUES, AEC_SPENERGY_VALUES, AEC_NUM_MICS |
| 35 | AUDIO_MGR | MIC_GAIN, REF_GAIN, OP_L, OP_R, SELECTED_CHANNELS |
| 20 | GPO/LED | GPO_READ/WRITE, LED_EFFECT/BRIGHTNESS/COLOR, DOA_VALUE |
| 17 | Post-Processing | AGC settings, noise suppression, echo control |
| 36 | IO_CONFIG | GPI_VALUE_ALL |

### Python Scripts
- `python_control/xvf_host.py` — full-featured CLI with all parameters (argparse-based)
- `python_control/respeaker_get_doa.py` — simple DoA + speech detection polling loop

## Seeed Studio Wiki Documentation

- Introduction: https://wiki.seeedstudio.com/respeaker_xvf3800_introduction/
- XIAO Getting Started: https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_getting_started/
- Python SDK: https://wiki.seeedstudio.com/respeaker_xvf3800_python_sdk/
- I2S Test: https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_i2s/
- RGB LED Control: https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_rgb/
- Volume Control: https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_volume/
- GPIO Control: https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_gpio/
- UDP Audio Streaming: https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_udp_audio_stream/
- MQTT Streaming: https://wiki.seeedstudio.com/respeaker_steams_mqtt/
- Record/Playback: https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_record_playback/
- Home Assistant: https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_home_assistant/
- Xiaozhi Voice Agent: https://wiki.seeedstudio.com/respeaker_xvf_3800_xiaozhi/

## Web App (`web_app/`)

Flask dashboard running on port 5001. Launch with `python app.py` from `web_app/`.

### Current Features (main branch)
- Device control: LED effects, brightness, color, speed
- DoA visualization with 360° compass
- Beam energy monitoring (4 channels)
- Audio recording/playback (16kHz WAV)
- 8 tuning presets (one-click configuration)
- GPIO status monitoring
- Raw USB data monitor
- Dark industrial UI theme

### Tech Stack
- **Backend**: Flask 3.0.0, pyusb 1.2.1, sounddevice 0.4.6, numpy, scipy
- **Frontend**: Vanilla JS, no frameworks, 200ms polling for status updates
- **Audio**: sounddevice InputStream, 16kHz, 2-channel, WAV output to `recordings/`

## Planned Feature: Wake Word Detection + Voice Transcription

**Status**: Not yet implemented. A previous attempt (push-to-talk) was rolled back from main due to breaking the app.

### Chosen Approach
- **Wake word engine**: OpenWakeWord (100% open source, offline, ~200KB models, custom wake word training)
- **Transcription**: MLX Whisper (`mlx-community/whisper-large-v3-turbo`) for Apple Silicon acceleration
- **Integration**: Built into the existing Flask web app, not a separate service

### Architecture
```
ReSpeaker USB (16kHz, 2ch) → sounddevice.InputStream (mono int16, 80ms frames)
  → OpenWakeWord.predict() → [detection] → accumulate audio buffer
  → VAD silence detection → stop → mlx_whisper.transcribe() → SSE to frontend
```

### State Machine
```
IDLE → LISTENING → WAKE_DETECTED → RECORDING → TRANSCRIBING → LISTENING (loop)
```

### Implementation Tasks

1. **Dependencies**: Add `openwakeword`, `onnxruntime`, `mlx-whisper`, `python-dotenv` to `requirements.txt`

2. **Backend (`app.py`)**:
   - `WakeWordState` enum and `ww_state` dict with thread lock
   - Config loading from `.env` (threshold, cooldown, VAD params, Whisper model)
   - SSE event system (`push_sse_event()`, `/api/wakeword/events` endpoint)
   - Audio pipeline: `wakeword_audio_callback()` — 80ms frames through OpenWakeWord, energy-based VAD
   - `_on_wake_detected()` — LED feedback + SSE event
   - `_transcribe_audio()` — concat buffer, float32 conversion, `mlx_whisper.transcribe()`, save WAV
   - API routes: `POST /api/wakeword/start`, `POST /api/wakeword/stop`, `GET /api/wakeword/status`, `POST /api/wakeword/config`, `GET /api/wakeword/transcriptions`, `GET /api/wakeword/events`
   - Mutual exclusion: wake word listener and manual recording cannot run simultaneously (single audio stream)
   - Whisper model preloading at startup if `PRELOAD_WHISPER=1`

3. **Frontend (`templates/index.html`)**:
   - Wake Word Detection card: state indicator, confidence bar, start/stop button
   - Configuration controls: threshold, cooldown, wake word model selector
   - Transcription history list with text, timestamp, duration, language
   - SSE EventSource for real-time updates (detected, recording, transcription results)
   - Mutual exclusion UI: disable manual record when listening, and vice versa

4. **Configuration (`.env`)**:
   - `WAKEWORD_ENABLED`, `WAKEWORD_MODEL` (default: `hey_jarvis`), `WAKEWORD_THRESHOLD` (default: 0.5), `WAKEWORD_COOLDOWN` (default: 2.0s)
   - `VAD_SILENCE_THRESHOLD` (default: 500), `VAD_SILENCE_DURATION` (default: 1.5s), `VAD_MAX_RECORDING_DURATION` (default: 30s)
   - `WHISPER_MODEL`, `WHISPER_LANGUAGE`, `PRELOAD_WHISPER`

### LED State Mapping
| State | Effect | Color | Visual |
|-------|--------|-------|--------|
| IDLE | Rainbow (2) | — | Default |
| LISTENING | Breath (1) | Blue | Slow pulsing blue |
| WAKE_DETECTED | Solid (3) | Cyan | Bright cyan flash |
| RECORDING | Solid (3) | Green | Solid green |
| TRANSCRIBING | Breath (1) | Purple | Fast pulsing purple |

### Key Constraints
- Audio stream mutual exclusion: only one consumer (wake word OR manual recording) at a time
- OpenWakeWord needs 16kHz mono int16, 80ms frames (1280 samples) — must convert from ReSpeaker's 2-channel output
- MLX Whisper expects float32 in [-1.0, 1.0] range
- SSE single-queue is fine for single-user dashboard (v1)
- Graceful degradation: if openwakeword or mlx-whisper not installed, UI shows status badge and disables features
