# record a 5 second clip on PIR signal and use MOG2 to grab the moving object
import picamera
from gpiozero import MotionSensor
import cv2 as cv
import numpy as np
import time

'''
analyze to see where the peak is
record it as youre analyzing it
jpeg it at full res as youre
ping pong buffer of images and overwrite the old one
two buffers and decide which one youre gonna overwrite each time and analyze
each time by each MOG

'''

SUBTYPE = "MOG2"

if SUBTYPE == "MOG2":
    # create an MOG2 background subtractor
    backSub = cv.createBackgroundSubtractorMOG2()
else:
    backSub = cv.createBackgroundSubtractorKNN()

# set up motion sensor connection to pin 3, gpio2
pir = MotionSensor(4)
# raspberry pi camera
camera = picamera.PiCamera(framerate=10)
# set resolution and brightness
camera.resolution = (1640, 922)
camera.brightness = 60

# wait for motion
print()
print("Waiting for motion capture...")
pir.wait_for_motion()

# received motion
print()
print("MOTION DETECTED")

print()
print("Video recording started...")
# start recording using pi camera
camera.start_recording('demo.h264')

# wait for video to record
camera.wait_recording(10)

# stop recording
camera.stop_recording()
camera.close()
print()
print("Video recording stopped...")

######

capture = cv.VideoCapture("demo.h264")

# get a running max of the highest activation (most white pixels)
maxFrame  = None
maxPixels = 0
frameNum  = 1

print()
print("Analyzing video...")

start_time = time.time()

# TODO optimize algorithm
# don't save capture as h264 and just use the processed frames? throw them out after?
# record for less amount of time
# record less frames per second?
# anything to reduce amount of processed frames, really

while True:
    print("Frame {}".format(frameNum))

    ret, frame = capture.read()
    if frame is None:
        break

    fgMask = backSub.apply(frame)

    currPixels = np.sum(fgMask // 255.0)
    if currPixels > maxPixels:
        maxPixels = currPixels
        maxMask   = fgMask
        maxFrame  = frame

    frameNum += 1

exec_time = time.time() - start_time

print()
print("Execution time: {}".format(exec_time))

cv.imwrite("maxframe.jpeg", maxFrame)
cv.imwrite("maxmask.jpeg", maxMask)

print()
print("Object saved to maxframe.jpeg")
print("Mask saved to maxmask.jpeg")
