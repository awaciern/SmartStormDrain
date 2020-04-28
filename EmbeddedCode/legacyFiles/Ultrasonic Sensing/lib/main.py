import utime
import pycom
import machine
from machine import Pin
from network import LoRa
import socket
import time
import ubinascii



    # initialise LoRa in LORA mode
    # Please pick the region that matches where you are using the device:
    # Asia = LoRa.AS923
    # Australia = LoRa.AU915
    # Europe = LoRa.EU868
    # United States = LoRa.US915
    # more params can also be given, like frequency, tx power and spreading factor

    # create a raw LoRa socket
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
    distance = ((utime.ticks_diff(start, finish)) * .0133858)/2

    return distance*-1

   # to reduce errors we take ten readings and use the median
def distance_median():

    # initialise the list
    distance_samples = []
    # take 10 samples and append them into the list
    for count in range(10):
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

count = 0
x = 1;
transmit = 3
receive = 1
s.settimeout(3)
# limit to 200 packets; just in case power is left on
while True:
    # take distance measurment, turn the light blue when measuring
    pycom.rgbled(0x00007d)
    #print("done 1")
    distance = distance_median()
    #print("done 2")
    utime.sleep_us(100)
    #print("done 3")
    print("distance = {0} inches".format(distance))
    #print("done 4")
    utime.sleep_ms(100)
    #print("done 5")
    pycom.rgbled(0x004600)
    #print("done 6")
    #s.setblocking(True)
    pycom.rgbled(0x001100)
    print('Sending distance')
    #print("done 7")
    #Sending...
    pycom.rgbled(0x111100)
    s.send('{0}'.format(distance))
    #print("done 8")
