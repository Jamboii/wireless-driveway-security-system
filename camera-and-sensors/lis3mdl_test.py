import time
import board
import busio
import adafruit_lis3mdl
from adafruit_lis3mdl import LIS3MDL, Range

import numpy as np
# import matplotlib
# matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

# print(adafruit_lis3mdl.__file__)
# print(board.SCL)
# print(board.SDA)

i2c = busio.I2C(board.SCL, board.SDA)
sensor = LIS3MDL(i2c)
# print(sensor.data_rate)
# sensor.data_rate = adafruit_lis3mdl.Rate()
sensor.range = Range.RANGE_16_GAUSS

data = []

print("3...")
time.sleep(1)
print("2...")
time.sleep(1)
print("1...")
time.sleep(1)
print("GO")
time.sleep(1)

for i in range(100*10):
# while True:
    mag_x, mag_y, mag_z = sensor.magnetic

    mean = np.mean(np.array([mag_x,mag_y,mag_z]))
    # print("X:{0:10.2f}, Y:{1:10.2f}, Z:{2:10.2f} Mean:{3:10.2f} uT".format(mag_x, mag_y, mag_z, mean))
    print("{0:10.2f}".format(mean))
    # print("")
    data.append(mean)
    time.sleep(0.01)

data = np.array(data)

plt.figure(1)
plt.plot(data)
plt.title('Time Series of Average Magnetic Strength')
plt.xlabel('Time (100 samps/s)')
plt.ylabel('Average Mag. Str. (uT)')
plt.savefig('mag_ts.png')
