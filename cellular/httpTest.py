import RPi.GPIO as GPIO
import serial
import time
import re

ser=serial.Serial("/dev/ttyAMA0",115200)
ser.flushInput()
power_key=6
rec_buff=''

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(power_key,GPIO.OUT)
print('serial comm established')

def send_at(command,back,timeout):
    rec_buff = ''
    ser.write((command+'\r\n').encode())
    time.sleep(timeout)
    if ser.inWaiting():
        time.sleep(0.01)
        rec_buff = ser.read(ser.inWaiting())
    if back not in rec_buff.decode():
        print(command + ' ERROR')
        print(command + ' back:\t' + rec_buff.decode())
        return 0,rec_buff.decode()
    else:
        return 1,rec_buff.decode()

def startUp():
    #looks at sim status, signal strength, registration
    send_at('AT+CPIN?','+CPIN',1)
    send_at('AT+CSQ','+CSQ',1)
    send_at('AT+COPS?','+COPS',1)
    send_at('AT+CGREG=1','+CGREG',1)
    send_at('AT+CGREG?','+CGREG',1)
    send_at('AT+CFUN?','+CFUN',1)
    #checks apn settings
    send_at('AT+CGDCONT?','+CGDCONT',1)
    #perform GPRS attach
    send_at('AT+cgatt=1','OK',1)
    send_at('AT+CGACT=1','OK',1)
    send_at('AT+CMGF=1','OK',1)
    send_at('AT+HTTPPINIT','OK',1)
    #send_at('AT+HTTPPARA/"URL/",'
    send_at('AT+CHTTPACT=\"httpbin.org\",80','OK',1)
startUp()
