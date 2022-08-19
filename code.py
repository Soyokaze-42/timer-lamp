"""
This Is a neopixel timer-lamp written with circuitpython.

When it is powered on, it pulses. each click in the encoder adds 5 seconds to the timer.
Once the button is pressed, the timer starts. Then pushing the button changes the color that will be changed when the
encoder is turned, briefly flashing that color after the button has been pressed.

Use a rotary encoder for BUTTON_PIN and the two ENCODER_PINs.
Use neopixels on pin PIXELS_PIN with count PIXELS_COUNT.
"""

import asyncio
import board
import alarm
import time
import countio
import rotaryio
import digitalio
import neopixel

PIXELS_PIN = board.D8
PIXELS_COUNT = 7

BUTTON_PIN = board.D7
ENCODER_PIN_DT = board.D10
ENCODER_PIN_CLK = board.D9
ENCODER_DIVISOR = 2  # Depends on the encoder used


class lamp:
    "Lamp-timer with asyncio"

    def __init__(self):
        """lamp init

        Vars:
            rgb (list): three ints, [R,G,B] used to change the color of the lamp
            brightness (float): the brightness of the lamp (between 0 and 1)
            current_color (int): the color that will change when the encoder is turned 0=R 1=G 2=B
            turn_off_time (int): number of seconds on the micro clock when the light should turn off (and sleep)
            timeout (int): number of seconds on the micro clock to stop looking for input to set the timer
            countdown (bool): True if the timer has started
            exit (bool): True if the timer is done and the program should sleep
        """
        self.rgb = [10, 10, 10]
        self.brightness = 1
        self.current_color = 0
        self.turn_off_time = time.monotonic()
        self.timeout = time.monotonic() + 30
        self.countdown = False
        self.exit = False

        print(self.timeout, self.countdown)

    async def update_color(self, delta):
        """Update the current color (self.rgb) by delta without going under 0 or over 255.

        Args:
            delta (int): the size and direction of the change in color.
        """
        if 0 <= self.rgb[self.current_color] + delta <= 255:
            self.rgb[self.current_color] += delta
        elif 0 > self.rgb[self.current_color] + delta:
            self.rgb[self.current_color] = 0
        else:
            self.rgb[self.current_color] = 255

    async def update_neopixels(self):
        """Keep the neopixels the correct color and brightness.
        Constantly runs until the program needs to sleep.
        """
        old_color = 0
        with neopixel.NeoPixel(PIXELS_PIN, PIXELS_COUNT, auto_write=True) as neopixels:
            while not self.exit:
                # Update color and brightness
                if old_color == self.current_color:
                    neopixels.brightness = self.brightness
                    neopixels.fill(self.rgb)
                    await asyncio.sleep(0.04)
                else:
                    # Blink the color to edit
                    neopixels.brightness = self.brightness
                    old_color = self.current_color
                    color = [0, 0, 0]
                    color[self.current_color] = 20
                    neopixels.fill((0, 0, 0))
                    neopixels.fill(color)
                    await asyncio.sleep(0.5)
            # Turn light off when the program sleeps
            neopixels.brightness = 0
        print("Cleaned up neopixels")

    async def catch_button_interrupts(self):
        """Constant loop to deal with button presses on the encoder"""
        with countio.Counter(
            BUTTON_PIN, edge=countio.Edge.RISE, pull=digitalio.Pull.UP
        ) as interrupt:
            current_count = 0

            while not interrupt.count:
                # Pulse white lights until the button is pressed
                self.brightness = abs(time.monotonic() % 1 - 0.5) * 2
                await asyncio.sleep(0.04)
                if time.monotonic() > self.timeout:
                    break

            # start the counter and set brightness to 1 after the button has been pressed
            self.countdown = True
            self.brightness = 1

            while time.monotonic() < self.turn_off_time:
                # while the timer is counting down
                # check if the the button has been pressed and change the current color if so.
                if current_count < interrupt.count:
                    self.current_color = interrupt.count % 3
                    print("New color", self.current_color)
                    current_count = interrupt.count

                await asyncio.sleep(0.04)
        # When the timer is finished, trigger the program shutdown
        self.exit = True

    async def catch_encoder_interrupts(self):
        """constant loop to track changes in the encoder"""
        with rotaryio.IncrementalEncoder(
            ENCODER_PIN_CLK, ENCODER_PIN_DT, divisor=ENCODER_DIVISOR
        ) as encoder:
            while self.countdown == False:
                # until the countdown starts, the encoder changes the timer length
                self.turn_off_time = self.timeout + 5 * encoder.position
                await asyncio.sleep(0.04)

            # set the timer
            self.turn_off_time = time.monotonic() + 5 * encoder.position
            print("Timer set for {} seconds".format(5 * encoder.position))
            encoder.position = 0

            while not self.exit:
                # update the color of the lamp
                if encoder.position != 0:
                    await self.update_color((encoder.position) * 3)
                    print(self.rgb)
                    encoder.position = 0
                await asyncio.sleep(0.04)
        print("Cleaned up encoder")

    def run(self):
        asyncio.run(
            asyncio.gather(
                *(
                    self.catch_button_interrupts(),
                    self.catch_encoder_interrupts(),
                    self.update_neopixels(),
                )
            )
        )
        # deep sleep and set an alarm on the rotary encoder button on exit
        pin_alarm = alarm.pin.PinAlarm(BUTTON_PIN, value=False, pull=digitalio.Pull.UP)
        alarm.exit_and_deep_sleep_until_alarms(pin_alarm)


if __name__ == "__main__":
    print(f"Alarm wake up: {alarm.wake_alarm}")
    lamp().run()
