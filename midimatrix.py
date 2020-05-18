import mido
import RPi.GPIO as GPIO
import time
from subprocess import call

outport = mido.open_output('f_midi')

GPIO.setmode(GPIO.BCM)
global shift, onmessages, offmessages, mapping, currentmapping

shift = 0
ypins = [18,23,24,25,12,16,20,21]
xpins = [19,13,6,5,22,27,17,4]
functionpins = [1,7,8,26,0]
statuspin = 2

WIDTH = len(xpins)
HEIGHT = len(ypins)

values = [[0 for i in range(WIDTH)] for j in range(HEIGHT)]
chromaticnotemapping = [36,37,38,39,40,41,42,43,41,42,43,44,45,46,47,48,46,47,48,49,50,51,52,53,51,52,53,54,55,56,57,58,56,57,58,59,60,61,62,63,61,62,63,64,65,66,67,68,66,67,68,69,70,71,72,73,71,72,73,74,75,76,77,78]
drummapping = [36,37,38,39,68,69,70,71,40,41,42,43,72,73,74,75,44,45,46,47,76,77,78,79,48,49,50,51,80,81,82,83,52,53,54,55,84,85,86,87,56,57,58,59,88,89,90,91,60,61,62,63,92,93,94,95,64,65,66,67,96,97,98,99]
octavemappingoffset = [0,2,4,5,7,9,11,12]
octavemapping = [0 for i in range(64)]
octavebasenote = 12
for i in range(HEIGHT):
    for j in range(WIDTH):
        octavemapping[i*WIDTH + j] = octavemappingoffset[j] + octavebasenote + i*12

mapping = chromaticnotemapping # default to chromatic mapping
currentmapping = 0
onmessages = [mido.Message('note_on', note = i, velocity = 127) for i in mapping]
offmessages = [mido.Message('note_off', note = i, velocity = 127) for i in mapping]
buttonpresslength = 1 # 10 seconds for long press
shutdownlength = 3 # 5 seconds for shutdown press

def shiftcallback(channel):
    global shift
    shift = 0 if GPIO.input(channel) else 1
    print("shift: {}".format(shift))
def button1callback(channel):
    global shift, shutdownsequence
    if shift:
        shutdownsequence = 0 if GPIO.input(channel) else 1
        if shutdownsequence:
            print("Shutting down...")
            starttime = time.time()
            while shutdownsequence and time.time() - starttime < shutdownlength:
                pass
            if shutdownsequence and time.time() - starttime > shutdownlength:
                call("sudo nohup shutdown -h now", shell=True)
            else:
                print("Shutdown cancelled")
    else:
        pass
def button2callback(channel):
    global shift, onmessages, offmessages, mapping, currentmapping
    value = GPIO.input(channel)
    if shift:
        if value:
            ### switch mapping modes
            print("switching mapping modes")
            if currentmapping == 0:
                mapping = drummapping
                currentmapping = (currentmapping + 1)%3
            elif currentmapping == 1:
                mapping = octavemapping
                currentmapping = (currentmapping + 1)%3
            elif currentmapping == 2:
                mapping = chromaticnotemapping
                currentmapping = (currentmapping + 1)%3
            else:
                pass
            onmessages = [mido.Message('note_on', note = i, velocity = 127) for i in mapping]
            offmessages = [mido.Message('note_off', note = i, velocity = 127) for i in mapping]
    else:
        pass


GPIO.setup(statuspin, GPIO.OUT)
GPIO.output(statuspin, 1)
for i in xpins:
    GPIO.setup(i, GPIO.OUT)
for j in ypins:
    GPIO.setup(j, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
for k in functionpins:
    GPIO.setup(k, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(8, GPIO.BOTH, callback=shiftcallback, bouncetime=20)
GPIO.add_event_detect(26, GPIO.BOTH, callback=button1callback, bouncetime=20)
GPIO.add_event_detect(0, GPIO.BOTH, callback=button2callback, bouncetime=20)



# timeout = 100
# starttime = time.time()
try:
    while 1:
        for i in range(WIDTH):
            GPIO.output(xpins[i], 1)
            for j in range(HEIGHT):
                currentval = GPIO.input(ypins[j])
                if currentval != values[i][j]:
                    if currentval:
                        # print("playing note {}".format(i*WIDTH + j))
                        outport.send(onmessages[i*WIDTH + j])
                    else:
                        # print("stopping note {}".format(i*WIDTH + j))
                        outport.send(offmessages[i*WIDTH + j])
                values[i][j] = currentval
            GPIO.output(xpins[i], 0)
    GPIO.cleanup()
except KeyboardInterrupt:
    GPIO.cleanup()
    print("\nCleaning up...")
