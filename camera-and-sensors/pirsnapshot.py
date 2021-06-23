import picamera
from gpiozero import MotionSensor
from time import sleep

# set up motion sensor connection to pin 3, gpio2
pir = MotionSensor(4)
# raspberry pi camera
camera = picamera.PiCamera()
#set resolution and brightness
camera.resolution = (1640, 922)
camera.brightness = 70

for i in range(3):
    print("Test number {}".format(i+1))
    pir.wait_for_motion()
    print("MOTION DETECTED HELP")

    # motion detected past this point
    camera.start_preview()
    #add text on image
    camera.annotate_text = 'Image Number {}'.format(i+1)
    #store image
    camera.capture('/home/pi/Desktop/image_{}.jpeg'.format(i+1))
    camera.stop_preview()
    sleep(3)
