import cv2 as cv
import numpy as np
import time

subType       = "MOG2"
TOO_CLOSE_CAP = 90000

if subType == "MOG2":
    # create an MOG2 background subtractor
    backSub = cv.createBackgroundSubtractorMOG2()
else:
    backSub = cv.bgsegm.createBackgroundSubtractorCNT()

capture = cv.VideoCapture("../../walking.h264")

'''
analyze to see where the peak is
record it as youre analyzing it
jpeg it at full res as youre
ping pong buffer of images and overwrite the old one
two buffers and decide which one youre gonna overwrite each time and analyze
each time by each MOG

rc.local
.bashrc
init.d
SysV
systemd
crontab
'''

'''
alg to try
- search until white pixel in middle of mask
- start loop that searches for increase in white pixels
- once white pixels decrease exit loop and output image
'''

# get a running max of the highest activation (most white pixels)
maxFrame    = None
maxFrame_sm = None
maxMask     = None
maxFrameNum = 0
maxPixels   = 0
frameNum    = 1

print()
print("Analyzing video...")

start_time = time.time()

while True:

    ret, frame = capture.read()
    if frame is None:
        break

    # height x width x color
    hgt, wid, layers = frame.shape
    # print(hgt//4,wid//4)

    # downscale the frame for faster processing
    resize_wid = wid // 4
    resize_hgt = hgt // 4
    frame_resize = cv.resize(frame, (resize_wid, resize_hgt))
    mid_col = resize_wid // 2
    mid_row = resize_hgt // 2

    fgMask = backSub.apply(frame_resize)

    '''
    cv.rectangle(frame, (10, 2), (100,20), (255,255,255), -1)
    cv.putText(frame, str(capture.get(cv.CAP_PROP_POS_FRAMES)), (15, 15),
               cv.FONT_HERSHEY_SIMPLEX, 0.5 , (0,0,0))

    cv.imshow('Frame', frame)
    cv.imshow('FG Mask', fgMask)

    keyboard = cv.waitKey(30)
    if keyboard == 'q' or keyboard == 27:
        break
    '''

    # Check if frame is worth checking out
    if fgMask[mid_row][mid_col] == 255.0:
        # Find amount of white pixels
        currPixels = np.sum(fgMask // 255.0)

        # If we have new maximum within reason
        if maxPixels < currPixels <= TOO_CLOSE_CAP:
            maxFrameNum = frameNum
            maxPixels = currPixels
            maxMask   = fgMask
            maxFrame  = frame
            maxFrame_sm = frame_resize
            print("Frame {}: score - {}".format(frameNum, currPixels))
        elif currPixels < maxPixels: # No more maxing
            # break
            pass

    frameNum += 1

exec_time = time.time() - start_time

print()
print("Execution time: {}".format(exec_time))

print("Max frame: {}".format(maxFrameNum))
cv.imwrite("maxframe.jpeg", maxFrame)
cv.imwrite("maxmask.jpeg", maxMask)
# cv.imwrite("maxframe_sm.jpeg", maxFrame_sm)
# print(maxPixels)

print()
print("Object saved to maxframe.jpeg")
print("Mask saved to maxmask.jpeg")
