import picamera
from gpiozero import MotionSensor, PWMLED
from time import sleep

# ultrasonic sensor testing
# from gpiozero import DistanceSensor
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep

# pigpio = PiGPIOFactory()

# print("Creating distance sensor...")
# us = DistanceSensor(echo=24, trigger=23, max_distance=4, threshold_distance=1.75)
# us_threshold = 2.0

led = PWMLED(17)

'''
while True:
    print('Distance: {}'.format(us.distance))
    sleep(0.05)
'''

camera = picamera.PiCamera()
camera.resolution = (1640, 922)
camera.brightness = 0

# set up motion sensor connection to pin 3, gpio2
print("Creating PIR sensor")
pir = MotionSensor(4)
camera.start_recording("big_record.h264")
camera.annotate_text_size = 64
camera.annotate_background = True
vid_count = 0
while vid_count < 3:
        camera.brightness = 0
        camera.annotate_text = "not currently recording..."
        print("Test number {}, waiting for signal from motion sensor...".format(vid_count+1))
        # print('Distance: {}'.format(us.distance))
        sleep(0.5)
        pir.wait_for_motion()
        # print('Distance: {}'.format(us.distance))
        # if us.distance < us_threshold:
        print("MOTION DETECTED, recording STARTED for 5 seconds")
        led.value = 1
        camera.brightness = 50
        # camera.start_recording("record_{}.h264".format(i))
        camera.annotate_text = "record_{}.h264".format(vid_count+1)
        for sec in range(1,6):
            print("{}...".format(sec))
            camera.wait_recording(1)
        # camera.stop_recording()
        print("recording STOPPED, saved to record_{}.h264".format(vid_count+1))
        sleep(3)
        vid_count += 1
        led.off()
camera.stop_recording()
