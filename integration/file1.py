#!python3

# essentially the cellular script
# reads in file contents, sends file, deletes file from existence, looks for new contents
# also can receive commands from the aether (some phone) and give them to the Mot. System
# these commands will be stored in another file

import os
import sys
import time
import cv2 as cv
from filelock import FileLock

PINGNUM = 0
img_dir = "/home/pi/wireless-driveway-security/integration/"

if __name__ == "__main__":
    while True:
        '''
        for line in sys.stdin.readlines():
            with FileLock("file2to1.txt.lock"):
                print("Lock acquired")
                f = open("file2to1.txt")
                print("file 2to1 opened")
                f.write("PING {}\n".format(PINGNUM))
                PINGNUM += 1
                print("PING")
                print()
                f.close()
        '''
        print("-----------------------------")
        print("Waiting for file to unlock...")
        # lock the file so we make sure no other process can fuck with it
        with FileLock("file1to2.txt.lock"):
            print("Lock acquired.")
            print()

            # open up our text file which will process any commands written to it
            f = open("file1to2.txt")
            print("file1to2.txt opened.")

            # read in and spit out all lines in the text file
            lines = f.readlines()
            print("LINES IN FILE: {}".format(lines))

            # if our text file has commands to process in it
            if len(lines) >= 1:
                # look at the first line only and dick around with it
                cmd_num = lines[0].split()
                print("LINE ARGS: {}".format(cmd_num))
                # cmd_num should be split into a "cmd" portion and "num" portion
                # cmd - the actual action to be processed (e.g. OUTPUT = HEY AN IMAGE NEEDS TO BE SENT NOW)
                # num - some sorta index pertaining to how many of said cmd needs to be processed (e.g. OUTPUT 1 = process 1st output image, OUTPUT 2 = process 2nd output image)
                if len(cmd_num) == 2:
                    cmd = cmd_num[0]
                    num = cmd_num[1]
                else:
                    cmd = ""
                    num = ""
                    print("COMMAND IS INVALID, PASSING...")
            else: # otherwise our text file is empty
                cmd = ""
                num = ""
                print("TEXT FILE IS EMPTY, PASSING...")

            # look for the OUTPUT command (which could be an indication of a new maxframe.jpeg)
            if cmd == "OUTPUT":
                # try to access the image denoted by the command and "process" and remove it
                # "process" being sending the img over cellular or something
                try:
                    # read in image and do some processing (e.g. convert to binary and send over FTP)
                    img = cv.imread(img_dir + "OUTPUT_{}.jpeg".format(num))
                    print("OUTPUT {} shape: {}".format(num,img.shape))
                    print()
                    # remove img path from existence
                    os.remove("OUTPUT_{}.jpeg".format(num))
                except Exception:
                    # haha bitch what file
                    print("output.jpeg does not exist")

                # get rid of the file name regardless if it doesn't exist
                lines.pop(0)
                print(lines)

            f.close()
            # open the file again to rewrite our new lines (lines[1:])
            with open("file1to2.txt","w+") as f:
                for line in lines:
                    f.write(line)


            # wait for a bit (simulate waiting for other cellular processing)
            print("Simulating any extra processing...")
            time.sleep(0.1)
        # some extra waiting to allow time to give up possession of the txt file
        time.sleep(0.05)
