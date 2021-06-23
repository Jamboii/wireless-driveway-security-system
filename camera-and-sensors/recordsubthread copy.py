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

FPS           = 13
REC_TIME      = 10
RES_WID       = 1640
RES_HGT       = 922
# RESIZE_WID    = RES_WID // 4
# RESIZE_HGT    = RES_HGT // 4
TOO_CLOSE_CAP = 90000

backSub = cv.bgsegm.createBackgroundSubtractorCNT()

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

    def run(self):
        # This method runs in a separate thread
        while not self.terminated:
            # Wait for an image to be written to the stream
            if self.event.wait(1):
                try:
                    self.stream.seek(0)
                    # Read the image and do some processing on it
                    #Image.open(self.stream)
                    #...
                    #...
                    # Set done to True if you want the script to terminate
                    # at some point
                    # print("We runnin")
                    # self.owner.done = self.process()
                    self.owner.done = True
                    print(self.terminated)
                finally:
                    # Reset the stream and event
                    self.stream.seek(0)
                    self.stream.truncate()
                    self.event.clear()
                    # Return ourselves to the available pool
                    with self.owner.lock:
                        self.owner.pool.append(self)

    def process(self):

        # recursive filter
        # IIR filter
        # double lowpass_frame[hgt][wid][3]
        # do an IIR filter
        # y[n] = alpha*y[n-1] + (1-alpha) * u[n]
        # lowpass_frame = alpha*lowpass_frame + (1-alpha)*current_frame
        # make alpha = 0.99 or 0.999, get a time constant of about 100 frames. i.e. roughly 100 frame averages

        # over center, and over whole area of the picture
        # sum_of_sqs_ctr = 0
        # sum_of_sqs_whole = 0
        # // separate loops for center
        # for (v= ..)
        #   for (h = )
        #       {
        #           sum_of_sqs += (current_pix[v][h] - lowpass_frame[v][h])^2
        # // divide by number of pixels considered
        # find typical high pass filter, change in current frame from long-term average

        # when sum_sqs_center > threshold, declare object moved to center

        process_start = time.time()

        data    = np.frombuffer(self.stream.getvalue(), dtype=np.uint8)
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
            if self.owner.maxPixels < currPixels <= TOO_CLOSE_CAP:
                # maxFrameNum = frameNum
                self.owner.maxPixels = currPixels
                self.owner.maxMask   = fgMask
                self.owner.maxFrame  = frame
                # maxFrame_sm = frame_resize
                # print("Frame {}: score - {}".format(frameNum, currPixels))
                print("Frame score: {}\tMax Frame: {}".format(currPixels, maxPixels))
            elif currPixels < self.owner.maxPixels: # No more maxing
                return True # max found, stop streaming

        return False # max not found yet, keep streaming

class ProcessOutput(object):
    def __init__(self, maxPixels, maxFrame, maxMask):
        self.done = False
        # Variables to return
        self.maxPixels = maxPixels
        self.maxFrame  = maxFrame
        self.maxMask   = maxMask
        # Construct a pool of 4 image processors along with a lock
        # to control access between threads
        self.lock = threading.Lock()
        self.pool = [ImageProcessor(self) for i in range(4)]
        self.processor = None

    def write(self, buf):
        print("WRITE")
        if buf.startswith(b'\xff\xd8'):
            # New frame; set the current processor going and grab
            # a spare one
            if self.processor:
                self.processor.event.set()
            with self.lock:
                if self.pool:
                    self.processor = self.pool.pop()
                else:
                    # No processor's available, we'll have to skip
                    # this frame; you may want to print a warning
                    # here to see whether you hit this case
                    print("Frame skipped sorry")
                    self.processor = None
        if self.processor:
            self.processor.stream.write(buf)

    def flush(self):
        # When told to flush (this indicates end of recording), shut
        # down in an orderly fashion. First, add the current processor
        # back to the pool
        print("FLUSH")
        if self.processor:
            print("Processor is not None, appending processor to pool and setting to None...")
            with self.lock:
                self.pool.append(self.processor)
                self.processor = None
        # Now, empty the pool, joining each thread as we go
        while True:
            print("Emptying the pool and joining each thread")
            with self.lock:
                try:
                    print("Popping process from pool")
                    proc = self.pool.pop()
                except IndexError:
                    print("Uh oh IndexError the pool is actually empty")
                    break
                    pass # pool is empty
            proc.terminated = True
            print("Joining process")
            proc.join()

'''
with picamera.PiCamera(resolution=(RES_WID,RES_HGT),framerate=10) as camera:
    maxPixels = 0
    maxFrame  = None
    maxMask   = None

    output = ProcessOutput(maxPixels, maxFrame, maxMask)

    start_time = time.time()

    camera.start_recording(output, format='mjpeg', resize=(RES_WID//4,RES_HGT//4))
    while not output.done:
        camera.wait_recording(1)
    camera.stop_recording()

    exec_time = time.time() - start_time

    print()
    print("Execution time: {}".format(exec_time))

    cv.imwrite("maxframe.jpeg", maxFrame)
    cv.imwrite("maxmask.jpeg", maxMask)

    print()
    print("Object saved to maxframe.jpeg")
    print("Mask saved to maxmask.jpeg")
'''

camera = picamera.PiCamera(resolution=(RES_WID,RES_HGT), framerate=FPS)

output = ProcessOutput(0, np.array([]), np.array([]))

start_time = time.time()

camera.start_recording(output, format='mjpeg', resize=(RES_WID//4,RES_HGT//4))
while not output.done:
    camera.wait_recording(1)
camera.stop_recording()

exec_time = time.time() - start_time

print()
print("Execution time: {}".format(exec_time))

print()
print("Max pixels: {}".format(output.maxPixels))

if output.maxFrame != None and output.maxMask != None:
    cv.imwrite("maxframe.jpeg", output.maxFrame)
    cv.imwrite("maxmask.jpeg", output.maxMask)

    print()
    print("Object saved to maxframe.jpeg")
    print("Mask saved to maxmask.jpeg")
else:
    print()
    print("Time up, no image written")

print(output.pool)
print(output.processor)
