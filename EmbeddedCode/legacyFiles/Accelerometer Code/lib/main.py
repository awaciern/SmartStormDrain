# main.py -- put your code here!
import time
import utime
from machine import Pin
from machine import I2C
import pycom
from network import LoRa
import socket
import machine
import ubinascii
from machine import ADC

pycom.wifi_on_boot(False)
adc = machine.ADC()             # create an ADC object
adc.init(bits=12)
adc.vref(1108)

x_axis = adc.channel(pin='P16',attn=ADC.ATTN_11DB)   # create an analog pin on P16
val_x = x_axis()                    # read an analog value

y_axis = adc.channel(pin='P17',attn=ADC.ATTN_11DB)
val_y = y_axis()

z_axis = adc.channel(pin='P18',attn=ADC.ATTN_11DB)
val_z = z_axis()

def measure_xyz(n):
    # initialise the list
    samples_x = []
    samples_y = []
    samples_z = []
    # take 10 samples and append them into the list
    for count in range(n):
        samples_x.append(arduino_map(x_axis(),0,4095,-3,3))
        samples_y.append(arduino_map(y_axis(),0,4095,-3,3))
        samples_z.append(arduino_map(z_axis(),0,4095,-3,3))
        utime.sleep_ms(2)
    samples = []
    samples.append((sum(samples_x) / len(samples_x)))
    samples.append((sum(samples_y) / len(samples_y)))
    samples.append((sum(samples_z) / len(samples_z)))
    return samples

# Python program to get average of a list
def mean(lst):
    return sum(lst) / len(lst)

x_still = 1950
y_still = 2300
z_still = 1960
x_datapoints = []
y_datapoints = []
z_datapoints = []

count = 1

def arduino_map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

while count <= 50:
    raw_x = x_axis()
    voltage_x = x_axis.voltage()
    scaled_x = arduino_map(x_axis(),0,4095,-3,3)
    raw_y = y_axis()
    voltage_y = y_axis.voltage()
    scaled_y = arduino_map(y_axis(),0,4095,-3,3)
    raw_z = z_axis()
    voltage_z = z_axis.voltage()
    scaled_z = arduino_map(z_axis(),0,4095,-3,3)
    samples = measure_xyz(10) #Gather 10 samples over 20 milliseconds

    x_datapoints.append(raw_x)
    y_datapoints.append(raw_y)
    z_datapoints.append(raw_z)

    #print("Voltage (mV,1650=0g): {},{},{}".format(voltage_x,voltage_y,voltage_z))
    print("RAW (ADC output, 0-4095): {}, {}, {}".format(raw_x,raw_y,raw_z))
    #print("SCALED (g force): {},{},{}".format(scaled_x,scaled_y,scaled_z))
    #print("Average values over 10 readings = {}".format(samples))
    print("Average values over total time: {}, {}, {}".format(mean(x_datapoints), mean(y_datapoints),mean(z_datapoints)))

    utime.sleep_ms(80)
    count = count+1
print(x_datapoints)
current = 0
turbulent_events = []
while current < len(x_datapoints):
    if(abs(x_datapoints[current] - 1950) > 200):
        #print("Turbulence for event {}".format(current))
        turbulent_events.append(current)
    current += 1

if(len(turbulent_events) > 11):
    print("There were {} turbulent events.".format(len(turbulent_events)))
    print("Turbulence = HIGH")
elif((len(turbulent_events) > 7) and (len(turbulent_events) < 11)):
    print("There were {} turbulent events. Turbulence = MEDIUM".format(len(turbulent_events)))
else:
    print("Only {} turbulent events, so Turbulence = LOW".format(len(turbulent_events)))
