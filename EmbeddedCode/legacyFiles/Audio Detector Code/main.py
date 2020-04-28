# main.py -- put your code here!
import time
import utime
from machine import Pin
from machine import I2C
from machine import ADC
import pycom
from network import LoRa
import socket
import machine
import ubinascii
adc = ADC(0)
adc.vref(1108)
adc.init(bits=12)

audioEnvelope = adc.channel(pin='P13', attn=ADC.ATTN_11DB)

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

count = 1
latest_readings = []
all_readings = []
final_stats = []
while count <= 25:
    latest_readings = measure_audio(10)
    print("Audio Levels for 10 samples (AVG) = {0}".format(latest_readings[0]))
    print("Audio Levels for 10 samples (20th,50th,80th) = {0}, {0}, {0}".format(latest_readings[1],latest_readings[2],latest_readings[3]))
    all_readings = all_readings + latest_readings
    #print(audioEnvelope.voltage())
    utime.sleep_ms(100)
    count = count + 1

all_readings = sorted(all_readings)
final_stats.append(all_readings[int(len(all_readings)*0.2)]) #20th percentile
final_stats.append(all_readings[int(len(all_readings)*0.5)]) #50th percentile
final_stats.append(all_readings[int(len(all_readings)*0.8)]) #80th percentile
print("...")
print("Metrics from 5 seconds of Detection: ")
print("Audio Level Average = {0}".format(sum(all_readings) / len(all_readings)))
print("Percentiles for samples (20th, 50th, 80th) = {0}".format(final_stats))
