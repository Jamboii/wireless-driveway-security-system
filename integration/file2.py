#!python3

# essentially the motion sensing/img processing script
# generates file contents from some trigger, lets cellular system handle it
# just keep spitting out data
# can receive triggers from motion subsystem but also from another file written to by cellular

import os
import time
import numpy as np
import cv2 as cv
from filelock import FileLock

SIZE = 50
OUTNUM = 0
img_dir = "/home/pi/wireless-driveway-security/integration/" # directory to output toy images to

# function to look at the amount of outputs we have currently to process
# update the initial output index number based on this amount of output files
def get_outnum():
    filemax = 0
    for file in os.listdir(img_dir):
        if file.endswith(".jpeg") and "OUTPUT" in file:
            filemax = max(int(file.split("_")[1][:-5]),filemax)
    return filemax

if __name__ == "__main__":

    OUTNUM = get_outnum() # immediately update the output index (use: OUTPUT_OUTNUM.jpeg --> OUTPUT_1.jpeg)

    while True:
        # create random noise image to export
        output = np.random.randint(2,size=SIZE*SIZE).reshape((SIZE,SIZE))
        print("Waiting for file to unlock...")
        # lock the text file that we send commands to so we make sure no other process fucks with it while we edit the contents
        with FileLock("file1to2.txt.lock"):
            print("Lock acquired.")
            print()
            # open the text file of which we're appending commands to so they can be read by other processes
            with open("file1to2.txt","a") as f:
                print("file1to2.txt opened.")

                # write our new command to the text file
                # format: OUTPUT NUM = {COMMAND, INDEX NUMBER}
                # where the index number signifies the amount of times this command has been written
                f.write("OUTPUT {}\n".format(OUTNUM))

                # write our random noise image out to some directory
                cv.imwrite(img_dir + "OUTPUT_{}.jpeg".format(OUTNUM),output)
                # update OUTNUM index
                OUTNUM += 1

                # do any other extra prcoessing (e.g. waiting for a motion sensor signal lol)
                print("Simulate any extra processing...")
                time.sleep(0.1)
        # sleep for a bit to give time to unlock the file and pass it to another process
        time.sleep(0.05)
