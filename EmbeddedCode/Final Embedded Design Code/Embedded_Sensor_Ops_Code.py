


#-----------------------------------------------------------------------------------------
#| Embedded_Sensor_Ops_Code.py
#| Senior Design Team 15 - Smart Storm Drain
#| Description: Primary device code for LoPy4 Microcontroller and Sensor Operation
#| Sensors Used: (2) JSN-SR04T 2.0 Waterproof Ultrasonic Distance Sensors
#|               (1) TSL2591 Digital Ambient Light Sensor
#|                        - Requires "tsl2591.py" file to operate!
#|               (1) Sparkfun Sound Detector (using Audio Envelope Output only)
#| Each Sensor requires 5V power input and a common GND rail in addition to I/O
#|
#| *Use "Embedded_Sensor_Ops_Code.py" & "tsl2591.py" TOGETHER with Communications code "LoPy_Ring.py"
#| or "LoPy_No_Ring.py" in order to integrate embedded sensing code w/ communications code to pass
#| real sensor data to the database/webpage. Modify the comms code by adding in functions found in this
#|  file as Lopy_Ring and LoPy_No_Ring currently send filler/dummy data in their current implementation*
#-----------------------------------------------------------------------------------------
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
import tsl2591 # Ambient Light Sensor library file

#-----------------------------------------------------------------------------------------
#| Setup ADC Configuration:
#| Initialize ADC using configured Vref value (1108 mV) and 12 bits of resolution
#-----------------------------------------------------------------------------------------
adc = ADC(0)
adc.vref(1108)
adc.init(bits=12)

#-----------------------------------------------------------------------------------------
#| Initialize Sensor Pinouts - Both GPIO and ADC
#|
#| Dual JSN-SR04T 2.0 Ultrasonic Sensors (Which sensor is #1 vs #2 does not matter):
#|    - Sensor 1: Trigger => Pin 21 ("trigger_1"); used as 3.3V GPIO Output from uC to sensor
#|    - Sensor 1: Echo    => Pin 22 ("echo_1"); used as 3.3V (Down from 5V) Input to UC from sensor
#|    - Sensor 2: Trigger => Pin 23 ("trigger_2"); used as 3.3V GPIO Output from uC to sensor
#|    - Sensor 2: Echo    => Pin 18 ("echo_2"); used as 3.3V (Down from 5V) Input to UC from sensor
#|
#| TSL2591 Ambient Light Sensor (initialize using "tsl = tsl2591.Tsl2591(0)" statement,
#|                               pins provided below only for reference):
#|    - SCL (for I2C) => Pin 9; Configured in included tsl2591.py file, not here
#|    - SDA (for I2C) => Pin 10; Configured in included tsl2591.py file, not here
#|
#| Sparkfun Sound Detector:
#|    - Envelope => Pin 13 ("audioEnvelope"); used as ADC Input w/ 11DB Attenuation for nearly linear 0-3.3V range
#|
#| *For battery voltage monitoring: Hookup voltage input to Pin 15 ("battery_voltage")
#| *To enable Opto-JFET to allow 5V power to sensors, Pin 19 is used ("sensor_power")
#-----------------------------------------------------------------------------------------
trigger_1 = Pin('P21', mode=Pin.OUT)
echo_1 = Pin('P22', mode=Pin.IN)
trigger_2 = Pin('P23', mode=Pin.OUT)
echo_2 = Pin('P18', mode=Pin.IN)

tsl = tsl2591.Tsl2591(0) #Pins 9 and 10 are dedicated to the Ambient Light Sensor

audioEnvelope = adc.channel(pin='P13', attn=ADC.ATTN_11DB)

battery_voltage=adc.channel(pin='P15',attn=ADC.ATTN_11DB)

sensor_power = Pin('P19', mode=Pin.OUT)
#-----------------------------------------------------------------------------------------
#| Initialize Misc. Variables used during operation:
#-----------------------------------------------------------------------------------------
count = 0
sleep_time = 10000
latest_readings = []
distance_to_use = 0
flow_rate_integer = -1
presence_of_debris = False
pycom.heartbeat(False)

#-----------------------------------------------------------------------------------------
#| Initialize and Configure Threshold Values used to determine Flow Rate:
#|  Sound Levels, Ambient Light Levels,  and Water levels based upon environment specific
#|  to each device
#-----------------------------------------------------------------------------------------

 # Sound values refer to adc value of # out of 4095. Configure these values based on your own
 # testing feedback of values based on 30dB-40dB for low, 40-60dB for medium, and 60+dB for high.
Sound_Level_low = 270
Sound_Level_medium = 400
Sound_Level_high = 600

# Water level values refer to the distance from the sensor head to the surface of the water.
# These values will need to be configured baased for each device based upon actual distance
# to top of the storm drain outlet from the sensor head.
Water_Level_normal = 11
Water_Level_high = 10

# Ambient light levels refer to the lux values obtained from the tsl2591 sensor. Run tests with
# your sensors to identify "high" vs. "low" values of your own, or use these as default.
Ambient_Light_low = 30
Ambient_Light_high = 50

#
NORMAL_FLOW_RATE = 1
HIGH_FLOW_RATE = 2
CLOG_FLOW_RATE = 0
#-----------------------------------------------------------------------------------------
#| Function: distance_measure([input] trigger_#, [output] echo_#)
#|  Description: Takes 1 sample of distance reading from given sensor and returns value
#|  Uses functionality of JSN-SR04T to operate by triggering LOW & HIGH pulses and then
#|  waiting for the return of an echo pulse before measuring the time in between.
#-----------------------------------------------------------------------------------------
# Ultrasonic distance measurement
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

#-----------------------------------------------------------------------------------------
#| Function: distance_median([input] trigger_#, [output] echo_#)
#|  Description: takes 10 samples of distance from given sensor and returns the median value.
#|  Utilizes distance_measure() function above.
#-----------------------------------------------------------------------------------------

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
    return int(distance_median)

#-----------------------------------------------------------------------------------------
#| Function: measure_audio_IIR(integer n)
#|  Description: takes 'n' samples of audio envelope ADC input and uses an IIR digital filter
#|  structure to differentiate Signal from Noise. IIR filters account for previous output Values
#|  when determining new output values.
#-----------------------------------------------------------------------------------------
def measure_audio_IIR(n):
    # initialise the lists
    stats = []
    output = audioEnvelope() # Initial ADC_Output Value
    # take 10 samples and append them into the list
    for count in range(n):
        output += ((audioEnvelope() - output) / max(count,1))
        utime.sleep_ms(10)
    stats.append(output)
    return stats

#-----------------------------------------------------------------------------------------
#| Function: measure_battery_voltage(integer n)
#|  Description: takes 'n' samples of battery voltage ADC input and averages value
#|
#-----------------------------------------------------------------------------------------
def measure_battery_voltage(n):
    # Initialize lists
    samples = []
    stats = []
    # take 10 samples and append them into the list
    for count in range(n):
        samples.append(audioEnvelope.voltage())
        utime.sleep_ms(10)
    samples = sorted(samples)
    stats.append(sum(samples) / len(samples)) #Average
    # Return the average
    return stats

#-----------------------------------------------------------------------------------------
#| Function: determine_flow_rate(water_level, sound_level, ambient_light_level)
#|  Description: takes 3 parameters and determines "flow rate" from these parameters
#|  Returns integer value = 1 for "Normal" flow rate, 2 for "High", and 0 for a "Clog". These
#|  return values are the implementation used in the Communications code & database code.
#-----------------------------------------------------------------------------------------

def determine_flow_rate(water_level, sound_level, ambient_light_level):
    if((water_level > Water_Level_normal) and (sound_level < Sound_Level_medium) and (ambient_light_level > Ambient_Light_high)):
        print("Flow Rate = NORMAL")
        return NORMAL_FLOW_RATE
    if((water_level < Water_Level_normal) and (sound_level > Sound_Level_medium) and (ambient_light_level < Ambient_Light_high)):
        print("Flow Rate = HIGH")
        return HIGH_FLOW_RATE
    if((water_level < Water_Level_normal) and (sound_level < Sound_Level_medium) and (ambient_light_level > Ambient_Light_high)):
        print("Flow Rate = LOW. Potential Clog Detected.")
        return CLOG_FLOW_RATE
    else:
        return "Flow Rate Sensing Abnormality. Check sensor values."

#-----------------------------------------------------------------------------------------
#| REGULAR OPERATIONAL LOOP BELOW - RUNS IF uC AWAKES FROM DEEPSLEEP MODE
#|
#| *This is proof-of-concept code that does not communicate data. In order to transmit gathered
#| from these sensors, the functions & initializations in this code will need to  be added to
#| either the "LoPy_Ring.py" or "LoPy_No_Ring.py" code found in the Communications/LoRaWAN Node folder.
#| The While True: loops below should mainly be used to prove that the sensors are operating correctly.
#| *
#-----------------------------------------------------------------------------------------

while True:
    if machine.reset_cause() == machine.DEEPSLEEP_RESET:
        print("Gathering Environmental Metrics:")
        sensor_power(1) #Enable to Opto-JFET High to deliver 5V to all sensors
        # take distance measurment, turn the light blue when measuring
        pycom.rgbled(0x0000ff)
        presence_of_debris = False
        print("battery voltage= {0} V".format(measure_battery_voltage*1.4))
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
        latest_readings = measure_audio_IIR(100)
        print("Audio Levels for 100 samples (AVG) = {0}".format(latest_readings[0]))
        full, ir = tsl.get_full_luminosity()  # read raw values (full spectrum and ir spectrum)
        lux = tsl.calculate_lux(full, ir)  # convert raw values to lux
        print("full spectrum luminosity: {0}".format(full))
        print("IR spectrum luminosity: {0}".format(ir))
        print("Calculated Lux value: {0}".format(lux))
        print("Determining Flow Rate:")
        print("...")
        flow_rate_integer = determine_flow_rate(distance_to_use,latest_readings[0], full)
        print("...")
        print("preparing to deepsleep for {0} milllieconds".format(sleep_time))
        sensor_power(0) #Disable Opto-JFET LOW to cut power to all sensors to eliminate quiescent current
        machine.deepsleep(sleep_time)

#-----------------------------------------------------------------------------------------
#| INITIAL BOOTUP OPERATION BELOW - RUNS IF uC FULLY RESET (Not from Deep Sleep)
#|
#-----------------------------------------------------------------------------------------

    else:
        print("Initial Power-on Process Beginning")
        sensor_power(1) #Enable to Opto-JFET High to deliver 5V to all sensors
        print("Gathering Environmental Metrics:")
        # take distance measurment, turn the light blue when measuring
        pycom.rgbled(0x0000ff)
        presence_of_debris = False
        print("battery voltage= {0} V".format(measure_battery_voltage*1.4))
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
        latest_readings = measure_audio_IIR(100)
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
        flow_rate_integer = determine_flow_rate(distance_to_use,latest_readings[0], full)
        print("...")
        print("preparing to deepsleep for {0} milllieconds".format(sleep_time))
        sensor_power(0) #Disable Opto-JFET LOW to cut power to all sensors to eliminate quiescent current
        machine.deepsleep(sleep_time)
