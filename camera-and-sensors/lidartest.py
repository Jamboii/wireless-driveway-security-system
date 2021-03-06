import serial
import time
import RPi.GPIO as GPIO
import picamera

FPS = 13
RES_WID = 1640
RES_HGT = 922

camera = picamera.PiCamera(resolution=(RES_WID,RES_HGT), framerate=FPS)

print()
print("Starting camera...")

LEDpin = 11

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(LEDpin,GPIO.OUT)
GPIO.output(LEDpin,GPIO.LOW)

print("serial")
ser = serial.Serial('/dev/ttyUSB0',115200,timeout=1,xonxoff=False,rtscts=False)
print("enabled")

#ser.write(0x42)
ser.write(bytes(b'B'))

#ser.write(0x57)
ser.write(bytes(b'W'))

#ser.write(0x02)
ser.write(bytes(2))

#ser.write(0x00)
ser.write(bytes(0))

#ser.write(0x00)
ser.write(bytes(0))

#ser.write(0x00)
ser.write(bytes(0))
#ser.write(0x01)
ser.write(bytes(1))
#ser.write(0x06)
ser.write(bytes(6))
print("bytes written")

while(True):
    while(ser.in_waiting >= 9):
        # print(ser.read())
        if((b'Y' == ser.read()) and ( b'Y' == ser.read())):
            GPIO.output(LEDpin, GPIO.LOW)
            Dist_L = ser.read()
            Dist_H = ser.read()
            Dist_Total = (ord(Dist_H) * 256) + (ord(Dist_L))
            for i in range (0,5):
                ser.read()

            print(Dist_Total)
            if(Dist_Total < 700):
                GPIO.output(LEDpin, GPIO.HIGH)
                print("DETECTED")
                exit(0)
                # camera.capture('/home/pi/ifthisworks.jpeg')
                # exit(0)
