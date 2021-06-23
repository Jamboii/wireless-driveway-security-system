import io
import picamera
import picamera.array
import time
import cv2 as cv
import numpy as np
import threading

# TODO output frame at original resolution
# TODO process frames using threading so framerate isn't artificially slowed
# TODO only stream for 10 seconds
# TODO make backgroundSubtractor "train" for 15 frames without those frames being processed
# TODO make a class structure out of all of this so it aint as messy
# TODO integrate with PIR sensor

# TODO rework alg, what if something comes into frame and then stays there for a bit, or even walks closer to camera module?

RES_WID = 1640
RES_HGT = 922
TOO_CLOSE_CAP = 90000

backSub = cv.bgsegm.createBackgroundSubtractorCNT()

print()
print("Starting camera...")

def process(stream, maxPixels, maxFrame, maxMask):
    process_start = time.time()

    data    = np.frombuffer(stream.getvalue(), dtype=np.uint8)
    frame   = cv.imdecode(data, 1)

    hgt, wid, layers = frame.shape
    mid_col = wid // 2
    mid_row = hgt // 2

    fgMask = backSub.apply(frame)

    print("frame exec: {}".format(time.time() - process_start))

    # Check if frame is worth checking out aka does an object reach the middle of frame
    if fgMask[mid_row][mid_col] == 255.0:
        # Find amount of white pixels
        currPixels = np.sum(fgMask // 255.0)

        print(currPixels)

        # If we have new maximum within reason
        if maxPixels < currPixels <= TOO_CLOSE_CAP:
            # maxFrameNum = frameNum
            maxPixels = currPixels
            maxMask   = fgMask
            maxFrame  = frame
            # maxFrame_sm = frame_resize
            # print("Frame {}: score - {}".format(frameNum, currPixels))
        elif currPixels < maxPixels: # No more maxing
            return True, maxPixels, maxFrame, maxMask # max found, stop streaming

    return False, maxPixels, maxFrame, maxMask # keep streaming

with picamera.PiCamera(resolution=(RES_WID,RES_HGT),framerate=10) as camera:
    maxPixels = 0
    maxFrame  = None
    maxMask   = None

    start_time = time.time()

    # camera.shutter_speed    = camera.exposure_speed
    # camera.exposure_mode    = 'off'
    # g                       = camera.awb_gains
    # camera.awb_mode         = 'off'
    # camera.awb_gains        = g

    stream = io.BytesIO()
    for foo in camera.capture_continuous(stream, format='jpeg', resize=(RES_WID//4,RES_HGT//4)):
        # Truncate the stream to the current position (in case
        # prior iterations output a longer image)
        stream.truncate()
        stream.seek(0)

        maxFound, maxPixels, maxFrame, maxMask = process(stream, maxPixels, maxFrame, maxMask)
        if maxFound:
            break

    exec_time = time.time() - start_time

    print()
    print("Execution time: {}".format(exec_time))

    cv.imwrite("maxframe.jpeg", maxFrame)
    cv.imwrite("maxmask.jpeg", maxMask)

    print()
    print("Object saved to maxframe.jpeg")
    print("Mask saved to maxmask.jpeg")
