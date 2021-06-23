import os

import cv2 as cv
import numpy as np

ETX    = b'\x03'[0] # <ETX>    = 0x03
CTRL_Z = b'\x1A'[0] # <CTRL+Z> = 0x1A

FNAME  = "../camera-and-sensors/maxframe.jpeg"

# print(ETX)
# print(CTRL_Z)

def img2bin(img_path):
    # read in image of predetermined file name
    im = cv.imread(img_path)

    # jpg encode the image into an image buffer
    is_success, im_buf_arr = cv.imencode(".jpeg", im)
    # convert the image buffer to a byte class representing the image
    byte_im = im_buf_arr.tobytes()

    # byte class is immutable, create a byte array of the image so that data is mutable
    byte_im_arr     = bytearray(byte_im)
    # create a new byte array to account for found instances of ETX and CTRL+Z
    byte_im_arr_new = bytearray()

    # print(type(byte_im))
    # print(type(byte_im_arr))

    count = 0
    # loop through each byte within the image
    for byte in byte_im_arr:
        if byte == ETX:                  # <ETX> --> <ETX><ETX>
            # print("ETX")
            byte_im_arr_new.append(ETX)
            byte_im_arr_new.append(ETX)
            count += 1
        elif byte == CTRL_Z:             # <CTRL+Z> --> <ETX><CTRL+Z>
            # print("CTRL_Z")
            byte_im_arr_new.append(ETX)
            byte_im_arr_new.append(CTRL_Z)
            count += 1
        else:                            # Any other byte is just re-appended
            byte_im_arr_new.append(byte)

    # Make sure we have a new byte array length whose additions only account for ETX and CTRL_Z instances
    assert(len(byte_im_arr_new) - count == len(byte_im_arr))

    print("Image successfully converted to binary.")

    # Rename/Delete the image file so we know we're done with this image
    # new_img_path = img_path.split(".")[0] + "_old.jpeg"
    # os.rename(img_path, new_img_path)

    return byte_im_arr_new

while True:
    try:
        byte_arr = img2bin(FNAME)
        break
    except Exception:
        pass
