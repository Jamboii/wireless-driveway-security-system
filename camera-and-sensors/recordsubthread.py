import io
import picamera
import picamera.array
import time
import datetime
import cv2 as cv
import numpy as np
import threading
import os

import serial
import RPi.GPIO as GPIO

from gpiozero import MotionSensor, PWMLED
from filelock import FileLock

# TODO output frame at original resolution ----REALLY HARD RN TO UPSCALE/CAPTURE AT FULL RES

# TODO integrate interrupts ---- may not be possible, micropython maybe?
# TODO rework alg, what if something comes into frame and then stays there for a bit, or even walks closer to camera module?

FPS           = 13
REC_TIME      = 10
RES_WID       = 1640
RES_HGT       = 922
# RESIZE_WID    = RES_WID // 4
# RESIZE_HGT    = RES_HGT // 4
TOO_CLOSE_CAP = 90000

LIDAR_THRESH = 700
BOUND_RATIO = 20

sense = 'lidar'

img_dir   = "/home/pi/wireless-driveway-security/img_output/"
mask_dir  = "/home/pi/wireless-driveway-security/mask_output/"
img_count = 0

filelock_maxframes = "/home/pi/wireless-driveway-security/integration/maxframes.txt"
filelock_pings     = "/home/pi/wireless-driveway-security/integration/pings.txt"

led = PWMLED(17)

ser = serial.Serial("/dev/ttyUSB0", 115200)

# backSub = cv.bgsegm.createBackgroundSubtractorCNT(FPS, True, (FPS)*60)
backSub = cv.createBackgroundSubtractorMOG2()

camera = picamera.PiCamera(resolution=(RES_WID,RES_HGT), framerate=FPS)

print()
print("Starting camera...")

class ImageProcessor(threading.Thread):
    def __init__(self, owner):
        super(ImageProcessor, self).__init__()
        self.stream = io.BytesIO()
        self.event = threading.Event()
        self.terminated = False
        self.owner = owner
        self.start()
        print("Image Processor Created")

    def run(self):
        # This method runs in a separate thread
        print("RUN")
        while not self.terminated:
            # Wait for an image to be written to the stream
            if self.event.wait(1):
                try:
                    self.stream.seek(0)
                    # Read the image and do some processing on it
                    data  = np.frombuffer(self.stream.getvalue(), dtype=np.uint8)
                    frame = cv.imdecode(data, 1)
                    # frame_resize = cv.resize(frame, (RESIZE_WID,RESIZE_HGT))

                    # Increase Frame Number
                    print("Frame {}".format(self.owner.frameNum))
                    self.owner.frameNum += 1

                    # Check if time for recording is up and we need to exit threads
                    if self.owner.frameNum > (FPS*REC_TIME):
                        print("TOOK TOO LONG, DONE")
                        self.owner.done = True

                    # Create mask
                    hgt, wid, layers = frame.shape
                    # hgt = RESIZE_HGT
                    # wid = RESIZE_WID
                    fgMask = backSub.apply(frame)

                    # Find midpoint of frame
                    mid_col = wid // 2
                    mid_row = hgt // 2
                    rad_col = wid // BOUND_RATIO
                    rad_row = hgt // BOUND_RATIO

                    row_low  = mid_row - rad_row
                    row_high = mid_row + rad_row + 1
                    col_low  = mid_col - rad_col
                    col_high = mid_col + rad_col + 1
                    # if fgMask[mid_row][mid_col] == 255.0 and self.owner.frameNum > FPS*1.5:
                    if fgMask[row_low:row_high,col_low:col_high].any() and self.owner.frameNum > FPS*1.5:
                        currPixels = np.sum(fgMask // 255.0)
                        print(currPixels)
                        if currPixels > self.owner.maxPixels and currPixels <= TOO_CLOSE_CAP:
                            print("CONTINUE")
                            self.owner.maxPixels = currPixels
                            self.owner.maxFrame  = frame
                            self.owner.maxMask   = fgMask
                        elif currPixels <= self.owner.maxPixels:
                            print("DONE NOW")
                            # cap_time = time.time()
                            # self.owner.maxFrame = camera.capture(self.stream, format='jpeg', use_video_port=True)
                            # print("Capture time: {}".format(time.time() - cap_time))
                            self.owner.done = True
                    # print(self.terminated)
                finally:
                    # Reset the stream and event
                    self.stream.seek(0)
                    self.stream.truncate()
                    self.event.clear()
                    # Return ourselves to the available pool
                    with self.owner.lock:
                        # print("Returning ourselves to available pool")
                        self.owner.pool.append(self)

class ProcessOutput(object):
    def __init__(self, maxPixels, maxFrame, maxMask):
        self.done = False
        # Variables to return
        self.maxPixels = maxPixels
        self.maxFrame  = maxFrame
        self.maxMask   = maxMask
        self.frameNum  = 1
        # Construct a pool of 4 image processors along with a lock
        # to control access between threads
        self.lock = threading.Lock()
        self.pool = [ImageProcessor(self) for i in range(4)]
        self.processor = None

    def write(self, buf):
        print()
        print("WRITE")
        if buf.startswith(b'\xff\xd8'):
            # New frame; set the current processor going and grab
            # a spare one
            if self.processor:
                self.processor.event.set()
            with self.lock:
                if self.pool:
                    self.processor = self.pool.pop()
                    print(self.processor)
                else:
                    # No processor's available, we'll have to skip this frame
                    print("Frame skipped sorry")
                    self.processor = None
        if self.processor:
            # print("Writing buffer")
            self.processor.stream.write(buf)

    def flush(self):
        # When told to flush (this indicates end of recording), shut
        # down in an orderly fashion. First, add the current processor
        # back to the pool

        # Take a picture to commemorate the moment first
        # start_cap = time.time()
        # camera.capture('maxframe_another.jpeg', use_video_port=True)
        # print("Capture Time: {}".format(time.time()-start_cap))
        time.sleep(0.5)
        print("FLUSH")
        if self.processor:
            print("Processor is not None, appending processor to pool and setting to None...")
            with self.lock:
                print("Processor: {}".format(self.processor))
                self.pool.append(self.processor)
                self.processor = None

        print(self.pool)
        assert(len(self.pool) == 4)
        for proc in self.pool:
            print("Terminating {}...".format(proc))
            proc.terminated = True
        for proc in self.pool:
            print("Joining {}/Terminated:{}...".format(proc,proc.terminated))
            proc.join()
        print("Flush is leaving now")

################################################

def get_imgcount():
    filemax = 0
    for file in os.listdir(img_dir):
        if file.endswith(".jpeg") and "maxframe" in file:
            filemax = max(int(file.split("_")[1][:-5])+1,filemax)
    print(filemax)
    return filemax

def run_detection():
    output = ProcessOutput(0, np.array([]), np.array([]))

    start_time = time.time()

    # camera.start_recording('highres.h264')
    camera.start_recording(output, format='mjpeg', resize=(RES_WID//4,RES_HGT//4))
    while not output.done:
        camera.wait_recording(1)
    camera.stop_recording()

    exec_time = time.time() - start_time

    print()
    print("Execution time: {}".format(exec_time))

    print()
    print("Max pixels: {}".format(output.maxPixels))

    if output.maxFrame.any() and output.maxMask.any():
        # cv.imwrite(img_dir  + "maxframe_{}.jpeg".format(img_count), output.maxFrame)
        # cv.imwrite(mask_dir + "maxmask_{}.jpeg".format(img_count),  output.maxMask)
        img_count = get_imgcount()

        # write some stuff to our lock
        with FileLock(filelock_maxframes+".lock"):
            print("Lock acquired.")
            print()
            with open(filelock_maxframes,"a") as f:
                print("{} opened.".format(filelock_maxframes))

                # write new command to the text file
                # format: MAXFRAME NUM = {COMMAND, INDEX NUMBER}
                # where the index number signifies the amount of times this command has been written
                f.write("MAXFRAME {}\n".format(img_count))

                # write our maxframe image and mask out to our directories
                cv.imwrite(img_dir  + "maxframe_{}.jpeg".format(img_count), output.maxFrame)
                cv.imwrite(mask_dir + "maxmask_{}.jpeg".format(img_count),  output.maxMask)

                # increment image count
                img_count += 1

        time.sleep(0.05)

        print()
        print("Object saved to maxframe.jpeg")
        print("Mask saved to maxmask.jpeg")
    else:
        print()
        print("Time up, no image written")
        # TODO maybe force this back to motion_sense()
        # motion_sense()
        '''
        if sense == "pir":
            motion_sense()
        else:
            lidar_sense()
        '''
    print(output.pool)
    print(output.processor)
    # motion_sense()
    return

#################################################

def motion_sense():
    # Set Motion Sensor to GPIO 4
    pir = MotionSensor(27, threshold=0.99)

    # print()
    # print("Setting up motion sensor...")
    # time.sleep(45)

    print()
    print("Waiting for motion capture...")
    time.sleep(1)
    # pir.wait_for_motion()

    img_count = get_imgcount()

    while True:
        print("waiting, gonna check for pings in the meantime...")
        with FileLock(filelock_pings + ".lock"):
            print("Lock acquired.")
            print()

            # open up our text file which will process any command written to it
            f = open(filelock_pings)
            print("{} opened.".format(filelock_pings))

            # read in and spit out all lines in the text file
            lines = f.readlines()
            print("LINES IN PING FILE: {}".format(lines))

            # if our text file has commands to process in it
            if len(lines) >= 1:
                # look at the first line only and dick around with it
                cmd_num = lines[0].split()
                print("LINE ARGS: {}".format(cmd_num))

                # cmd_num should be split into a "cmd" portion and "num" portion
                if len(cmd_num) == 2:
                    cmd = cmd_num[0]
                    num = cmd_num[1]
                else:
                    cmd = ""
                    num = ""
                    print("COMMAND IS INVALID, PASSING...")
            else:
                cmd = ""
                num = ""
                print("TEXT FILE IS EMPTY, PASSING...")

            if cmd == "PING":
                # it's time to create an image to output
                try:
                    # WRITE AGAIN TO MAXFRAME
                    with FileLock(filelock_maxframes + ".lock"):
                        print("Lock acquired - maxframes ping snapshot")
                        print()
                        with open(filelock_maxframes,"a") as f_max:
                            print("{} opened - ping writing.".format(filelock_maxframes))
                            f_max.write("MAXFRAME {}\n".format(img_count))
                            camera.capture(img_dir + "maxframe_{}.jpeg".format(img_count),resize=(RES_WID//4,RES_HGT//4))
                            img_count += 1
                    time.sleep(0.05)
                    # ENDING WRITE TO MAXFRAME
                except:
                    print("can't take an image right now lol")

                lines.pop(0)
                print(lines)

            f.close()
            # open the file again to rewrite our new lines (lines[1:])
            with open(filelock_pings,"w+") as f:
                for line in lines:
                    f.write(line)

        time.sleep(0.05)

        if pir.motion_detected:
            print()
            print("PIR MOTION DETECTED")

            pir.close()
            # extra sleep for humans to process whats happening
            time.sleep(2)
            # run_detection()
            # lidar_sense()
            return True

def lidar_sense():
    print("Waiting for LIDAR capture...")
    time.sleep(0.05)
    start_time = time.time()
    while True:
        #time.sleep(0.1)
        count = ser.in_waiting
        # print(count)
        if count > 8:
            recv = ser.read(9)
            ser.reset_input_buffer()
            # type(recv), 'str' in python2(recv[0] = 'Y'), 'bytes' in python3(recv[0] = 89)
            # type(recv[0]), 'str' in python2, 'int' in python3

            if recv[0] == 0x59 and recv[1] == 0x59:     #python3
                distance = recv[2] + recv[3] * 256
                strength = recv[4] + recv[5] * 256
                print('(', distance, ',', strength, ')')
                ser.reset_input_buffer()
                if distance < LIDAR_THRESH:
                    print("LIDAR MOTION DETECTED")
                    led.value = 1
                    # run_detection()
                    # break
                    return True

            exec_time = time.time() - start_time
            if (exec_time >= 10):
                print("NO LIDAR MOTION, RECHECKING PIR")
                # motion_sense()
                # break
                return False

            if recv[0] == 'Y' and recv[1] == 'Y':     #python2
                lowD = int(recv[2].encode('hex'), 16)
                highD = int(recv[3].encode('hex'), 16)
                lowS = int(recv[4].encode('hex'), 16)
                highS = int(recv[5].encode('hex'), 16)
                distance = lowD + highD * 256
                strength = lowS + highS * 256
                print(distance, strength)

if __name__ == "__main__":

    img_count = get_imgcount()

    '''
    if sense == "pir":
       motion_sense()
    else:
        try:
            if ser.is_open == False:
                ser.open()
            motion_sense()
        except KeyboardInterrupt:   # Ctrl+C
            if ser != None:
                ser.close()
    '''
    try:
        if ser.is_open == False:
            ser.open()
        '''
        while True:
            # check for motion from the PIR
            motion_check = motion_sense()
            if motion_check:
                # check the LIDAR if theres motion from the PIR
                # if theres nothing from lidar go back to PIR detection
                lidar_check = lidar_sense()
                if lidar_check:
                    # run detection sequence if theres detection from the LIDAR
                    run_detection()
        '''
        while True:
            run_detection()
    except KeyboardInterrupt: # CTRL+C
        if ser != None:
            ser.close()
