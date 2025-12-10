#!/usr/bin/env python3
import time
from rpi_ws281x import PixelStrip, Color
import argparse

# LED strip configuration:
LED_COUNT = 50        # Number of LED pixels.
LED_PIN = 18          # GPIO pin led is connected to.
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)

if __name__ == '__main__':
    print("Initializing LED strip...")
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    try:
        strip.begin()
        print("LED strip initialized!")
    except RuntimeError as e:
        print(f"Error: {e}")
        print("Make sure you are running as root (sudo).")
        exit(1)

    try:
        print("Color Wipe: Red")
        colorWipe(strip, Color(255, 0, 0))
        print("Color Wipe: Green")
        colorWipe(strip, Color(0, 255, 0))
        print("Color Wipe: Blue")
        colorWipe(strip, Color(0, 0, 255))
        print("Clearing...")
        colorWipe(strip, Color(0,0,0), 10)
    except KeyboardInterrupt:
        colorWipe(strip, Color(0,0,0), 10)
