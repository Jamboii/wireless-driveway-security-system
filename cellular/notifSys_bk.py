#!/usr/bin/python

import RPi.GPIO as GPIO
import serial
import time
import re
import os
import datetime
from pytz import timezone
from filelock import FileLock

import cv2 as cv
import numpy as np

img_dir = "/home/pi/wireless-driveway-security/img_output/"
ping_count = 0

filelock_maxframes = "/home/pi/wireless-driveway-security/integration/maxframes.txt"
filelock_pings     = "/home/pi/wireless-driveway-security/integration/pings.txt"

captureImage     = False
sendNotification = True
isDelete=False

#define the serial port to be used to communicate with Waveshare SIM7600
#Be sure to disable bluetooth features if working with RPi Zero WH
ser = serial.Serial("/dev/ttyAMA0",115200)
rec_buff = '' #used to read serial resp

power_key = 6 #used to ensure SIM7600 is powered up

#define SIM memory index
mem_idx=0
#define command dictionary and will set mem_idx post setting responses
commands={}

#set up welcome messge
welcome='''Welcome to your wireless driveway security system! Your number has been added to the notification list. Text HELP for possible commands.'''
#set up list of commands
help='''Possible Commands:\n HELP for help\n PING for status\n PAUSE to pause
 UNPAUSE to resume\n STOP to stop notifications'''
#sets up delete text exchanges
delete1='Please text YES to stop recieving notifications'
delete2='Your number has been unregistered.'
delete3='Invalid response. Still on notification list'
#set up invalid command resp
invalid='That command was invalid. Please text HELP for help'
#set up pause and unpause command responses
pause='Notifications have been paused. Text UNPAUSE to resume'
unpause='Notifications have resumed'
# set up text for ping response
ping='Status and image requested.'
#Variable to set phone number
myNum = '**********' #********** change it to the phone number you want to call or the code will upon registration
# some FTP data globals
ETX    = b'\x03'[0] # <ETX>    = 0x03
CTRL_Z = b'\x1A'[0] # <CTRL+Z> = 0x1A
#ETX=bytes.fromhexlify('03')
#CTRL_Z=bytes.fromhexlify('1A')
# FNAME  = "../camera-and-sensors/maxframe.jpeg" # file that function will search for

#ser.reset_input_buffer()
#ser.reset_output_buffer()
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(power_key,GPIO.OUT)
print ('Serial Comm Established')

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

    return byte_im_arr_new

def send_at(command,back,timeout):
    rec_buff = ''
    test_num=0
    back=back.lower()
    ser.write((command+'\r\n').encode('ascii'))
    time.sleep(timeout)
    if ser.inWaiting():
        time.sleep(timeout)
        rec_buff = ser.read(ser.inWaiting()).lower()
        print( rec_buff.decode('ascii'))
    if back not in rec_buff.decode('ascii'):
        print('^^^')
        return 0,rec_buff.decode('ascii')
    else:
        return 1,rec_buff.decode('ascii')

#looks at sim status, signal strength, registration
def setBasic():
    send_at('AT+CPIN?','+CPIN',1)
    send_at('AT+CSQ','+CSQ',1)
    send_at('AT+COPS?','+COPS',1)
    send_at('AT+CGREG=1','+CGREG',1)
    send_at('AT+CGREG?','+CGREG',1)
    send_at('AT+CFUN?','+CFUN',1)
    send_at('at+cgsockcont=1,\"IP\",\"wap.tracfone\"','OK',2)
    #checks apn settings
    send_at('AT+CGDCONT?','+CGDCONT',2)
#function that performs basic
def setDataCall():
    #perform GPRS attach
    send_at('AT+cgatt=1','OK',1)
    send_at('AT+CMGF=1','OK',1)
#set configurations to access ftp server
def setFTP():
    #ftp logout and stop to ensure proper functionality
    send_at('at+cftpslogout','+cftpslogout: 0',2)
    send_at('at+cftpsstop','+cftpsstop: 0',2)
    #define username, password, and other vital ftp login information
    send_at('at+cftpport=21','OK',1)
    send_at('at+cftpmode=1','OK',1)
    send_at('at+cftptype=I','OK',1)
    send_at('at+cftpserv=\"73.198.62.223\"','OK',1)
    send_at('at+cftppw=\"4doi98uy43ew#\"','OK',1)
    #perform FTP start and login
    send_at('at+cftpsstart','+cftpsstart: 0',2)
    send_at('at+cftpsingleip=1','OK',1)
    send_at('at+cftpslogin=\"73.198.62.223\",21,\"test\",\"4doi98uyg43ew#\",0','+cftpslogin: 0',8)

#Startup function that runs basic status AT Commands, sets up data call functionality, ftp functionality
def setWS7600():
    setBasic()
    setDataCall()
    setFTP()

#function that is able to set desired str as an SMS message in modem memory and to command
def setCommand(message,phonenum,key):
    global mem_idx
    global commands
    print (phonenum)
    print('in setMess')
    #write sms to modem memory
    rts,output=send_at("AT+CMGW=\""+phonenum+"\"",">",1)
    # if asking to write a message is sucessful we will encode the desired message for the SMS
    if rts == 1:
        print('in if')
        ser.write((message+'\x1A').encode())
        e,f=send_at('','OK',1)
        print (output)
        # put info in command dict
        #increment the index of the dictionary so all desired responses are not saved on top of ea other
        commands[key]=mem_idx
        mem_idx+=1
#function to be used upon inital bootup to save command messages to modem mem
def setResponses():
    global mem_idx
    global myNum
    #delete all messages including unread
    send_at('AT+CMGD=,4','OK',1)
    mem_idx=0
    print('all messages from modem mem have been deleted')
    #check storage to confirm no messages
    send_at('AT+CMGL=\"ALL\"','+CMGL',1)
    print ('Read all the messages to ensure modem mem is empty')
    #write all possible commands to a dictionary and their resp to the modem mem
    #should increment from 0 to 6 not including invalid
    setCommand(welcome,myNum,'p4g934dweih5fth')
    setCommand(help,myNum,'help')
    setCommand(pause,myNum,'pause')
    setCommand(unpause,myNum,'unpause')
    setCommand(delete1,myNum,'stop')
    setCommand(ping,myNum,'ping')
    #check to see if the messages stored as expected
    a,b=send_at('AT+CMGL=\"ALL\"','+CMGL',1)
    #prints dictionary to ensure everything
    print(commands)

#basic function which asks the modem to send the message from mem
def sendSMS(messageIdx):
    send_at('AT+CMSS='+messageIdx,'+CMSS',1)

#main function for monitoring if a SMS is recieved, interpreting the command, and responding respectively
def recieveSMS():
    global commands
    alert=''
    done=0
    newText='+CMTI'
    if ser.inWaiting():
        time.sleep(0.01)
        print ('setting alert')
        alert=ser.read(ser.inWaiting())
        print(alert)
        print ('this is the length of the incoming serial '+str(len(alert)))
        alertStr=str(alert)
        time.sleep(0.01)
        #determine if it is a new text by looking for +cmni
        if alertStr.find(newText) != -1:
            #extract where message is stored in memory aka find the first number
            # alert should resemble
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
    global captureImage
    global isDelete
    global sendNotification
    global myNum
    #reads sent message at a index
    a,recievedSMS=send_at("AT+CMGR="+messageIdx,'+CMGR',1)
    print(recievedSMS)
    #splits the resp of +cmgr to extract contents of sms
    command_split=recievedSMS.split('\n')
    command=command_split[2].split('\r')[0]
    print (command)
#    registered, thatNum = isContact(recievedSMS, idx)
    try:
        #based on the command an index of where the proper resp in modem mem is returned
        idx=commands[command.lower()]
        print (idx)
        print('checking if registered?')
        #only continues if the message recieved was sent by person registered to device
        registered,thatNum=isContact(recievedSMS,idx)
        if (registered):
            print('determined message was from contact and a command')
            #this is the beginning of an unhealthy amount of if elif statements hehe
            #note the help doesnt need elif b/c it just need to send message of the idx
            #i do not think the welcome needs one since isCOntact should handle it
            if (idx ==2): #handles the pause
                print('Notifications have been paused')
                sendNotification=False
            elif (idx == 3): #handles unpause
                print('Notifications have resumed')
                sendNotification=True
            elif (idx == 4): # handles stop
                print('sets isDelete to true')
                isDelete=True
            # this if statement will set captureImage so that the files communicating b/w scripts knows when to write
            #ping command would be at index 5 since it is the last of the 6 commands put in the dictionary by setResponses
            elif (idx == 5):
                print("filterSMS - PING RECEIVED")
                captureImage=True
                if (not sendNotification):
                    idx=2
                    captureImage=False
            else:
                print('something fishy happened with try except filtering or we used help or welcome commands')
            #send_at('AT+CMGR='+str(idx),'+CMGR',2)
            sendSMS(str(idx))
            print('proper text shouldve sent')
        else:
            print('send some type of not registered command?')
        print("filterSMS captureImage: {}".format(captureImage))
    except:
        print('have entered the except so not a command. checking if registered?')
        # determines if the text recieved was from a registered user
        # if not sends message telling them to register and does not do any command
        registered, thatNum =isContact(recievedSMS)
        if (registered):
            print('user is a contact')
            #checks to see if command not in dictionary was yes
            #if it was and isdelete = 1 it completes deregistration process
            if(isDelete):
                print('a delete command was previously sent')
                if (command == 'yes'):
                    send_at("at+cmgs=\""+myNum+'\"',">",1)
                    ser.write((delete2).encode('ascii'))
                    ser.write(('\x1A').encode('ascii'))
                    myNum=''
                    print('did jazz to delete phone num')
                    isDelete=False
                else:
                    send_at("at+cmgs=\""+myNum+'\"',">",1)
                    ser.write((delete3).encode('ascii'))
                    ser.write(('\x1A').encode('ascii'))

           #if it was a register user it lets them know the command was invalid
            else:
                print('something whack happened with deregistration or invalid')
                print ('send help command due to invalid resp')
                send_at("at+cmgs=\""+myNum+'\"',">",1)
                ser.write(('That is an invalid command. Please text HELP to see valid commands.').encode('ascii'))
                ser.write(('\x1A').encode('ascii'))
        #not a registered user so sends something about how to register
        else:
            print('send some type of command about not being registered?')
            send_at("at+cmgs=\""+thatNum+'\"',">",1)
            ser.write(('You are not a registerd device. Please send unique registration code provided with device.').encode('ascii'))
            ser.write(('\x1A').encode('ascii'))

#this module will be about user registration
#will return True if the num is on the contact list
def isContact(readSMSContent,dictionaryIDX=99):
    global myNum
    #extract the phone number from the serial resp from +cmgr (reading sms)
    content_split= readSMSContent.split('\"')
    print('in is Contact -- '+str(content_split))
    num=content_split[3]
    print('the supposed number'+num)
    #if the number whom sent the txt matches our contact return true
    if (num == myNum ):
        print('the user is registered')
        return True, num
    #check to see if the proper unique registration code was equal to welcome
    elif (dictionaryIDX==0):
        print('begin welcome reg process')
        myNum = num
        setResponses()
        return True, num
    else:
        return False, num

# This function completes sending an image via FTP and sending user a sms with timestamp
def sendFTP(FPATH,FNAME):
    global myNum
    print("IN SENDFTP...")
    time.sleep(1)
    #gonna try not to do this for every image cuz it takes forever and ever and im getting wrinkles :)
   # send_at('at+cftpsstart','+cftpsstart: 0',2)
   # send_at('at+cftpsingleip=1','OK',1)
   # send_at('at+cftpslogin=\"73.198.62.223\",21,\"test\",\"4doi98uyg43ew#\",0','+cftpslogin: 0',8)
    word = img2bin(FPATH)
    #get some big time for the SMS
    tz=timezone('EDT')
    myTime=str(datetime.datetime.now(tz))
    #want to send user a txt that image was captured
    send_at("AT+CMGS=\""+myNum+'\"',">",1)
    # if asking to write a message is sucessful we will encode the desired message for the SMSw
    ser.write((r'Image captured at '+myTime+ ' Image is processing and will be available shortly at: http://73.198.62.223/'+FNAME).encode("ascii"))
    ser.write(('\x1A').encode('ascii'))
    time.sleep(.01)
    send_at(' ','OK',.5)
    print("SARAH BREAKPOINT 1")
    #this jazz will send an image with ftp w/ kludge that doesnt work tehe
    rts2,out2=send_at('at+cftpput=\"'+FNAME+'\"','+cftpput: begin',3)
    time.sleep(.1)
    n=256
    #my for loop kludge that keeps me up at night
    for i in range(0,len(word),n):
        print("SARAH BREAKPOINT "+str(i))
        ser.write(word[i:i+n])
        time.sleep(.2)
    ser.write(word)
    time.sleep(.03)
    ser.write(('\x1A').encode('ascii'))
    time.sleep(2)
    reset_input_buffer()
    reset_output_buffer()
    print('Completed FTP Put Command')
#    time.sleep(16)
#    if ser.inWaiting():
#        time.sleep(.01)
#        print (ser.read(ser.inWaiting()))
    #send_at('','OK',.1)
    #time.sleep(.1)
    #Hello I make link send to user registered
#    print (FNAME)
#    print (myTime)
#    send_at("AT+CMGS=\""+myNum+"\"",">",1)
#    ser.write((r'View image from '+myTime+ 'at http://73.198.62.223/' + FNAME ).encode('ascii'))
#    time.sleep(.01)
#    ser.write(('\x1A').encode('ascii'))
    return myTime

def run():
    #alex put your stuff here for the whole file checking jazz
    # if there's no send notification and theres an image in the file, sendFTP(FNAME)
    global captureImage
    global ping_count
    global sendNotification
    while True:
        print("------------------------------------")
        # see if we have a ping command to process
        print("Checking for ping command...")
        print("Top of the while captureImage: {}".format(captureImage))
        print()
        if captureImage and sendNotification:
            print("PING COMMAND TO BE PROCESSED")
            # process ping command
            with FileLock(filelock_pings + ".lock"):
                print("Lock acquired - ping add.")
                # open txt file
                with open(filelock_pings,"a") as f:
                    print("{} opened.".format(filelock_pings))
                    # write new command
                    f.write("PING {}\n".format(ping_count))
                    # increment ping count
                    ping_count += 1
            time.sleep(0.05)
            captureImage = False
            print()
        else:
            captureImage = False
        # look in the maxframe.txt for any images to process
        with FileLock(filelock_maxframes + ".lock"):
            print("Lock acquired.")

            # open up our text file which will process any commands written to it
            f = open(filelock_maxframes)
            print("{} opened.".format(filelock_maxframes))

            # read in and spit out all lines in the text file
            lines = f.readlines()
            print("LINES IN FILE: {}".format(lines))

            # if our text file has commands to process in it
            if len(lines) >= 1:
                # look at the first line only and dick around with it
                cmd_num = lines[0].split()
                print("LINE ARGS: {}".format(cmd_num))

                # cmd_num should be split into a "cmd" portion and "num" portion
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

            # look for MAXFRAME command, which means theres a new maxframe_#.jpeg file to process
            if cmd == "MAXFRAME":
                # try to access the image and process the shit out of it
                img_name= "maxframe_{}.jpeg".format(num)
                img_path=img_dir+img_name
                try:
                    img = cv.imread(img_path)
                    print("loaded {}, sending to FTP server".format(img_path))
                    # send image to ftp server
                    #################
                    if sendNotification:
                        mytime=sendFTP(img_path,img_name)
                        send_at("AT+CMGS=\""+myNum+"\"",">",1)
                        ser.write(('View image from '+myTime+ 'at http://73.198.62.223/' + img_name ).encode('ascii'))
                        time.sleep(.01)
                        ser.write(('\x1A').encode('ascii'))
                    #################
                except Exception:
                    # haha bitch what file you talking about????
                    print("{} was not properly loaded/sent, moving on...".format(img_path))

                # get rid of the file name regardless if it doesn't exist
                lines.pop(0)
                print(lines)

            f.close()
            # open the file agai to rewrite our new lines (lines[1:])
            with open(filelock_maxframes,"w+") as f:
                for line in lines:
                    f.write(line)
            print()
        time.sleep(3)
        print("Attempting to receive SMS...")
        # try to get a command sent by the user
        recieveSMS()
        print("receiveSMS captureImage: {}".format(captureImage))
        print()

setWS7600()
setResponses()
#while (True):
 #   recieveSMS()
#sendFTP(img_dir+"maxframe_3.jpeg","maxframe_3.jpeg")
run()
