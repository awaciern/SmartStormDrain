# main.py -- put your code here!
import time
import utime
from machine import Pin
from machine import I2C
import pycom
from network import LoRa
from machine import ADC
import socket
import machine
import ubinascii
import tsl2591

#Setup and Configuration
#Initialize Sensor Pinout
adc = ADC(0)
adc.vref(1108)
adc.init(bits=12)
trigger_1 = Pin('P21', mode=Pin.OUT)
echo_1 = Pin('P22', mode=Pin.IN)
trigger_2 = Pin('P23', mode=Pin.OUT)
echo_2 = Pin('P18', mode=Pin.IN)
audioEnvelope = adc.channel(pin='P13', attn=ADC.ATTN_11DB)
#Pins 9 and 10 are dedicated to the Ambient Light Sensor
tsl = tsl2591.Tsl2591(0)

#Initialize ADC
count = 0
sleep_time = 10000
latest_readings = []
distance_to_use = 0
presence_of_debris = False
pycom.heartbeat(False)

#Sensor Threshold values
Sound_Level_low = 270
Sound_Level_medium = 400
Sound_Level_high = 600

Water_Level_normal = 11
Water_Level_high = 10

Ambient_Light_low = 30
Ambient_Light_high = 50


# Ultrasonic distance measurment
def distance_measure(trigger, echo):
    # trigger pulse LOW for 2us (just in case)
    trigger(0)
    utime.sleep_us(2)
    # trigger HIGH for a 10us pulse
    trigger(1)
    utime.sleep_us(20)
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
def distance_median(trigger, echo):
    # initialise the list
    distance_samples = []
    # take 10 samples and append them into the list
    for count in range(10):
        distance_samples.append(int(distance_measure(trigger, echo)))
    # sort the list
    distance_samples = sorted(distance_samples)
    # take the center list row value (median average)
    distance_median = distance_samples[int(len(distance_samples)/2)]
    # apply the function to scale to volts
    #print(distance_samples)
    return int(distance_median)
# Audio Sensor Measuring Function
def measure_audio(n):
    # initialise the list
    samples = []
    stats = []
    # take 10 samples and append them into the list
    for count in range(n):
        samples.append(audioEnvelope.voltage())
        utime.sleep_ms(10)
    samples = sorted(samples)
    stats.append(sum(samples) / len(samples))
    stats.append(samples[int(len(samples)*0.2)]) #20th percentile
    stats.append(samples[int(len(samples)*0.5)]) #50th percentile
    stats.append(samples[int(len(samples)*0.8)]) #80th percentile
    return stats


while True:
    if machine.reset_cause() == machine.DEEPSLEEP_RESET:
        pycom.rgbled(0xFFFF00)
        time.sleep(1)
        pycom.rgbled(0x999900)
        time.sleep(1)
        pycom.rgbled(0x555500)
        time.sleep(1)
        pycom.rgbled(0x442200)
        time.sleep(1)
        pycom.rgbled(0x39035D)
        print("Gathering Environmental Metrics:")
        # take distance measurment, turn the light blue when measuring
        pycom.rgbled(0x0000ff)
        presence_of_debris = False
        distance_1 = distance_median(trigger_1,echo_1)
        utime.sleep_ms(100)
        distance_2 = distance_median(trigger_2,echo_2)
        if(abs(distance_1 - distance_2) > 2):
            print("Distance mismatch detected.")
            presence_of_debris = True
        if(distance_1 < distance_2):
            print("distance_2 = {0} in".format(distance_2))
            distance_to_use = distance_2
        else:
            print("distance_1 = {0} in".format(distance_1))
            distance_to_use = distance_1
        utime.sleep_ms(100)
        pycom.rgbled(0x000000)
        latest_readings = measure_audio(100)
        print("Audio Levels for 100 samples (AVG) = {0}".format(latest_readings[0]))
        full, ir = tsl.get_full_luminosity()  # read raw values (full spectrum and ir spectrum)
        lux = tsl.calculate_lux(full, ir)  # convert raw values to lux
        print("full spectrum luminosity: {0}".format(full))
        print("IR spectrum luminosity: {0}".format(ir))
        print("Calculated Lux value: {0}".format(lux))
        print("Determining Flow Rate:")
        print("...")
        if((distance_to_use > Water_Level_normal) and (latest_readings[0] < Sound_Level_medium) and (full > Ambient_Light_high)):
            print("Flow Rate = NORMAL")
        if((distance_to_use < Water_Level_normal) and (latest_readings[0] > Sound_Level_medium) and (full < Ambient_Light_high)):
            print("Flow Rate = HIGH")
        if((distance_to_use < Water_Level_normal) and (latest_readings[0] < Sound_Level_medium) and (full > Ambient_Light_high)):
            print("Flow Rate = LOW. Potential Clog Detected.")
        print("...")
        print("preparing to deepsleep for {0} milllieconds".format(sleep_time))
        machine.deepsleep(sleep_time)
    else:
        print("Initial Power-on Process Beginning")
        pycom.rgbled(0xFF0000)  # Red
        time.sleep(1)
        pycom.rgbled(0x00FF00)  # Green
        time.sleep(1)
        pycom.rgbled(0x0000FF)  # Blue
        time.sleep(1)
        pycom.rgbled(0xFF0000)  # Red
        time.sleep(1)
        pycom.rgbled(0x00FF00)  # Green
        time.sleep(1)
        pycom.rgbled(0x0000FF)  # Blue
        time.sleep(1)
        print("...")
        print("Gathering Environmental Metrics:")
        # take distance measurment, turn the light blue when measuring
        pycom.rgbled(0x0000ff)
        presence_of_debris = False
        distance_1 = distance_median(trigger_1,echo_1)
        utime.sleep_ms(100)
        distance_2 = distance_median(trigger_2,echo_2)
        if(abs(distance_1 - distance_2) > 2):
            print("Distance mismatch detected.")
            presence_of_debris = True
        if(distance_1 < distance_2):
            print("distance_2 = {0} in".format(distance_2))
            distance_to_use = distance_2
        else:
            print("distance_1 = {0} in".format(distance_1))
            distance_to_use = distance_1
        utime.sleep_ms(100)
        pycom.rgbled(0x000000)
        latest_readings = measure_audio(100)
        print("Audio Levels for 100 samples (AVG) = {0}".format(latest_readings[0]))

        full, ir = tsl.get_full_luminosity()  # read raw values (full spectrum and ir spectrum)
        lux = tsl.calculate_lux(full, ir)  # convert raw values to lux
        print("full spectrum luminosity: {0}".format(full))
        time.sleep(1)
        print("IR spectrum luminosity: {0}".format(ir))
        time.sleep(1)
        print("Calculated Lux value: {0}".format(lux))
        #Determine Flow Rate Category:
        print("Determining Flow Rate:")
        print("...")
        if((distance_to_use > Water_Level_normal) and (latest_readings[0] < Sound_Level_medium) and (full > Ambient_Light_high)):
            print("Flow Rate = NORMAL")
        if((distance_to_use < Water_Level_normal) and (latest_readings[0] > Sound_Level_medium) and (full < Ambient_Light_high)):
            print("Flow Rate = HIGH")
        if((distance_to_use < Water_Level_normal) and (latest_readings[0] < Sound_Level_medium) and (full > Ambient_Light_high)):
            print("Flow Rate = LOW. Potential Clog Detected.")
        print("...")
        print("preparing to deepsleep for {0} milllieconds".format(sleep_time))
        machine.deepsleep(sleep_time)
