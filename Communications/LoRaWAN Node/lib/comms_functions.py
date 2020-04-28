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

# Colors
off = 0x000000
red = 0xff0000
green = 0x00ff00
blue = 0x0000ff

RING = 1
NO_RING = 2

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
    distance = pycom.nvs_get('dist')
    utime.sleep_us(100)
    print("distance = {0} inches".format(distance))
    utime.sleep_ms(100)
    #print("Gathering Light Data in:")
    utime.sleep_us(100)
    full, ir = tsl.get_full_luminosity()  # read raw values (full spectrum and ir spectrum)
    #full = 42.5
    lux = tsl.calculate_lux(full, ir)  # convert raw values to lux
    #print("full spectrum luminosity: {0}".format(full))
    #print("IR spectrum luminosity: {0}".format(ir))
    print("Calculated Lux value: {0}".format(lux))
    packet_light  = ustruct.pack('f',lux)
    packet_dist  = ustruct.pack('f',distance)
    #print("packed value:", packet_light)
    #print("unpacked lux value:", ustruct.unpack('f',packet_light))
    #print("unpacked distance value:", ustruct.unpack('f',packet_dist))
    full_packet = ustruct.pack('f', distance) + ustruct.pack('f', lux)

    return full_packet

def restore_lora():
    lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.US915, tx_power=20, bandwidth = LoRa.BW_500KHZ, sf=7, frequency = 903900000)
    lora.nvram_restore()
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
    s.send(make_payload())
    time.sleep(2)
    # make the socket non-blocking
    s.setblocking(False)
    # get any data received (if any...)
    data = s.recvfrom(128)
    print("received message: {0}".format(data))
#    except OSError as e:
#        if e.args[0] == 11:
#            # EAGAIN error occurred, add your retry logic here
#            time.sleep(2)
#            s.send(full_packet)
    return

def initialize_lora(name):
    print("first connection")
    lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.US915, tx_power=20, bandwidth = LoRa.BW_500KHZ, sf=7, frequency = 903900000)
    #remove all channels gateway doesn't use
    for channel in range(16, 72):
            lora.remove_channel(channel)
    for channel in range(0,7):
        lora.remove_channel(channel)
    #create an OTAA authentication parameters for no ring lopy
    if name == 1:
        dev_eui = ubinascii.unhexlify('70B3D549952757BF') # these settings can be found from TTN
        app_eui = ubinascii.unhexlify('70B3D57ED0028A4F')
        app_key = ubinascii.unhexlify('88397B010F71D34BEDF77DA003C3A54C')
    elif name == NO_RING:
        dev_eui = ubinascii.unhexlify('70B3D54990435DFE') # these settings can be found from TTN
        app_eui = ubinascii.unhexlify('70B3D57ED0028A4F')
        app_key = ubinascii.unhexlify('CE46C01958A612D102F0D106AB415862')
    else:
        dev_eui = ubinascii.unhexlify('70B3D54990435DFE') # these settings can be found from TTN
        app_eui = ubinascii.unhexlify('70B3D57ED0028A4F')
        app_key = ubinascii.unhexlify('CE46C01958A612D102F0D106AB415862')

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
    print("received message: {0}".format(data))

    return
