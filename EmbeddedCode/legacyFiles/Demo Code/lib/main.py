# main.py -- put your code here!
import time
import utime
from machine import Pin
from machine import I2C
import tsl2591
import pycom
from network import LoRa
import socket
import machine
import ubinascii


lora = LoRa(mode=LoRa.LORA, region=LoRa.US915, bandwidth=LoRa.BW_500KHZ, sf=7)

    # create a raw LoRa socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
trigger = Pin('P7', mode=Pin.OUT)
echo = Pin('P8', mode=Pin.IN)


trigger.value(0)


# Ultrasonic distance measurment
def distance_measure():
    # trigger pulse LOW for 2us (just in case)
    trigger(0)
    utime.sleep_us(2)
    # trigger HIGH for a 10us pulse
    trigger(1)
    utime.sleep_us(10)
    trigger(0)

    # wait for the rising edge of the echo then start timer
    while echo() == 0:
        pass
    start = utime.ticks_us()

    # wait for end of echo pulse then stop timer
    while echo() == 1:
        pass
    finish = utime.ticks_us()

    # pause for 20ms to prevent overlapping echos
    utime.sleep_ms(20)

    # calculate distance by using time difference between start and stop
    # speed of sound 340m/s or .034cm/us. Time * .034cm/us = Distance sound travelled there and back
    # divide by two for distance to object detected.
    # Note: changing the multiplying factor to 0.0133858 for inches
    distance = ((utime.ticks_diff(start, finish)) * 0.0133858)/2

    return distance*-1

   # to reduce errors we take ten readings and use the median
def distance_median():

    # initialise the list
    distance_samples = []
    # take 10 samples and append them into the list
    for count in range(1000):
        distance_samples.append(int(distance_measure()))
    # sort the list
    distance_samples = sorted(distance_samples)
    # take the center list row value (median average)
    distance_median = distance_samples[int(len(distance_samples)/2)]
    # apply the function to scale to volts

    print(distance_samples)

    return int(distance_median)

# disable LED heartbeat (so we can control the LED)
pycom.heartbeat(False)
# set LED to red
pycom.rgbled(0x7f0000)

#initialize Ambient Light Sensor Object
tsl = tsl2591.Tsl2591(0)

while True:
    # take distance measurment, turn the light blue when measuring
    pycom.rgbled(0x0000ff)
    distance = distance_median()
    utime.sleep_us(100)
    print("distance = {0} in".format(distance))
    utime.sleep_ms(100)
    pycom.rgbled(0x000000)
    #pycom.rgbled(0x111100) #dim yellow
    print("Gathering Light Data in:")
    print("5")
    time.sleep(1)
    print("4")
    time.sleep(1)
    print("3")
    time.sleep(1)
    print("2")
    time.sleep(1)
    print("1")
    time.sleep(1)
    full, ir = tsl.get_full_luminosity()  # read raw values (full spectrum and ir spectrum)
    lux = tsl.calculate_lux(full, ir)  # convert raw values to lux
    print("full spectrum luminosity: {0}".format(full))
    time.sleep(1)
    print("IR spectrum luminosity: {0}".format(ir))
    time.sleep(1)
    print("Calculated Lux value: {0}".format(lux))
    time.sleep(1)
    #print("LED brightness will indicate relative luminosity for demonstration")
    if(ir > 70):
        pycom.rgbled(0xFFFF00)
    elif(ir >= 50 and ir < 70):
        pycom.rgbled(0x999900)
    elif(ir >= 30 and ir < 50):
        pycom.rgbled(0x555500)
    elif(ir >= 10 and ir < 30):
        pycom.rgbled(0x442200)
    elif(ir < 10):
        pycom.rgbled(0x39035D)

    print("Gathering Distance Data in:")
    print("5")
    time.sleep(1)
    print("4")
    time.sleep(1)
    print("3")
    time.sleep(1)
    print("2")
    time.sleep(1)
    print("1")
    time.sleep(1)
