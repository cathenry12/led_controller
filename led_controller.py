#!/usr/bin/env python3
import time
import json
import argparse
import signal
import sys
import logging
import threading
import colorsys
from flask import Flask, render_template, request, jsonify
from rpi_ws281x import PixelStrip, Color

# Try importing BlueDot (handle if not installed for testing)
try:
    from bluedot import BlueDot
    BLUEDOT_AVAILABLE = True
except ImportError:
    BLUEDOT_AVAILABLE = False
    logging.warning("BlueDot library not found. Bluetooth control disabled.")

# Configuration Defaults
DEFAULT_CONFIG = {
    "LED_COUNT": 50,
    "LED_PIN": 18,
    "LED_FREQ_HZ": 800000,
    "LED_DMA": 10,
    "LED_BRIGHTNESS": 255,
    "LED_INVERT": False,
    "LED_CHANNEL": 0
}

CONFIG_FILE = "/home/pi/led_controller/config.json"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Animation Logic ---

class AnimationState:
    def __init__(self, strip):
        self.strip = strip
        self.mode = "off" # off, solid, rainbow, color_wipe, theater_chase, pulse
        self.color = Color(255, 0, 0) # Default Red
        self.brightness = 255
        self.running = True
        self._lock = threading.Lock()
        
        # internal counters
        self.step = 0
        self.last_update = 0
        self.previous_mode = "solid" # For toggling

    def set_mode(self, mode):
        with self._lock:
            if mode != "off":
                self.previous_mode = mode
            self.mode = mode
            self.step = 0
            logging.info(f"Mode set to: {mode}")

    def toggle(self):
        with self._lock:
            if self.mode == "off":
                self.mode = self.previous_mode
            else:
                self.previous_mode = self.mode
                self.mode = "off"
            logging.info(f"Toggled to: {self.mode}")

    def set_color(self, r, g, b):
        with self._lock:
            self.color = Color(r, g, b)
            if self.mode == "off":
                self.mode = "solid"
                self.previous_mode = "solid"
            # logging.info(f"Color set to: {r},{g},{b}") # Commented out to reduce spam from sliders/bluedot

    def set_brightness(self, brightness):
        with self._lock:
            self.strip.setBrightness(brightness)
            self.strip.show()
            self.brightness = brightness

    def update(self):
        """Called inside the main loop to update LED state based on mode."""
        now = time.time()
        
        with self._lock:
            if self.mode == "off":
                self._clear()
            
            elif self.mode == "solid":
                self._solid()
                
            elif self.mode == "rainbow":
                if now - self.last_update > 0.02:
                    self.step = (self.step + 1) % 256
                    self._rainbow_frame(self.step)
                    self.last_update = now
            
            elif self.mode == "color_wipe":
                 if now - self.last_update > 0.05:
                    self.step = (self.step + 1) % (self.strip.numPixels() + 1)
                    if self.step == 0:
                         self._clear()
                    else:
                        self.strip.setPixelColor(self.step - 1, self.color)
                        self.strip.show()
                    self.last_update = now
            
            elif self.mode == "theater_chase":
                if now - self.last_update > 0.1:
                    self.step = (self.step + 1) % 3
                    self._theater_chase_frame(self.step)
                    self.last_update = now
            
            elif self.mode == "pulse":
                if now - self.last_update > 0.02:
                    import math
                    intensity = int((math.sin(time.time() * 2) + 1) * 127.5)
                    self.strip.setBrightness(intensity)
                    self._solid()
                    self.last_update = now

    def _clear(self):
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, Color(0,0,0))
        self.strip.show()

    def _solid(self):
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, self.color)
        self.strip.show()

    def _rainbow_frame(self, j):
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, self._wheel((int(i * 256 / self.strip.numPixels()) + j) & 255))
        self.strip.show()

    def _theater_chase_frame(self, q):
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, 0)
        for i in range(0, self.strip.numPixels(), 3):
             if i + q < self.strip.numPixels():
                 self.strip.setPixelColor(i+q, self.color)
        self.strip.show()

    def _wheel(self, pos):
        if pos < 85:
            return Color(pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return Color(255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return Color(0, pos * 3, 255 - pos * 3)

# --- Globals ---
app = Flask(__name__)
anim_controller = None

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/color', methods=['POST'])
def set_color():
    data = request.json
    r = int(data.get('r', 0))
    g = int(data.get('g', 0))
    b = int(data.get('b', 0))
    anim_controller.set_color(r, g, b)
    anim_controller.set_mode('solid')
    return jsonify({"status": "ok"})

@app.route('/api/brightness', methods=['POST'])
def set_brightness():
    data = request.json
    b = int(data.get('brightness', 255))
    anim_controller.set_brightness(b)
    return jsonify({"status": "ok"})

@app.route('/api/pattern', methods=['POST'])
def set_pattern():
    data = request.json
    pattern = data.get('pattern', 'solid')
    anim_controller.set_mode(pattern)
    return jsonify({"status": "ok"})

# --- BlueDot Integration ---
def setup_bluedot(controller):
    if not BLUEDOT_AVAILABLE:
        return

    bd = BlueDot()
    
    def on_press(pos):
        # Top-center tap could be toggle? 
        # Actually standard BlueDot behavior is interaction.
        # Let's map positions.
        pass

    def on_release(pos):
        pass

    def on_move(pos):
        # pos.angle is 0-360. 
        # pos.distance is 0-1.
        # Map angle to Hue.
        hue = (pos.angle % 360) / 360.0
        # Saturation is distance? Or just full color?
        # Let's use full saturation for vivid LEDs.
        # Convert HSV to RGB
        r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
        # Scale to 255
        controller.set_color(int(r*255), int(g*255), int(b*255))
        if controller.mode != "solid":
            controller.set_mode("solid")

    def on_double_tap():
        # Cycle patterns
        modes = ["solid", "rainbow", "color_wipe", "theater_chase", "pulse"]
        try:
             current_idx = modes.index(controller.mode)
             next_mode = modes[(current_idx + 1) % len(modes)]
        except ValueError:
             next_mode = "solid"
        controller.set_mode(next_mode)
        
    def on_tap():
        # Toggle On/Off
        controller.toggle()

    bd.when_pressed = on_tap # Single tap to toggle? 
    # Waiting for double tap might be tricky with simple callbacks
    # BlueDot supports when_double_pressed
    bd.when_double_pressed = on_double_tap
    
    # Drag for color
    bd.when_moved = on_move
    
    logging.info("BlueDot Bluetooth interface initialized.")

# --- Main ---

def load_config(path):
    config = DEFAULT_CONFIG.copy()
    try:
        with open(path, 'r') as f:
            config.update(json.load(f))
    except Exception:
        pass
    return config

def main():
    global anim_controller
    
    # Signal handling
    def signal_handler(sig, frame):
        logging.info("Shutting down...")
        anim_controller.running = False
        anim_controller.set_mode("off")
        anim_controller.update() 
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    config = load_config(CONFIG_FILE)
    
    strip = PixelStrip(
        config["LED_COUNT"],
        config["LED_PIN"],
        config["LED_FREQ_HZ"],
        config["LED_DMA"],
        config["LED_INVERT"],
        config["LED_BRIGHTNESS"],
        config["LED_CHANNEL"]
    )
    
    try:
        strip.begin()
    except RuntimeError:
        logging.error("Could not initialize LEDs. Run as root.")
        sys.exit(1)

    anim_controller = AnimationState(strip)

    # Setup Bluetooth
    if BLUEDOT_AVAILABLE:
        setup_bluedot(anim_controller)

    # Start Flask
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False))
    flask_thread.daemon = True
    flask_thread.start()
    
    logging.info("Web Server started on port 5000")
    logging.info("Starting Animation Loop...")

    while True:
        try:
            anim_controller.update()
            time.sleep(0.01)
        except KeyboardInterrupt:
            signal_handler(None, None)

if __name__ == '__main__':
    main()
