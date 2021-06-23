import io
import picamera
from time import sleep

camera = picamera.PiCamera()
camera.resolution = (1640, 922)
# camera.resolution = (410,230)
camera.brightness = 60

print()
print("Press ENTER to start WALKING recording for 10 seconds.")
input()
sleep(15)
print("video recording STARTED")
#start recording using pi camera
camera.start_recording("car_10pm.h264")
#wait for video to record
camera.wait_recording(10)
#stop recording
camera.stop_recording()
print("video recording STOPPED")
exit(0)

print()
print("Press ENTER to start CAR recording for 10 seconds.")
input()
sleep(20)
print("video recording STARTED")
camera.start_recording("car_11am2.h264")
camera.wait_recording(10)
camera.stop_recording()
camera.close()
print("video recording STOPPED")

'''
with picamera.PiCamera(framerate=10) as camera:
    stream = io.BytesIO()
    for foo in camera.capture_continuous(stream, format='jpeg'):
        # Truncate the stream to the current position (in case
        # prior iterations output a longer image)
        stream.truncate()
        stream.seek(0)
        # if process(stream):
        #  break
'''
