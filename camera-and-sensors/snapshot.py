import picamera
from gpiozero import PWMLED
from time import sleep
from fractions import Fraction

RES_WID = 1640
RES_HGT = 922
FPS = 13

TIMER = 3

led = PWMLED(17)
#create object for PiCamera class
'''
camera = picamera.PiCamera(
    resolution=(1280,720),
    framerate=Fraction(1,6),
    sensor_mode=3)
camera.shutter_speed = 6000000
camera.iso = 800
print("initializing camera")
sleep(30)
camera.exposure_mode = 'off'
'''
'''
camera = picamera.PiCamera()
print("video recording started")
camera.start_recording("/home/pi/newdemo.h264")
camera.wait_recording(15)
camera.stop_recording()
camera.close()
'''
# camera.capture('/home/pi/dark.jpg')

led.value = 1
camera = picamera.PiCamera(resolution=(RES_WID//4,RES_HGT//4), framerate=FPS)
#set resolution
# camera.resolution = (1640, 922)
# camera.framerate = Fraction(1,6)
camera.brightness = 50
# camera.start_preview(alpha=200)
#add text on image
# camera.annotate_text = 'Existence is pain.'
print("Sleeping for {} seconds.".format(TIMER))
for i in range(TIMER):
    print("{}...".format(i+1))
#store image
camera.capture('sarahimage.jpeg')
# camera.stop_preview()
print("Image saved to /home/pi/sarahimage.jpeg")
