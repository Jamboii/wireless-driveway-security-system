
#!/usr/bin/python

import RPi.GPIO as GPIO
import serial
import time
import re
import os

#import base64
import cv2 as cv
import numpy as np

ser = serial.Serial(port="/dev/ttyAMA0",baudrate=115200, rtscts=True)
ser.flushInput()
myNum = '**********' #********** change it to the phone number you want to caall
power_key = 6
rec_buff = ''
#define SIM memory index
mem_idx=0
#define command dictionary and will set mem_idx post setting responses
commands={}
#name of file to be sent
filename='larry.jpg'
#set up welcome messge
welcome='''Welcome to your wireless driveway security system!Your number
    has been added to the notification list. Text HELP for possible commands.'''
#set up list of commands
help='''Possible Commands\n HELP for help\n PING for status\n PAUSE to pause
 UNPAUSE to resume\n STOP to stop notifications'''
#sets up delete text exchanges
delete1='Please test YES to stop recieving notifications'
delete2='Number has been deleted'
delete3='Invalid response. Still on notification list'
#set up invalid command resp
invalid='That command was invalid. Please text HELP for help'
#set up pause and unpause command responses
pause='Notifications have been paused. Text UNPAUSE to resume'
unpause='Notifications have resumed'
ping='time'

# some FTP data globals
ETX    = b'\x03'[0] # <ETX>    = 0x03
CTRL_Z = b'\x1A'[0] # <CTRL+Z> = 0x1A
#ETX=bytes.fromhexlify('03')
#CTRL_Z=bytes.fromhexlify('1A')
FNAME  = "../camera-and-sensors/maxframe.jpeg" # file that function will search for

GPIO.setmode(GPIO.BCM)
GPIO.setup(16,GPIO.IN)
GPIO.setup(17,GPIO.OUT)
GPIO.setwarnings(False)
GPIO.setup(power_key,GPIO.OUT)
print ('Serial Comm Established')

def img2use(img_path):
#    with open (img_path, "rb") as img_file:
#        f=img_file.read()
#   b=bytearray(f)
    #print(my_string.count('\x03'))
    #print(my_string.count('\x1A'))
    #my_string.replace('\x03','\x0303')
    #my_string.replace('\x1A','\x031A')
    return b[0]
def img2bin(img_path):
    # read in image of predetermined file name
    im = cv.imread(img_path)

    # jpeg encode the image into an image buffer
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
    # CAN BE LEFT COMMENTED OUT FOR NOW UNTIL NECESSARY
    # new_img_path = img_path.split(".")[0] + "_old.jpeg"
    # os.rename(img_path, new_img_path)

    return byte_im_arr_new, byte_im_arr

def send_at(command,back,timeout):
    rec_buff = ''
    test_num=0
    back=back.lower()
    ser.write((command+'\r\n').encode())
    time.sleep(timeout)
    if ser.inWaiting():
        time.sleep(timeout)
        rec_buff = ser.read(ser.inWaiting()).lower()
        print( rec_buff.decode())
#        print('b4 if')
    if back not in rec_buff.decode():
        print('^^^')
        return 0,rec_buff.decode()
    else:
        return 1,rec_buff.decode()
def startUp():
    ser.write(('at+ifc=2,2\r\n').encode('ascii'))
    #looks at sim status, signal strength, registration
    send_at('AT+CPIN?','+CPIN',1)
    send_at('AT+CSQ','+CSQ',1)
    send_at('AT+COPS?','+COPS',1)
    send_at('AT+CGREG=1','+CGREG',1)
    send_at('AT+CGREG?','+CGREG',1)
    send_at('AT+CFUN?','+CFUN',1)
    send_at('at+cgsockcont=1,\"IP\",\"wap.tracfone\"','OK',2)
    #checks apn settings
    send_at('AT+CGDCONT?','+CGDCONT',2)
def testBytes():
    #p=np.arange(256)
    p=bytearray([num for num in range(256)])
    d= p+p+p+p+p+p+p+p+p+p
    e= d+d+d+d+d+d+d+d+d+d
    g= e+e+e+e+e+e
    byte_im_arr_new = bytearray()

    # print(type(byte_im))
    # print(type(byte_im_arr))

    count = 0
    # loop through each byte within the image
    for byte in g:
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
    return byte_im_arr_new, g
def setMessage(message,phonenum,key):
    global mem_idx
    global commands
    print (phonenum)
    print('in setMess')
    rts,output=serts,output=send_at("AT+CMGW=\""+phonenum+"\"",">",1)
    if rts == 1:
        print('in if')
        ser.write((message+'\x1A').encode())
        e,f=send_at('','OK',1)
        print (output)
        commands[key]=mem_idx
        mem_idx+=1
def setResponses():
    global mem_idx
    global myNum
    #delete all messages including unread
    send_at('AT+CMGD=,4','OK',1)
    mem_idx=0
    print('post delete')
    #check storage to confirm no messages
    send_at('AT+CMGL=\"ALL\"','+CMGL',1)
    print ('post check empty')
    setMessage(welcome,myNum,'p4g934dweih5fth')
    setMessage(help,myNum,'help')
    setMessage(pause,myNum,'pause')
    setMessage(unpause,myNum,'unpause')
    #setMessage(invalid,myNum,'invalid')
    setMessage(delete1,myNum,'stop')
    setMessage(delete2,myNum,'yes')
    setMessage(ping,myNum,'ping')
    #check to see if the messages stored as expected
    a,b=send_at('AT+CMGL=\"ALL\"','+CMGL',1)
    print(b)
    print(commands)
def sendSMS(messageIdx):
    send_at('AT+CMSS='+messageIdx,'+CMSS',1)
def TestRecieveSMS():
    #alert=''
    alert=b'\r\n+CMTI: "SM",2\r\n'
    alertStr=str(alert)
    done=0
    newText='+CMTI'
    #determine if it is a new text by looking for +cmni
    if alertStr.find(newText) != -1:
        print ('new text')
        #extract where message is stored in memory
        messageNum=re.findall(r'\d+',alertStr)
        print (str(messageNum))
        #convert to useable form
        messageNumStr=''.join(map(str,messageNum))
        print (messageNumStr)
        send_at("AT+CMGR="+messageNumStr,'+CMGR',2)
    else:
        print ('unexpected serial comm from modem')
def recieveSMS():
    global commands
    alert=''
    done=0
    newText='+CMTI'
    while done != 1:
        if ser.inWaiting():
            time.sleep(0.01)
            print ('setting alert')
            alert=ser.read(ser.inWaiting())
            print(alert)
            alertStr=str(alert)
            time.sleep(0.01)
            #determine if it is a new text by looking for +cmni
            if alertStr.find(newText) != -1:
                #extract where message is stored in memory
                messageNum=re.findall(r'\d+',alertStr)
                print (str(messageNum))
                #convert to useable form
                messageNumStr=''.join(map(str,messageNum))
                #read the message from storage
                #print ('read message')
                #send_at("AT+CMGR="+messageNumStr,'+CMGR',2)
                #print('send')
                filterSMS(messageNumStr)
            else:
                print ('unexpected serial comm from modem')

def filterSMS(messageIdx):
    a,recievedSMS=send_at("AT+CMGR="+messageIdx,'+CMGR',1)
    print(recievedSMS)
    command_split=recievedSMS.split('\n')
    command=command_split[2].split('\r')[0]
    #print (command_split)
    print (command)
    idx=commands[command.lower()]
    print (idx)
    send_at('AT+CMGR='+str(idx),'+CMGR',2)
    sendSMS(str(idx))
def setSimpMessage(message,phonenum):
    print (phonenum)
    #clear memory
    print('in setMess')
    rts,output=serts,output=send_at("AT+CMGW=\""+phonenum+"\"",">",1)
    if rts == 1:
        ser.write((message+'\x1A').encode())
        e,f=send_at('','OK',2)
def setTestCases():
    setSimpMessage('help',myNum)
    setSimpMessage('pause',myNum)
    setSimpMessage('unpause',myNum)
    setSimpMessage('ping',myNum)
    setSimpMessage('stop',myNum)
    setSimpMessage('yes',myNum)
    setSimpMessage('not right',myNum)
def setDataCall():
    #perform GPRS attach
    send_at('AT+cgatt=1','OK',1)
    send_at('AT+CMGF=1','OK',1)
#set configurations to access ftp server
def setFTP():
    send_at('at+cftpslogout','+cftpslogout: 0',.5)
    send_at('at+cftpsstop','+cftpsstop: 0',.5)
    send_at('at+cftpport=21','OK',.2)
    send_at('at+cftpmode=1','OK',.2)
    send_at('at+cftptype=I','OK',.2)
    send_at('at+cftpserv=\"73.198.62.223\"','OK',.2)
    send_at('at+cftppw=\"4doi98uy43ew#\"','OK',.2)
    send_at('at+cftpsstart','+cftpsstart: 0',1)
    send_at('at+cftpsingleip=1','OK',.2)
    send_at('at+cftpslogin=\"73.198.62.223\",21,\"test\",\"4doi98uyg43ew#\",0','+cftpslogin: 0',4)
#    send_at('at+cftpsputfile=\"larry.jpg\",0','+cftpsputfile',4)
    #word=img2use(FNAME)
    word,doc=img2bin(FNAME)
#    word,doc =testBytes()
    #f = open('my_file_25kBTest_real', 'w+b')
    #f.write(doc)
    #f.close()
    rts2,out2=send_at('at+cftpput=\"img_fast_flow1\"','+cftpput: begin',3)
    print('1')
    time.sleep(.5)
#    if rts2==1:
    #ser.reset_input_buffer()
    #for i in range (60):
    #n=256
    #for i in range(0,len(word),n):
    #    ser.write(word[i:i+n])
    #    time.sleep(.01)
    ser.write(word)
    time.sleep(.1)
    ser.write(('\x1A').encode('ascii'))
#    rec=ser.read(ser.inwaiting())
    print('3')
#    send_at('at+cftpslogout','+cftpslogout:',1)
#    send_at('at+cftpsstop','+cftpsstop: 0',1)

#passes the file name and uploads the file to server
#def ftp_put_file(file_name):
   # send_at('at+cftpsputfile=\"+file_name+\",0','OK',1)
startUp()
#testBytes()
#img2base64(FNAME)
#setDataCall()
#setResponses()
setFTP()
#ftp_put_file(filename)
#TestRecieveSMS()
#recieveSMS()
#setTestCases()
#print (commands)
#recieveSMS()
#filterSMS('7')
