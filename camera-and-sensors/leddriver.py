from gpiozero import PWMLED
from time import sleep
from signal import pause

led = PWMLED(17)
# led_again = PWMLED(27)

def offon():
    while True:
        led.value = 0
        sleep(1)
        led.value = 0.5
        sleep(1)
        led.value = 1
        sleep(1)

def on():
    while True:
        led.value = 1
        # led_again.value = 1

def pulse():
    led.pulse()
    pause()

# offon()
# pulse()
# led.value = 0.9
on()
