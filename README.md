# timer-lamp
Lamp using a rotary encoder and individually addressable LEDs to set a timer and color of the light.

This project uses circuitpython, object-oriented programming, and asyncio to create the lamp. It was half learning exercise and half makeing something cool for my kids :) I originally put it inside a hollow moon lithophane, but it could be in anything that glows.

Requirements:
- Circuitpython on a microcontroller
- asyncio and neopixel libraries from Adafruit

Hardware:
- neopixel strip or ring wired to PIXELS_PIN
- roatary encoder wired to the three encoder pins
    - BUTTON_PIN
    - ENCODER_PIN_DT
    - ENCODER_PIN_CLK
NOTE: You can change the pins around to suit your micro and needs, but the DT/CLK pins need to be consecutive.

Installation:
- copy code.py to the micro and save.
