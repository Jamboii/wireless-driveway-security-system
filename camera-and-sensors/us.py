# ultrasonic sensor testing
from gpiozero import DistanceSensor
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep
import numpy as np

# pigpio = PiGPIOFactory()

print("Creating distance sensor...")
sensor = DistanceSensor(echo=24, trigger=23, max_distance=4, threshold_distance=1.75)
sensor_avg = 0
sensor_tot = 0
sensor_readings = 0

while True:
    sensor_readings += 1
    sensor_tot += sensor.distance
    sensor_avg = sensor_tot / sensor_readings
    print('Distance: {}, Average: {}'.format(sensor.distance,sensor_avg))
    sleep(0.05)

'''
print("Waiting for in range")
sensor.wait_for_in_range()
print("SUP")
'''
