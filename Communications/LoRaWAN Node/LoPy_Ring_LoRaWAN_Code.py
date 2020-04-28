from network import LoRa
from machine import Pin
import pycom
import socket
import tsl2591
import time
import utime
import ustruct
import ubinascii
from machine import Timer
import machine
import uos
#import comms_functions
default_interval = 10
# Colors
off = 0x000000
red = 0xff0000
green = 0x00ff00
blue = 0x0000ff

if pycom.nvs_get('dist')==None or pycom.nvs_get('dist')>200:
    pycom.nvs_set('dist',0)
if pycom.nvs_get('v')==None or pycom.nvs_get('v')>40:
    pycom.nvs_set('v',0)

#set GPIO pins to appropriate values
trigger = Pin('P8', mode=Pin.OUT)
echo = Pin('P13', mode=Pin.IN)
trigger.value(0)

#initialize Ambient Light Sensor Object
#tsl = tsl2591.Tsl2591(0)

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
    distance = ((utime.ticks_diff(start, finish))* 0.0133858)/2

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

def make_payload():
    pycom.rgbled(blue)
    #distance = distance_median()
    count = pycom.nvs_get('dist')
    utime.sleep_us(100)
#randomize water distance
    distance = os.urandom(1)[0]
    print("distance = {0} inches".format(distance))
    utime.sleep_ms(100)
#subract 0.1V from battery voltage every 5 counts
    c = count
    v = pycom.nvs_get('v')
    if c%5 == 0:
        v += 1
        pycom.nvs_set('v',v)
    print("v={0}".format(v))
    voltage = 4.0 - v*0.1
    if voltage < 3.0:
        print("Battery below 3V")
        pycom.nvs_set('v',0)
    print("Measured Voltage: {0}V".format(voltage))
#randomize flow rate
    x = os.urandom(1)[0]
    flow_rate = x % 4
    if(flow_rate < 3):
        print(flow_rate)
    else:
        flow_rate-=1
        print(flow_rate)
    print("Flow Rate: {0}".format(flow_rate))
#generate encoded packet to send to webapp
    full_packet =ustruct.pack('f',count) + ustruct.pack('f', float(distance)) + ustruct.pack('f', voltage)+ustruct.pack('f',float(flow_rate))
    return full_packet

pycom.heartbeat(False)

# Initialise LoRa in LORAWAN mode.
# Please pick the region that matches where you are using the device:
# Asia = LoRa.AS923
# Australia = LoRa.AU915
# Europe = LoRa.EU868
# United States = LoRa.US915
#quick boot if state already saved to nvram
if machine.reset_cause() == machine.DEEPSLEEP_RESET:
    lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.US915, tx_power=20, bandwidth = LoRa.BW_500KHZ, sf=7, frequency = 903900000)
    lora.nvram_restore()
    print("Waking from deep sleep!")
    #print("setting up lora socket")
    # create a LoRa socket
    s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
    #set to confirmed type of messages
    # set the LoRaWAN data rate
    s.setsockopt(socket.SOL_LORA, socket.SO_DR, 3)
    # make the socket blocking
    # (waits for the data to be sent and for the 2 receive windows to expire)
    s.setblocking(True)
    # send some data
    packet = make_payload()
    s.send(packet)
    s.send(packet) #send twice to reduce packet loss.
    # make the socket non-blocking
    s.setblocking(False)
    # get any data received (if any...)
    data = s.recvfrom(128)
    #print("received message: {0}".format(data[0]))
    data_int = int.from_bytes(data[0],"big")
    if data_int != 0:
        print("received message: ",data_int)
        if data_int == 1:
            print("poweroff command received")
            machine.deepsleep()
        elif data_int == 2:
            print("6:00 interval requested")
            sleep_interval = 360000
        elif data_int == 3:
            print("12:00 interval requested")
            sleep_interval = 720000
        elif data_int == 4:
            print("30:00 interval requested")
            sleep_interval = 1800000
        elif data_int == 5:
            print("1 hour interval requested")
            sleep_interval = 3600000
        else:
            print("unknown command")
        data_int = 0
    else:
        sleep_interval = default_interval
        print("no message received")
#    except OSError as e:
#        if e.args[0] == 11:
#            # EAGAIN error occurred, add your retry logic here
#            time.sleep(2)
#            s.send(full_packet)
else:
    pycom.nvs_set('dist',0)
    print("Initial Boot: Initializing LoRa...\n")
    lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.US915, tx_power=20, bandwidth = LoRa.BW_500KHZ, sf=7, frequency = 903900000)
#remove all channels gateway doesn't use
    for channel in range(16, 72):
            lora.remove_channel(channel)
    for channel in range(0,7):
        lora.remove_channel(channel)
    #create an OTAA authentication parameters for ring lopy
    dev_eui = ubinascii.unhexlify('70B3D549952757BF') # these settings can be found from TTN
    app_eui = ubinascii.unhexlify('70B3D57ED0028A4F')
    app_key = ubinascii.unhexlify('88397B010F71D34BEDF77DA003C3A54C')

    if not lora.has_joined():
        lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)
        pycom.rgbled(green)
        time.sleep(2.5)
    handshk_time = Timer.Chrono()
    handshk_time.start()
    # wait until the module has joined the network
    while not lora.has_joined():
        pycom.rgbled(off)
        time.sleep(0.1)
        pycom.rgbled(red)
        time.sleep(2.4)
        print('Not yet joined...')
    lora.nvram_save()
    handshk_time.stop()
    print("Total handshake time: {0}".format(handshk_time.read()))
    print('Joined!')
    pycom.rgbled(blue)
    # create a LoRa socket
    s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
    #set to confirmed type of messages
    # set the LoRaWAN data rate
    s.setsockopt(socket.SOL_LORA, socket.SO_DR, 3)
    # make the socket blocking
    # (waits for the data to be sent and for the 2 receive windows to expire)
    s.setblocking(True)
    # send some data
    s.send(make_payload())
    # make the socket non-blocking
    s.setblocking(False)
    # get any data received (if any...)
    data = s.recvfrom(128)
    data = s.recvfrom(128)
    data_int = int.from_bytes(data[0],"big")
    #print("received message: {0}".format(data))
    if data_int != 0:
        print("received message: ",data_int)
        if data_int == 1:
            print("poweroff command received")
            machine.deepsleep()
        elif data_int == 2:
            print("baud rate change requested")
        else:
            print("unknown command")
        data_int = 0
    else:
        sleep_interval = default_interval
        print("no message received")
#receive = s.recvfrom(128)
#print(lora.stats(),'\n')
#store value on nvram for future use
pycom.nvs_set('dist', pycom.nvs_get('dist')+1)
lora.nvram_save()
machine.deepsleep(sleep_interval)
