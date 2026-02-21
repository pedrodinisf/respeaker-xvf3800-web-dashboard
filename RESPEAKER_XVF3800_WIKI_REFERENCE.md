# ReSpeaker XVF3800 - Comprehensive Wiki Documentation Reference

Compiled from Seeed Studio Wiki pages. Last updated: 2026-02-21.

---

## TABLE OF CONTENTS

1. [Hardware Overview & Specifications](#1-hardware-overview--specifications)
2. [Firmware Flashing (DFU)](#2-firmware-flashing-dfu)
3. [USB Audio Recording](#3-usb-audio-recording)
4. [xvf_host Control Tool](#4-xvf_host-control-tool)
5. [XIAO ESP32S3 Getting Started](#5-xiao-esp32s3-getting-started)
6. [I2S Test with XIAO](#6-i2s-test-with-xiao)
7. [RGB LED Control via I2C](#7-rgb-led-control-via-i2c)
8. [Volume Control via I2C (AIC3104)](#8-volume-control-via-i2c-aic3104)
9. [Record and Playback Audio via I2S](#9-record-and-playback-audio-via-i2s)
10. [GPIO Control via I2C](#10-gpio-control-via-i2c)
11. [UDP Audio Streaming](#11-udp-audio-streaming)
12. [MQTT Audio Streaming](#12-mqtt-audio-streaming)
13. [Home Assistant / ESPHome Integration](#13-home-assistant--esphome-integration)
14. [Python SDK (USB Control)](#14-python-sdk-usb-control)
15. [I2C Protocol Reference](#15-i2c-protocol-reference)

---

## 1. Hardware Overview & Specifications

**Source:** https://wiki.seeedstudio.com/respeaker_xvf3800_introduction/

### Key Components

| Component | Details |
|-----------|---------|
| Main Processor | XMOS XVF3800 |
| Microphone Array | 4x PDM MEMS mics in circular pattern |
| Audio Codec | TLV320AIC3104 (I2C addr: 0x18) |
| RGB LEDs | 12x WS2812 individually-addressable |
| Connectivity | USB Type-C (power + data), 3.5mm AUX, JST speaker |
| Speaker Support | 5W amplified speakers |

### Audio Specifications

- 2-channel or 6-channel output options
- Sample rate: 16kHz (standard), 48kHz available
- Sample format: 24-bit (USB), 32-bit (I2S)
- USB Audio Class 2.0 compliant

### Audio Processing Features

- AEC (Acoustic Echo Cancellation)
- Multi-beam beamforming
- De-reverberation
- DoA (Direction of Arrival) detection
- Noise suppression
- AGC (Automatic Gain Control, 60dB)
- VAD (Voice Activity Detection)
- 360-degree far-field voice capture (up to 5 meters)

### GPIO Pin Map

| Pin Name | Direction | Default Function |
|----------|-----------|------------------|
| X1D09 | Input | Mute button status (HIGH when released) |
| X1D13 | Input | Floating |
| X1D34 | Input | Floating |
| X0D11 | Output | Floating |
| X0D30 | Output | Mute LED + mic mute control (HIGH = muted) |
| X0D31 | Output | Amplifier enable (LOW = enabled) |
| X0D33 | Output | WS2812 LED power control (HIGH = on) |
| X0D39 | Output | Floating |

### Dual Operation Modes

- **USB Mode (Default):** Plug-and-play on Windows/macOS/Linux/Raspberry Pi. Configurable via xvf_host over USB.
- **I2S/INT-Device Mode:** For embedded systems (XIAO, ESP32, Arduino). Requires I2S firmware. Configurable via I2C.

---

## 2. Firmware Flashing (DFU)

**Source:** https://wiki.seeedstudio.com/respeaker_xvf3800_introduction/

### Install dfu-util

**macOS:**
```bash
brew install dfu-util
dfu-util -l
```

**Linux/Raspberry Pi:**
```bash
sudo apt install dfu-util
sudo dfu-util -l
```

**Windows:**
Download dfu-util-0.11-binaries.tar.xz, add to system Path, verify with `dfu-util -V`.

### Flash Firmware

```bash
# Basic flash (USB firmware)
dfu-util -R -e -a 1 -D /path/to/dfu_firmware.bin

# With sudo (Linux)
sudo dfu-util -R -e -a 1 -D /path/to/dfu_firmware.bin
```

### Firmware Variants

- 2-channel USB firmware (Conference + ASR)
- 6-channel USB firmware (processed audio + 4 raw mic channels)
- I2S firmware variants (required for XIAO ESP32S3)
- Safe Mode firmware (supports both USB DFU and I2C DFU)

### Safe Mode Recovery

1. Power off completely
2. Press and hold Mute button
3. Reconnect power while holding Mute
4. Red LED blinks to confirm Safe Mode
5. Supports both USB DFU and I2C DFU recovery

### Windows DFU Troubleshooting (Zadig)

1. Install Zadig tool
2. Open Zadig -> Options -> List All Devices
3. Select reSpeaker XVF3800
4. Install WinUSB driver
5. Power-cycle device
6. Verify with: `dfu-util -l`

---

## 3. USB Audio Recording

**Source:** https://wiki.seeedstudio.com/respeaker_xvf3800_introduction/

### Raspberry Pi (Command Line)

```bash
# Find sound card
arecord -l

# Record 5 seconds of audio
arecord -D plughw:4,0 -c 2 -r 16000 -f S16_LE -d 5 output.wav

# Adjust ALSA volume
alsamixer

# Playback recording
aplay -D plughw:4,0 output.wav

# Save ALSA settings
sudo alsactl store
```

### Windows (Audacity)

- Host: Windows WASAPI
- Recording Device: reSpeaker 3800
- Channels: 2 (Stereo)
- Sample Rate: 16000 Hz
- Sample Format: 24-bit

---

## 4. xvf_host Control Tool

**Source:** https://wiki.seeedstudio.com/respeaker_xvf3800_introduction/

### Setup

**Windows:**
```bash
cd C:\Tools\xvf_host
xvf_host.exe --help
xvf_host.exe VERSION
```

**Raspberry Pi:**
```bash
cd /path/to/xvf_host
chmod +x xvf_host
./xvf_host --help
./xvf_host VERSION

# Using I2C interface
./xvf_host --use i2c VERSION
```

### LED Control

```bash
xvf_host.exe led_effect 1           # 0=off, 1=breath, 2=rainbow, 3=solid, 4=DoA
xvf_host.exe led_color 0xff8800     # Set color (orange)
xvf_host.exe led_speed 1            # Set animation speed
xvf_host.exe led_brightness 255     # Set brightness level
xvf_host.exe led_gammify 1          # Enable gamma correction
xvf_host.exe led_doa_color 0x0000ff 0xff0000  # DoA base/directional colors
```

### Configuration Persistence

```bash
xvf_host.exe save_configuration 1
xvf_host.exe clear_configuration 1
```

### GPIO Operations

```bash
# Read input pins
xvf_host.exe GPI_READ_VALUES
# Output: GPI_READ_VALUES 1 0 0 (high, low, low)

# Read output pins
xvf_host.exe GPO_READ_VALUES
# Output: GPO_READ_VALUES 0 1 1 0 0

# Set output pins
xvf_host.exe GPO_WRITE_VALUE 30 1  # Turn ON mute LED
xvf_host.exe GPO_WRITE_VALUE 30 0  # Turn OFF mute LED
```

### Direction of Arrival (DoA)

```bash
xvf_host.exe AEC_AZIMUTH_VALUES
# Output: AEC_AZIMUTH_VALUES 0.91378 (52.36 deg) 0.00000 (0.00 deg) 1.57080 (90.00 deg) 0.91378 (52.36 deg)
```

Values: Focused beam 1, Focused beam 2, Free running beam, Auto selected beam.

### Speech Energy Monitoring

```bash
xvf_host.exe AEC_SPENERGY_VALUES
# Output: AEC_SPENERGY_VALUES 2080656 0 2083455 2080656
```

### Audio Channel Routing

```bash
# Set left channel to Microphone 0
xvf_host.exe AUDIO_MGR_OP_L 3 0

# Set right channel to Far End (reference) data
xvf_host.exe AUDIO_MGR_OP_R 5 0
```

### Tuning Parameters

- `AUDIO_MGR_REF_GAIN`: Speaker input gain (echo signal)
- `AUDIO_MGR_MIC_GAIN`: Microphone input gain
- `AUDIO_MGR_SYS_DELAY`: Delay between mic and speaker signals
- `PP_AGCMAXGAIN`: Maximum automatic gain control level
- `AEC_ASROUTGAIN`: Gain for ASR beam output

---

## 5. XIAO ESP32S3 Getting Started

**Source:** https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_getting_started/

### Prerequisites

- ReSpeaker XVF3800 must have **I2S firmware** flashed (not USB firmware)
- Device does NOT support USB DFU when working with XIAO ESP32S3
- Safe mode enables both USB DFU and I2C DFU options

### Arduino IDE Setup

1. Download Arduino IDE from arduino.cc
2. Open Settings, add ESP32 board manager URL:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. Open Boards Manager, search "ESP32", install
4. Restart Arduino IDE

### I2S Pin Connections (XIAO ESP32S3 to XVF3800)

| Function | XIAO ESP32S3 Pin | XVF3800 Signal |
|----------|------------------|----------------|
| Bit Clock (BCK) | GPIO 8 | I2S_BCLK |
| Word Select (WS/LRCLK) | GPIO 7 | I2S_LRCLK |
| Data TX (to codec) | GPIO 44 | I2S_DIN |
| Data RX (from XVF3800) | GPIO 43 | I2S_DOUT |

### I2C Connection

| Function | XIAO ESP32S3 Pin |
|----------|------------------|
| SDA | GPIO 5 |
| SCL | GPIO 6 |
| XVF3800 I2C Address | 0x2C |
| AIC3104 I2C Address | 0x18 |

---

## 6. I2S Test with XIAO

**Source:** https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_i2s/

### Library Dependency
- `AudioTools` library (by Phil Schatzmann)

### Complete Arduino Sketch

```cpp
#include "AudioTools.h"

const int sampleRate = 16000;
const int frequency = 440;
const int amplitude = 500;
const int halfWavelength = sampleRate / frequency;

AudioInfo info(sampleRate, 2, 32);
I2SStream i2s;
I2SConfig cfg;
int32_t sample = amplitude;
int count = 0;

void printSamplesAndCount(int &nonZero) {
  nonZero = 0;
  bool truncated = false;
  for (int i = 0; i < 32000; i++) {
    int32_t rxSample;
    size_t n = i2s.readBytes((uint8_t*)&rxSample, sizeof(rxSample));
    if (n == sizeof(rxSample)) {
      if (rxSample != 0 && rxSample != 0xFFFFFFFF) {
        nonZero++;
      }
      if (i < 200) {
        Serial.printf("%d ", rxSample);
      } else if (!truncated) {
        Serial.print("... (truncated)");
        truncated = true;
      }
    }
  }
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  while (!Serial);
  AudioLogger::instance().begin(Serial, AudioLogger::Info);

  cfg = i2s.defaultConfig(RXTX_MODE);
  cfg.copyFrom(info);
  cfg.pin_bck = 8;
  cfg.pin_ws = 7;
  cfg.pin_data = 44;
  cfg.pin_data_rx = 43;
  cfg.is_master = true;
  i2s.begin(cfg);
  Serial.println("I2S full-duplex test start");
}

void loop() {
  for (int i = 0; i < 32000; i++) {
    if (count % halfWavelength == 0) {
      sample = -sample;
    }
    i2s.write((uint8_t*)&sample, sizeof(sample));
    count++;
  }

  int nonZero = 0;
  Serial.println("First read attempt:");
  printSamplesAndCount(nonZero);
  Serial.printf("Valid samples: %d\n", nonZero);

  if (nonZero > 16000) {
    Serial.println("I2S RX PASS!");
  } else {
    Serial.println("Valid samples below threshold, trying second read...");
    nonZero = 0;
    Serial.println("Second read attempt:");
    printSamplesAndCount(nonZero);
    Serial.printf("Valid samples: %d\n", nonZero);
    if (nonZero > 16000) {
      Serial.println("I2S RX PASS!");
    } else {
      Serial.println("I2S RX FAIL!");
    }
  }
  Serial.println("Test complete");
  while (true);
}
```

### Configuration Summary

- Sample Rate: 16,000 Hz
- Channels: Stereo (2)
- Bit Width: 32-bit
- Test Signal: 440 Hz square wave, amplitude 500
- Mode: Full duplex (RXTX_MODE)
- ESP32S3 operates as I2S master

---

## 7. RGB LED Control via I2C

**Source:** https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_rgb/

### I2C Protocol Details

| Function | Resource ID | Command ID |
|----------|------------|-----------|
| LED Effect | 20 (GPO_SERVICER_RESID) | 12 |
| LED Brightness | 20 | 13 |
| LED Speed | 20 | 15 |
| LED Color | 20 | 16 |

**LED Effect Values:** 0=off, 1=breath, 2=rainbow, 3=solid, 4=DoA

### Complete Arduino Sketch

```cpp
#include <Wire.h>

#define XMOS_ADDR 0x2C
#define GPO_SERVICER_RESID 20
#define GPO_SERVICER_RESID_LED_EFFECT 12
#define GPO_SERVICER_RESID_LED_COLOR 16
#define GPO_SERVICER_RESID_LED_SPEED 15
#define GPO_SERVICER_RESID_LED_BRIGHTNESS 13

void setup() {
  Wire.begin();
  Serial.begin(115200);
  delay(1000);
  setLEDEffect(1);
  setLEDColor(0xFF8800);
  setLEDSpeed(1);
  setLEDBrightness(255);
}

void loop() {
}

void xmos_write_bytes(uint8_t resid, uint8_t cmd, uint8_t *value, uint8_t write_byte_num) {
  Wire.beginTransmission(XMOS_ADDR);
  Wire.write(resid);
  Wire.write(cmd);
  Wire.write(write_byte_num);
  for (uint8_t i = 0; i < write_byte_num; i++) {
    Wire.write(value[i]);
  }
  Wire.endTransmission();
}

void setLEDEffect(uint8_t effect) {
  uint8_t payload[1] = { effect };
  xmos_write_bytes(GPO_SERVICER_RESID, GPO_SERVICER_RESID_LED_EFFECT, payload, 1);
  Serial.println("LED effect set.");
}

void setLEDColor(uint32_t color) {
  uint8_t payload[4] = {
    (uint8_t)(color & 0xFF),
    (uint8_t)((color >> 8) & 0xFF),
    (uint8_t)((color >> 16) & 0xFF),
    0x00
  };
  xmos_write_bytes(GPO_SERVICER_RESID, GPO_SERVICER_RESID_LED_COLOR, payload, 4);
  Serial.println("LED color set.");
}

void setLEDSpeed(uint8_t speed) {
  uint8_t payload[1] = { speed };
  xmos_write_bytes(GPO_SERVICER_RESID, GPO_SERVICER_RESID_LED_SPEED, payload, 1);
  Serial.println("LED speed set.");
}

void setLEDBrightness(uint8_t brightness) {
  uint8_t payload[1] = { brightness };
  xmos_write_bytes(GPO_SERVICER_RESID, GPO_SERVICER_RESID_LED_BRIGHTNESS, payload, 1);
  Serial.println("LED brightness set.");
}
```

### Color Format

Colors use 24-bit RGB. The payload sends bytes in little-endian order:
- Byte 0: R (bits 0-7 of the color value)
- Byte 1: G (bits 8-15)
- Byte 2: B (bits 16-23)
- Byte 3: 0x00 (padding)

---

## 8. Volume Control via I2C (AIC3104)

**Source:** https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_volume/

### AIC3104 Register Map

| Register | Address | Function |
|----------|---------|----------|
| PAGE_CTRL | 0x00 | Page control |
| LEFT_DAC_VOLUME | 0x2B | Left DAC digital volume |
| RIGHT_DAC_VOLUME | 0x2C | Right DAC digital volume |
| HPLOUT_LEVEL | 0x33 | Headphone left output level |
| HPROUT_LEVEL | 0x41 | Headphone right output level |
| LEFT_LOP_LEVEL | 0x56 | Line out left level |
| RIGHT_LOP_LEVEL | 0x5D | Line out right level |

### Volume Range

- Levels 0-8: DAC attenuation (-72dB to 0dB, step = 9 per level)
- Levels 9-17: Analog boost (+1 to +9 dB)

### Serial Commands

- `+` : Increase volume by one level
- `-` : Decrease volume by one level
- `m` : Toggle between headphone (HPLOUT) and line output (LOP)

### Complete Arduino Sketch

```cpp
#include <Wire.h>
#include "AudioTools.h"

#define AIC3104_ADDR 0x18

#define AIC3104_PAGE_CTRL        0x00
#define AIC3104_LEFT_DAC_VOLUME  0x2B
#define AIC3104_RIGHT_DAC_VOLUME 0x2C
#define AIC3104_HPLOUT_LEVEL     0x33
#define AIC3104_HPROUT_LEVEL     0x41
#define AIC3104_LEFT_LOP_LEVEL   0x56
#define AIC3104_RIGHT_LOP_LEVEL  0x5D

AudioInfo info(16000, 2, 16);
SineWaveGenerator<int16_t> sineWave(32000);
GeneratedSoundStream<int16_t> sound(sineWave);
I2SStream out;
StreamCopy copier(out, sound);

int volume = 8;
bool useHPOUT = true;

void aic3104_reg_write(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(AIC3104_ADDR);
  Wire.write(reg);
  Wire.write(val);
  Wire.endTransmission();
}

void setupAIC3104() {
  Wire.begin();
  aic3104_reg_write(AIC3104_PAGE_CTRL, 0x00);
  aic3104_reg_write(AIC3104_LEFT_DAC_VOLUME, 0x00);
  aic3104_reg_write(AIC3104_RIGHT_DAC_VOLUME, 0x00);
  aic3104_reg_write(AIC3104_HPLOUT_LEVEL, 0x0D);
  aic3104_reg_write(AIC3104_HPROUT_LEVEL, 0x0D);
  aic3104_reg_write(AIC3104_LEFT_LOP_LEVEL, 0x0B);
  aic3104_reg_write(AIC3104_RIGHT_LOP_LEVEL, 0x0B);
}

void setVolume(int vol) {
  vol = constrain(vol, 0, 17);
  volume = vol;
  if (vol <= 8) {
    uint8_t dacVal = vol * 9;
    aic3104_reg_write(AIC3104_LEFT_DAC_VOLUME, dacVal);
    aic3104_reg_write(AIC3104_RIGHT_DAC_VOLUME, dacVal);
    aic3104_reg_write(AIC3104_HPLOUT_LEVEL, 0x0D);
    aic3104_reg_write(AIC3104_HPROUT_LEVEL, 0x0D);
    aic3104_reg_write(AIC3104_LEFT_LOP_LEVEL, 0x0B);
    aic3104_reg_write(AIC3104_RIGHT_LOP_LEVEL, 0x0B);
  } else {
    aic3104_reg_write(AIC3104_LEFT_DAC_VOLUME, 0x00);
    aic3104_reg_write(AIC3104_RIGHT_DAC_VOLUME, 0x00);
    uint8_t gain = (vol - 8);
    uint8_t outVal = (gain << 4) | 0x0B;
    if (useHPOUT) {
      aic3104_reg_write(AIC3104_HPLOUT_LEVEL, outVal);
      aic3104_reg_write(AIC3104_HPROUT_LEVEL, outVal);
    } else {
      aic3104_reg_write(AIC3104_LEFT_LOP_LEVEL, outVal);
      aic3104_reg_write(AIC3104_RIGHT_LOP_LEVEL, outVal);
    }
  }
  Serial.print("Volume set to ");
  Serial.print(volume);
  Serial.print(" (");
  if (vol <= 8) Serial.print("-" + String(volume * 1) + " dB)");
  else Serial.print("+" + String((vol - 8)) + " dB)");
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  while (!Serial);
  setupAIC3104();
  setVolume(volume);
  auto config = out.defaultConfig(TX_MODE);
  config.copyFrom(info);
  config.pin_bck = 8;
  config.pin_ws = 7;
  config.pin_data = 44;
  config.is_master = true;
  out.begin(config);
  sineWave.begin(info, N_A4);
}

void loop() {
  copier.copy();
  if (Serial.available()) {
    char c = Serial.read();
    if (c == '+' && volume < 17) {
      setVolume(volume + 1);
    } else if (c == '-' && volume > 0) {
      setVolume(volume - 1);
    } else if (c == 'm') {
      useHPOUT = !useHPOUT;
      setVolume(volume);
      Serial.print("Switched to ");
      Serial.println(useHPOUT ? "HPLOUT (headphone)" : "LOP (line out)");
    }
  }
}
```

---

## 9. Record and Playback Audio via I2S

**Source:** https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_record_playback/

### Complete Arduino Sketch

```cpp
#include "AudioTools.h"

AudioInfo info(16000, 2, 32);
I2SStream out;
I2SConfig config;
uint8_t buffer[128000];
size_t bytes_read = 0;
size_t bytes_write = 0;

void setup(void) {
    Serial.begin(115200);
    while(!Serial);
    AudioLogger::instance().begin(Serial, AudioLogger::Info);

    Serial.println("starting I2S...");
    config = out.defaultConfig(TX_MODE);
    config.copyFrom(info);

    config.pin_bck = 8;
    config.pin_ws = 7;
    config.pin_data = 44;
    config.pin_data_rx = 43;
    config.is_master = true;
    out.begin(config);
    Serial.println("started...");
}

void loop() {
    // Record: switch to RX mode, read audio into buffer
    out.end();
    config.rx_tx_mode = RX_MODE;
    out.begin(config);
    bytes_read = out.readBytes(buffer, 128000);

    // Playback: switch to TX mode, write buffer back
    out.end();
    config.rx_tx_mode = TX_MODE;
    out.begin(config);
    bytes_write = out.write(buffer, 128000);
}
```

### Configuration

- Sample rate: 16kHz
- Channels: 2 (stereo)
- Bit depth: 32-bit
- Buffer size: 128,000 bytes
- Mode: Alternating RX/TX (half-duplex approach)

---

## 10. GPIO Control via I2C

**Source:** https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_gpio/

### I2C Protocol for GPIO

| Operation | Resource ID | Command ID | Payload |
|-----------|------------|-----------|---------|
| Read GPO | 20 (GPO_SERVICER_RESID) | 0 (read) | - |
| Write GPO | 20 | 1 (write) | [gpio_index, value] |
| Read GPI | 36 (IO_CONFIG_SERVICER_RESID) | 0 (read) / 6 (GPI_VALUE_ALL) | - |

**Note:** For read commands, OR the command ID with 0x80 (e.g., 0x00 | 0x80 = 0x80).

### Sketch 1: Read GPO Pin States

```cpp
#include <Wire.h>

#define XMOS_ADDR 0x2C
#define GPO_SERVICER_RESID 20
#define GPO_SERVICER_RESID_GPO_READ_VALUES 0
#define GPO_GPO_READ_NUM_BYTES 5

void setup() {
  Serial.begin(115200);
  while (!Serial);
  Wire.begin();
  delay(1000);
  Serial.println("XVF3800 GPO Read Test Starting...");
}

void loop() {
  uint8_t gpo_values[GPO_GPO_READ_NUM_BYTES] = {0};
  uint8_t status = 0xFF;
  bool success = read_gpo_values(gpo_values, &status);

  if (success) {
    Serial.print("I2C Communication SUCCESS. Status byte: 0x");
    Serial.print(status, HEX);
    Serial.print(" | GPO Output Values: ");
    for (uint8_t i = 0; i < GPO_GPO_READ_NUM_BYTES; i++) {
      Serial.print("0x");
      Serial.print(gpo_values[i], HEX);
      Serial.print(" ");
    }
    Serial.println();
  } else {
    Serial.println("Failed to read GPO values.");
  }
  delay(1000);
}

bool read_gpo_values(uint8_t *buffer, uint8_t *status) {
  const uint8_t resid = GPO_SERVICER_RESID;
  const uint8_t cmd = GPO_SERVICER_RESID_GPO_READ_VALUES | 0x80;
  const uint8_t read_len = GPO_GPO_READ_NUM_BYTES;

  Wire.beginTransmission(XMOS_ADDR);
  Wire.write(resid);
  Wire.write(cmd);
  Wire.write(read_len + 1);
  uint8_t result = Wire.endTransmission();

  if (result != 0) {
    Serial.print("I2C Write Error: ");
    Serial.println(result);
    return false;
  }

  Wire.requestFrom(XMOS_ADDR, (uint8_t)(read_len + 1));
  if (Wire.available() < read_len + 1) {
    Serial.println("I2C Read Error: Not enough data received.");
    return false;
  }

  *status = Wire.read();
  for (uint8_t i = 0; i < read_len; i++) {
    buffer[i] = Wire.read();
  }
  return true;
}
```

### Sketch 2: Read GPI Pin States

```cpp
#include <Wire.h>

#define XMOS_ADDR 0x2C
#define IO_CONFIG_SERVICER_RESID 36
#define IO_CONFIG_SERVICER_RESID_GPI_READ_VALUES 0
#define GPI_READ_NUM_BYTES 3

void setup() {
  Serial.begin(115200);
  while (!Serial);
  Wire.begin();
  delay(1000);
  Serial.println("XVF3800 GPI Read Test Starting...");
}

void loop() {
  uint8_t gpi_values[GPI_READ_NUM_BYTES] = {0};
  uint8_t status = 0xFF;
  bool success = read_gpi_values(gpi_values, &status);

  if (success) {
    Serial.print("I2C Communication SUCCESS. Status byte: 0x");
    Serial.print(status, HEX);
    Serial.print(" | GPI Input Values: ");
    for (uint8_t i = 0; i < GPI_READ_NUM_BYTES; i++) {
      Serial.print("0x");
      Serial.print(gpi_values[i], HEX);
      Serial.print(" ");
    }
    Serial.println();
  } else {
    Serial.println("Failed to read GPI values.");
  }
  delay(1000);
}

bool read_gpi_values(uint8_t *buffer, uint8_t *status) {
  const uint8_t resid = IO_CONFIG_SERVICER_RESID;
  const uint8_t cmd = IO_CONFIG_SERVICER_RESID_GPI_READ_VALUES | 0x80;
  const uint8_t read_len = GPI_READ_NUM_BYTES;

  Wire.beginTransmission(XMOS_ADDR);
  Wire.write(resid);
  Wire.write(cmd);
  Wire.write(read_len + 1);
  uint8_t result = Wire.endTransmission();

  if (result != 0) {
    Serial.print("I2C Write Error: ");
    Serial.println(result);
    return false;
  }

  Wire.requestFrom(XMOS_ADDR, (uint8_t)(read_len + 1));
  if (Wire.available() < read_len + 1) {
    Serial.println("I2C Read Error: Not enough data received.");
    return false;
  }

  *status = Wire.read();
  for (uint8_t i = 0; i < read_len; i++) {
    buffer[i] = Wire.read();
  }
  return true;
}
```

### Sketch 3: Write GPO - Mute/Unmute Mic

```cpp
#include <Wire.h>

#define XMOS_ADDR 0x2C
#define GPO_SERVICER_RESID 20
#define GPO_SERVICER_RESID_GPO_WRITE_VALUE 1
#define IO_CONFIG_SERVICER_RESID 36
#define IO_CONFIG_SERVICER_RESID_GPI_VALUE_ALL 6

void setup() {
  Wire.begin();
  Serial.begin(115200);
  delay(1000);
  Serial.println("Muting Mic (Setting GPIO 30 HIGH)");
  muteMic();
  delay(5000);
  Serial.println("Unmuting Mic (Setting GPIO 30 LOW)");
  unmuteMic();
  delay(3000);
  Serial.println("Reading GPIO Status...");
  readGPIOStatus();
}

void loop() {
}

void setGPIO30(uint8_t level) {
  uint8_t payload[2] = {30, level};
  xmos_write_bytes(GPO_SERVICER_RESID, GPO_SERVICER_RESID_GPO_WRITE_VALUE, payload, 2);
  Serial.print("Command Sent: GPIO 30 = ");
  Serial.println(level);
}

void muteMic() {
  setGPIO30(1);
}

void unmuteMic() {
  setGPIO30(0);
}

void xmos_write_bytes(uint8_t resid, uint8_t cmd, uint8_t *value, uint8_t write_byte_num) {
  Wire.beginTransmission(XMOS_ADDR);
  Wire.write(resid);
  Wire.write(cmd);
  Wire.write(write_byte_num);
  for (uint8_t i = 0; i < write_byte_num; i++) {
    Wire.write(value[i]);
  }
  Wire.endTransmission();
}

void readGPIOStatus() {
  uint8_t buffer[4] = {0};

  Wire.beginTransmission(XMOS_ADDR);
  Wire.write(IO_CONFIG_SERVICER_RESID);
  Wire.write(IO_CONFIG_SERVICER_RESID_GPI_VALUE_ALL);
  Wire.write(1);
  Wire.endTransmission(false);

  Wire.requestFrom(XMOS_ADDR, 5);
  if (Wire.available() < 5) {
    Serial.println("Error: Not enough bytes received from XVF3800.");
    return;
  }

  uint8_t status = Wire.read();
  for (int i = 0; i < 4; i++) {
    buffer[i] = Wire.read();
  }

  uint32_t gpio_status = ((uint32_t)buffer[3] << 24) |
                         ((uint32_t)buffer[2] << 16) |
                         ((uint32_t)buffer[1] << 8) |
                         ((uint32_t)buffer[0]);

  Serial.print("GPIO Status Register = 0x");
  Serial.println(gpio_status, HEX);

  bool gpio30 = (gpio_status >> 30) & 0x01;
  Serial.print("GPIO 30 State: ");
  Serial.println(gpio30 ? "HIGH (Muted)" : "LOW (Unmuted)");
}
```

---

## 11. UDP Audio Streaming

**Source:** https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_udp_audio_stream/

### Arduino Sketch (ESP32S3 Sender)

```cpp
#include "WiFi.h"
#include "WiFiUdp.h"
#include "AudioTools.h"

const char* ssid = "Your-SSID";
const char* password = "WIFI-PASSWORD";
const char* udpAddress = "192.168.x.x";
const int udpPort = 12345;

WiFiUDP udp;

AudioInfo info(16000, 2, 32);
I2SStream i2s_in;
I2SConfig i2s_config;

#define BUFFER_SIZE 1024
uint8_t buffer[BUFFER_SIZE];

// 5 seconds: 16000 Hz x 2 channels x 4 bytes = 128,000 bytes/sec x 5 = 640,000
#define TOTAL_BYTES 640000

void connectWiFi() {
  Serial.printf("Connecting to WiFi: %s\n", ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nConnected!");
  Serial.printf("IP Address: %s\n", WiFi.localIP().toString().c_str());
}

void setupI2SInput() {
  i2s_config = i2s_in.defaultConfig(RX_MODE);
  i2s_config.copyFrom(info);
  i2s_config.pin_bck = 8;
  i2s_config.pin_ws = 7;
  i2s_config.pin_data = 44;
  i2s_config.pin_data_rx = 43;
  i2s_config.is_master = true;
  i2s_in.begin(i2s_config);
  Serial.println("I2S input started.");
}

void setup() {
  Serial.begin(115200);
  while(!Serial);
  AudioLogger::instance().begin(Serial, AudioLogger::Info);
  connectWiFi();
  setupI2SInput();
  delay(500);

  Serial.printf("Sending 5 seconds of audio via UDP to %s:%d\n", udpAddress, udpPort);

  size_t total_sent = 0;
  size_t bytes_read = 0;

  while (total_sent < TOTAL_BYTES) {
    bytes_read = i2s_in.readBytes(buffer, BUFFER_SIZE);
    if (bytes_read > 0) {
      udp.beginPacket(udpAddress, udpPort);
      udp.write(buffer, bytes_read);
      udp.endPacket();
      total_sent += bytes_read;
      if (total_sent % 64000 == 0) {
        Serial.printf("Sent %d bytes (%.1f seconds)\n", total_sent, total_sent / 128000.0);
      }
    } else {
      Serial.println("Warning: No data read from I2S");
      delay(10);
    }
  }
  Serial.printf("Finished! Sent %d bytes total\n", total_sent);
}

void loop() {
}
```

### Python Receiver Script

```python
import socket
import wave
import time

udp_ip = "0.0.0.0"
udp_port = 12345

SAMPLE_RATE = 16000
CHANNELS = 2
SAMPLE_WIDTH = 4  # 32-bit = 4 bytes

EXPECTED_BYTES = 640000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((udp_ip, udp_port))
sock.settimeout(2.0)

print(f"Listening for audio on {udp_ip}:{udp_port}...")
audio_data = bytearray()
last_packet_time = time.time()

try:
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            if data:
                audio_data.extend(data)
                last_packet_time = time.time()
                if len(audio_data) % 64000 < 4096:
                    print(f"Received {len(audio_data)} bytes ({len(audio_data) / 128000:.1f} seconds)")
        except socket.timeout:
            if len(audio_data) > 0:
                print("Timeout - assuming transmission complete")
                break
            else:
                print("Waiting for data...")
                continue
except KeyboardInterrupt:
    print("\nStopped by user")

if len(audio_data) > 0:
    print(f"\nTotal received: {len(audio_data)} bytes")
    print("Saving to output.wav...")
    with wave.open("output.wav", "wb") as wav_file:
        wav_file.setnchannels(CHANNELS)
        wav_file.setsampwidth(SAMPLE_WIDTH)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(bytes(audio_data))
    print("Done! Audio saved to output.wav")
else:
    print("No data received!")
sock.close()
```

---

## 12. MQTT Audio Streaming

**Source:** https://wiki.seeedstudio.com/respeaker_steams_mqtt/

### Library Dependencies

- `ArduinoMqttClient` (from Arduino library manager)
- `AudioTools`
- `WiFi.h`

### Complete Arduino Sketch

```cpp
#include "WiFi.h"
#include "ArduinoMqttClient.h"
#include "AudioTools.h"

#define SIZE 1024
#define N 100

const char* ssid = "SSID";
const char* password = "PASSWORD";
const char* broker = "test.mosquitto.org";
const char* topic = "audio.wav";
int port = 1883;

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

AudioInfo info(16000, 1, 32);
WhiteNoiseGenerator<int16_t> noise(32000);
GeneratedSoundStream<int16_t> in_stream(noise);
EncodedAudioStream out_stream(&mqttClient, new WAVEncoder());
StreamCopy copier(out_stream, in_stream, SIZE);

void connectWIFI() {
  Serial.print("Attempting to connect to WPA SSID: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi ..");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print('.');
    delay(1000);
  }
  Serial.println("You're connected to the network");
  Serial.println();
}

void connectMQTT() {
  mqttClient.setId("reSpeaker");
  Serial.print("Attempting to connect to the MQTT broker: ");
  Serial.println(broker);
  if (!mqttClient.connect(broker, port)) {
    Serial.print("MQTT connection failed! Error code = ");
    Serial.println(mqttClient.connectError());
    stop();
  }
  Serial.println("You're connected to the MQTT broker!");
  Serial.println();
}

void sendMQTT() {
  out_stream.begin(info);
  mqttClient.beginMessage(topic, SIZE * N, true);
  copier.copyN(N);
  mqttClient.endMessage();
}

void setup() {
  Serial.begin(115200);
  AudioLogger::instance().begin(Serial, AudioLogger::Info);
  connectWIFI();
  connectMQTT();
  noise.begin(info);
  in_stream.begin(info);
  sendMQTT();
}

void loop() {
  mqttClient.poll();
  delay(10000);
}
```

### Notes

- This example generates white noise and sends it as WAV over MQTT
- To stream real microphone audio, replace the noise generator with I2S input
- Default broker: test.mosquitto.org (public, for testing only)
- Audio: 16kHz, mono, 32-bit, 1024-byte chunks, 100 chunks per message

---

## 13. Home Assistant / ESPHome Integration

**Source:** https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_home_assistant/

### Overview

Creates a voice assistant using ReSpeaker XVF3800 + XIAO ESP32S3 with Home Assistant. Supports wake words "Okay Nabu", "Hey Jarvis", "Hey Mycroft", and "Kenobi".

### Critical Firmware Note

The XVF3800 requires a 12.288 MHz MCLK. ESPHome cannot generate this due to API limitations. Custom firmware makes the XVF3800 act as I2S master, generating its own clocks.

### Firmware & Repository Links

- **I2S Firmware:** https://github.com/respeaker/reSpeaker_XVF3800_USB_4MIC_ARRAY/tree/master/xmos_firmwares/i2s
- **ESPHome I2S components:** https://github.com/formatBCE/esphome (ref: respeaker_microphone)
- **XVF3800 + AIC3104 ESPHome drivers:** https://github.com/formatBCE/Respeaker-XVF3800-ESPHome-integration (ref: main)
- **Example YAML config:** https://github.com/formatBCE/Respeaker-XVF3800-ESPHome-integration/tree/main/config
- **Custom firmware binary:** application_xvf3800_inthost-lr48-sqr-i2c-v1.0.7-release.bin (MD5: 043a848f544ff2c7265ac19685daf5de)

### ESPHome YAML - Key Sections

#### ESP32 Platform

```yaml
esp32:
  board: esp32-s3-devkitc-1
  cpu_frequency: 240MHz
  variant: esp32s3
  flash_size: 8MB
  framework:
    type: esp-idf
    version: recommended
    sdkconfig_options:
      CONFIG_ESP32S3_DATA_CACHE_64KB: "y"
      CONFIG_ESP32S3_DATA_CACHE_LINE_64B: "y"
      CONFIG_ESP32S3_INSTRUCTION_CACHE_32KB: "y"
      CONFIG_SPIRAM_RODATA: "y"
      CONFIG_SPIRAM_FETCH_INSTRUCTIONS: "y"
      CONFIG_BT_ALLOCATION_FROM_SPIRAM_FIRST: "y"
      CONFIG_BT_BLE_DYNAMIC_ENV_MEMORY: "y"
      CONFIG_MBEDTLS_EXTERNAL_MEM_ALLOC: "y"
      CONFIG_MBEDTLS_SSL_PROTO_TLS1_3: "y"
```

#### External Components

```yaml
external_components:
  - source:
      type: git
      url: https://github.com/formatBCE/esphome
      ref: respeaker_microphone
    components: [i2s_audio]
    refresh: 0s
  - source:
      type: git
      url: https://github.com/formatBCE/Respeaker-XVF3800-ESPHome-integration
      ref: main
    components: [respeaker_xvf3800, aic3104]
    refresh: 0s
```

#### I2C Bus

```yaml
i2c:
  - id: internal_i2c
    sda: GPIO5
    scl: GPIO6
    scan: true
    frequency: 100kHz
```

#### PSRAM

```yaml
psram:
  mode: octal
  speed: 80MHz
  ignore_not_found: false
```

#### ReSpeaker XVF3800 Component

```yaml
respeaker_xvf3800:
  id: respeaker
  address: 0x2C
  mute_switch:
    id: mic_mute_switch
    name: "Microphone Mute"
    update_interval: 1s
  dfu_version:
    name: "Firmware Version"
    update_interval: 120s
  led_beam_sensor:
    name: "Voice Beam Direction"
    id: beam_direction
    internal: true
  firmware:
    url: https://github.com/formatBCE/Respeaker-XVF3800-ESPHome-integration/raw/refs/heads/main/application_xvf3800_inthost-lr48-sqr-i2c-v1.0.7-release.bin
    version: "1.0.7"
    md5: 043a848f544ff2c7265ac19685daf5de
```

#### Audio DAC

```yaml
audio_dac:
  - platform: aic3104
    id: aic3104_dac
    i2c_id: internal_i2c
```

#### I2S Audio

```yaml
i2s_audio:
  - id: i2s_output
    i2s_lrclk_pin:
      number: GPIO7
      allow_other_uses: true
    i2s_bclk_pin:
      number: GPIO8
      allow_other_uses: true
  - id: i2s_input
    i2s_lrclk_pin:
      number: GPIO7
      allow_other_uses: true
    i2s_bclk_pin:
      number: GPIO8
      allow_other_uses: true
```

#### Microphone

```yaml
microphone:
  - platform: i2s_audio
    id: i2s_mics
    i2s_din_pin: GPIO43
    adc_type: external
    pdm: false
    sample_rate: 48000
    bits_per_sample: 32bit
    i2s_mode: secondary
    i2s_audio_id: i2s_input
    channel: stereo
```

#### Speaker (Hardware + Virtual Mixing)

```yaml
speaker:
  - platform: i2s_audio
    id: i2s_audio_speaker
    sample_rate: 48000
    i2s_mode: secondary
    i2s_dout_pin: GPIO44
    bits_per_sample: 32bit
    i2s_audio_id: i2s_output
    dac_type: external
    channel: stereo
    timeout: never
    buffer_duration: 100ms
    audio_dac: aic3104_dac
  - platform: mixer
    id: mixing_speaker
    output_speaker: i2s_audio_speaker
    num_channels: 2
    task_stack_in_psram: true
    source_speakers:
      - id: announcement_mixing_input
        timeout: never
      - id: media_mixing_input
        timeout: never
  - platform: resampler
    id: announcement_resampling_speaker
    output_speaker: announcement_mixing_input
    sample_rate: 48000
    bits_per_sample: 16
  - platform: resampler
    id: media_resampling_speaker
    output_speaker: media_mixing_input
    sample_rate: 48000
    bits_per_sample: 16
```

#### Media Player

```yaml
media_player:
  - platform: speaker_source
    id: external_media_player
    name: Media Player
    announcement_speaker: announcement_resampling_speaker
    media_speaker: media_resampling_speaker
    announcement_pipeline:
      format: FLAC
      num_channels: 1
      sample_rate: 48000
    media_pipeline:
      format: FLAC
      num_channels: 2
      sample_rate: 48000
    volume_increment: 0.05
    volume_min: 0.0
    volume_max: 1.0
```

#### Micro Wake Word

```yaml
micro_wake_word:
  id: mww
  microphone:
    microphone: i2s_mics
    channels: 1
  stop_after_detection: false
  models:
    - model: https://github.com/kahrendt/microWakeWord/releases/download/okay_nabu_20241226.3/okay_nabu.json
      id: okay_nabu
    - model: https://raw.githubusercontent.com/formatBCE/Respeaker-Lite-ESPHome-integration/refs/heads/main/microwakeword/models/v2/kenobi.json
      id: kenobi
    - model: hey_jarvis
      id: hey_jarvis
    - model: hey_mycroft
      id: hey_mycroft
    - model: https://github.com/kahrendt/microWakeWord/releases/download/stop/stop.json
      id: stop
      internal: true
  vad:
    probability_cutoff: 0.05
```

#### Voice Assistant

```yaml
voice_assistant:
  id: va
  microphone:
    microphone: i2s_mics
    channels: 0
  media_player: external_media_player
  micro_wake_word: mww
  use_wake_word: false
  noise_suppression_level: 0
  auto_gain: 0 dbfs
  volume_multiplier: 1
```

#### Voice Assistant Phase IDs

| Phase | ID | Description |
|-------|-----|-------------|
| Idle | 1 | Ready, waiting for wake word |
| Waiting for command | 2 | Wake word detected, waiting |
| Listening | 3 | Actively listening to command |
| Thinking | 4 | Processing command |
| Replying | 5 | Speaking response |
| Not ready | 10 | Not initialized |
| Error | 11 | Error occurred |

#### LED Ring Control

The LED ring is controlled via the `respeaker_xvf3800` component using `id(respeaker).set_led_ring(colors)` calls within scripts. Effects include: breathe, rainbow, comet (clockwise/counterclockwise), twinkle, timer_tick, and led_beam.

Color presets available: Purple, Blue, Green, Yellow, Cyan, White, Orange, Pink, Custom.

#### Wake Word Sensitivity Levels

| Level | okay_nabu cutoff | hey_jarvis cutoff | hey_mycroft cutoff |
|-------|-----------------|-------------------|-------------------|
| Slightly sensitive | 0.85 (217) | 0.97 (247) | 0.99 (253) |
| Moderately sensitive | 0.69 (176) | 0.92 (235) | 0.95 (242) |
| Very sensitive | 0.56 (143) | 0.83 (212) | 0.93 (237) |

---

## 14. Python SDK (USB Control)

**Source:** https://wiki.seeedstudio.com/respeaker_xvf3800_python_sdk/

### Method 1: Direct USB Control (pyusb)

#### Installation

```bash
pip install pyusb
```

#### USB Identifiers

- Vendor ID: 0x2886
- Product ID: 0x001A

#### Complete Python Script

```python
import sys
import struct
import usb.core
import usb.util
import time

PARAMETERS = {
    "VERSION": (48, 0, 3, "ro", "uint8"),
    "AEC_AZIMUTH_VALUES": (33, 75, 16, "ro", "radians"),
    "DOA_VALUE": (20, 18, 4, "ro", "uint16"),
    "REBOOT": (48, 7, 1, "wo", "uint8"),
}
# Parameter tuple format: (resid, cmdid, length, access_mode, datatype)

class ReSpeaker:
    TIMEOUT = 100000

    def __init__(self, dev):
        self.dev = dev

    def write(self, name, data_list):
        try:
            data = PARAMETERS[name]
        except KeyError:
            return
        if data[3] == "ro":
            raise ValueError('{} is read-only'.format(name))
        if len(data_list) != data[2]:
            raise ValueError('{} value count is not {}'.format(name, data[2]))
        windex = data[0]
        wvalue = data[1]
        data_type = data[4]
        data_cnt = data[2]
        payload = []
        if data_type == 'float' or data_type == 'radians':
            for i in range(data_cnt):
                payload += struct.pack(b'f', float(data_list[i]))
        elif data_type == 'char' or data_type == 'uint8':
            for i in range(data_cnt):
                payload += data_list[i].to_bytes(1, byteorder='little')
        else:
            for i in range(data_cnt):
                payload += struct.pack(b'i', data_list[i])
        print("WriteCMD: cmdid: {}, resid: {}, payload: {}".format(wvalue, windex, payload))
        self.dev.ctrl_transfer(
            usb.util.CTRL_OUT | usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_DEVICE,
            0, wvalue, windex, payload, self.TIMEOUT)

    def read(self, name):
        try:
            data = PARAMETERS[name]
        except KeyError:
            return
        resid = data[0]
        cmdid = 0x80 | data[1]
        length = data[2] + 1
        response = self.dev.ctrl_transfer(
            usb.util.CTRL_IN | usb.util.CTRL_TYPE_VENDOR | usb.util.CTRL_RECIPIENT_DEVICE,
            0, cmdid, resid, length, self.TIMEOUT)
        if data[4] == 'uint8':
            result = response.tolist()
        elif data[4] == 'radians':
            byte_data = response.tobytes()
            num_values = (length - 1) / 4
            match_str = '<'
            for i in range(int(num_values)):
                match_str += 'f'
            result = struct.unpack(match_str, byte_data[1:length])
        elif data[4] == 'uint16':
            result = response.tolist()
        return result

    def close(self):
        usb.util.dispose_resources(self.dev)

def find(vid=0x2886, pid=0x001A):
    dev = usb.core.find(idVendor=vid, idProduct=pid)
    if not dev:
        return
    return ReSpeaker(dev)

def main():
    dev = find()
    if not dev:
        print('No device found')
        sys.exit(1)
    print('{}: {}'.format("VERSION", dev.read("VERSION")))
    while True:
        result = dev.read("DOA_VALUE")
        print('{}: {}, {}: {}'.format("SPEECH_DETECTED", result[3], "DOA_VALUE", result[1]))
        time.sleep(1)
    dev.close()

if __name__ == '__main__':
    main()
```

#### DOA_VALUE Result Interpretation

- `result[0]`: Status byte
- `result[1]`: DoA value (direction in degrees)
- `result[3]`: Speech detected flag (VAD)

### Method 2: xvf_host Wrapper (subprocess)

#### Complete Python Script (test.py)

```python
import subprocess
import sys
import time

XVF_HOST_PATH = "./xvf_host"

def run_command(*args):
    """Run a command using the xvf_host tool."""
    command = ["sudo", XVF_HOST_PATH] + list(map(str, args))
    try:
        print(f"Running: {' '.join(command)}")
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        print("Output:\n", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error:\n", e.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_command("VERSION")
    time.sleep(0.005)
    run_command("led_effect", 1)
    time.sleep(0.005)
    run_command("led_color", "0xff8800")
    time.sleep(0.005)
    run_command("led_speed", 1)
    time.sleep(0.005)
    run_command("led_brightness", 255)
    time.sleep(0.005)
    run_command("clear_configuration", 1)
    time.sleep(0.005)
```

#### GitHub Repositories

- Windows: https://github.com/KasunThushara/reSpeakerXVF
- Raspberry Pi: https://github.com/KasunThushara/reSpeakerXVF_rpi

---

## 15. I2C Protocol Reference

### XVF3800 I2C Communication Pattern

**Address:** 0x2C

#### Write Command Format

```
Wire.beginTransmission(0x2C)
Wire.write(resource_id)       // Which subsystem
Wire.write(command_id)        // Which command
Wire.write(payload_length)    // How many data bytes follow
Wire.write(payload_bytes...)  // The data
Wire.endTransmission()
```

#### Read Command Format

```
// Step 1: Send read request
Wire.beginTransmission(0x2C)
Wire.write(resource_id)
Wire.write(command_id | 0x80)   // Set bit 7 for read
Wire.write(read_length + 1)     // Expected response length + status byte
Wire.endTransmission()

// Step 2: Read response
Wire.requestFrom(0x2C, read_length + 1)
status = Wire.read()             // First byte is always status
data[0] = Wire.read()            // Then data bytes follow
data[1] = Wire.read()
...
```

#### Known Resource IDs and Command IDs

| Resource ID | Name | Commands |
|------------|------|----------|
| 20 | GPO_SERVICER_RESID | 0=read_values, 1=write_value, 12=led_effect, 13=led_brightness, 15=led_speed, 16=led_color |
| 36 | IO_CONFIG_SERVICER_RESID | 0=gpi_read_values, 6=gpi_value_all |
| 33 | AEC | 75=azimuth_values |
| 48 | SYSTEM | 0=version, 7=reboot |

### AIC3104 Audio Codec I2C

**Address:** 0x18

#### Key Registers

| Register | Address | Description |
|----------|---------|-------------|
| Page Control | 0x00 | Select register page |
| Left DAC Volume | 0x2B | Digital volume, left |
| Right DAC Volume | 0x2C | Digital volume, right |
| HPLOUT Level | 0x33 | Headphone left output |
| HPROUT Level | 0x41 | Headphone right output |
| Left LOP Level | 0x56 | Line output left |
| Right LOP Level | 0x5D | Line output right |

---

## Pages Successfully Fetched

| # | URL | Status |
|---|-----|--------|
| 1 | https://wiki.seeedstudio.com/respeaker_xvf3800_introduction/ | OK |
| 2 | https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_getting_started/ | OK |
| 3 | https://wiki.seeedstudio.com/respeaker_xvf3800_python_sdk/ | OK |
| 4 | https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_i2s/ | OK |
| 5 | https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_rgb/ | OK |
| 6 | https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_volume/ | OK |
| 7 | https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_record_playback/ | OK |
| 8 | https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_gpio/ | OK |
| 9 | https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_udp_audio_stream/ | OK |
| 10 | https://wiki.seeedstudio.com/respeaker_steams_mqtt/ | OK |
| 11 | https://wiki.seeedstudio.com/respeaker_xvf3800_xiao_home_assistant/ | OK |

## Pages Not Found (404)

- respeaker_xvf3800_xiao_led (actual URL: respeaker_xvf3800_xiao_rgb)
- respeaker_xvf3800_xiao_mqtt (actual URL: respeaker_steams_mqtt)
- respeaker_xvf3800_xiao_udp (actual URL: respeaker_xvf3800_xiao_udp_audio_stream)
- respeaker_xvf3800_xiao_http (no dedicated page found)
- respeaker_xvf3800_xiao_homeassistant (actual URL: respeaker_xvf3800_xiao_home_assistant)
- respeaker_xvf3800_xiao_doa (DoA covered in Python SDK and xvf_host pages)
- respeaker_xvf3800_xiao_vad (VAD covered in Python SDK and Home Assistant pages)
- respeaker_xvf3800_xiao_record (actual URL: respeaker_xvf3800_xiao_record_playback)
