import RPi.GPIO as GPIO
import time
import math


MULTIPLIER = 17150
WAITTIME = 0.0
MAX_DIFFERENCE = 20

TRIG = [16, 38, 35, 13]
ECHO = [18, 36, 37, 11]
RESULT = [0, 0, 0, 0]
DATA = [[], [], [], []]  #0: front, 1: left, 2: back, 3: right
WDATA = [[0, 0], [0, 0], [0, 0], [0, 0]]

MOTOR = [29, 31, 32, 33]  #0: engine+, 1: engine-, 2: steering+, 3: steering-

LOGFILE = "log/main_" + str(int(time.time())) + ".log"

drivingForward = False
drivingBackward = False

measurements = 0
successful_measurements = [0, 0, 0, 0]

timeOfLastMeasurement = 0
velocity = 0


def setup():
    GPIO.setwarnings(False)
    GPIO.cleanup()
    GPIO.setmode(GPIO.BOARD)

    for trig in TRIG:
        GPIO.setup(trig, GPIO.OUT)
        GPIO.output(trig, False)

    for echo in ECHO:
        GPIO.setup(echo, GPIO.IN)

    for motor in MOTOR:
        GPIO.setup(motor, GPIO.OUT)
        GPIO.output(motor, False)


def measure(i):
    GPIO.output(TRIG[i], True)
    time.sleep(0.00001)
    GPIO.output(TRIG[i], False)

    msr_start = time.time()

    pulse_start = -1
    pulse_end = 0

    while GPIO.input(ECHO[i]) == 0:
        pulse_start = time.time()
        if time.time() - msr_start > 0.025:
            break

    while GPIO.input(ECHO[i]) == 1:
        pulse_end = time.time()
        if time.time() - msr_start > 0.025:
            break

    if time.time() - msr_start > 0.025:
        RESULT[i] = 1
    else:
        RESULT[i] = pulse_end - pulse_start

    time.sleep(WAITTIME)


def print_result(i):
    distance = RESULT[i] * MULTIPLIER
    distance = round(distance, 2)

    print("distance[" + str(i) + "] = " + str(distance) + " cm")


def clear_wdata(i):
    for n in range(len(WDATA[i])):
        WDATA[i][n] = 0


def save_result(i, file):
    DATA[i].append(RESULT[i])
    file.write(str(round(RESULT[i] * MULTIPLIER, 2)) + "\n")
    clear_wdata(i)
    successful_measurements[i] += 1
    print_result(i)


def check_results():
    global timeOfLastMeasurement
    with open(LOGFILE, "a+") as file:
        for i in range(len(RESULT)):
            if len(DATA[i]) >= 1 and RESULT[i] > 0:
                n = DATA[i][len(DATA[i]) - 1]

                if math.fabs(RESULT[i] - n) > timeFromDistance(MAX_DIFFERENCE):
                    if WDATA[i][0] == 0:
                        WDATA[i][0] = n
                    elif WDATA[i][1] == 0:
                        WDATA[i][1] = n
                    else:
                        if math.fabs(n - WDATA[i][0]) < timeFromDistance(MAX_DIFFERENCE):
                            if math.fabs(n - WDATA[i][1]) < timeFromDistance(MAX_DIFFERENCE):
                                save_result(i, file)
                            else:
                                clear_wdata(i)
                        else:
                            clear_wdata(i)
                else:
                    save_result(i, file)

                velocity = ((n - WDATA[i][0]) / float(100)) / float(time.time() - timeOfLastMeasurement) * 1000
                print(str(velocity) + " m/s")
                timeOfLastMeasurement = time.time()
            elif RESULT[i] > 0:
                save_result(i, file)
                file.write("\n")


def timeFromDistance(distance):
    return distance / float(MULTIPLIER)


def driveForward():
    global drivingForward
    global drivingBackward
    GPIO.output(MOTOR[0], True)
    drivingForward = True
    GPIO.output(MOTOR[1], False)
    drivingBackward = False

def driveBackward():
    global drivingForward
    global drivingBackward
    GPIO.output(MOTOR[0], False)
    drivingForward = False
    GPIO.output(MOTOR[1], True)
    drivingBackward = True

def stopdrive():
    global drivingForward
    global drivingBackward
    GPIO.output(MOTOR[0], False)
    drivingForward = False
    GPIO.output(MOTOR[1], False)
    drivingBackward = False

def steerLeft():
    GPIO.output(MOTOR[2], False)
    GPIO.output(MOTOR[3], True)

def steerRight():
    GPIO.output(MOTOR[2], True)
    GPIO.output(MOTOR[3], False)

def stopsteer():
    GPIO.output(MOTOR[2], False)
    GPIO.output(MOTOR[3], False)

def brake():
    BRAKETIME = 0.15
    if drivingForward:
        print("driving BACKWARD")
        driveBackward()
        time.sleep(BRAKETIME)
    elif drivingBackward:
        print("driving FORWARD")
        driveForward()
        time.sleep(BRAKETIME)
    stopdrive()

def turn():
    steerLeft()
    time.sleep(140 / float(velocity))
    stopsteer()


def drive1():
    for i in range(8):
        print(8 - i)
        time.sleep(1)
    driveForward()
    measure(0)
    check_results()
    while RESULT[0] > timeFromDistance(64):  #while distance is larger than 1m
        measure(0)
        check_results()
    brake()


def drive2():
    driveForward()
    start = time.time()
    measure(0)
    check_results()
    while (time.time() - start) < 0.5:  #while distance is larger than 1m
        measure(0)
        check_results()
    turn()
    stopdrive()


setup()

drive2()
