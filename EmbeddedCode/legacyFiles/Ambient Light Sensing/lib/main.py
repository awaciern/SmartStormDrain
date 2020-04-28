# main.py -- put your code here!
import time
import utime
from machine import Pin
from machine import I2C
import tsl2591
import pycom



tsl = tsl2591.Tsl2591(0)  # initialize tls2591
pycom.heartbeat(False)
cnt = 0

for cnt in range(5000):

    utime.sleep_ms(50)
    full, ir = tsl.get_full_luminosity()  # read raw values (full spectrum and ir spectrum)
    lux = tsl.calculate_lux(full, ir)  # convert raw values to lux
    if(ir > 70):
        pycom.rgbled(0xFF0900)
    elif(ir > 50 and ir < 70):
        pycom.rgbled(0xff7f00)
    elif(ir > 30 and ir < 50):
        pycom.rgbled(0x00ff00)
    elif(ir > 10 and ir < 30):
        pycom.rgbled(0x0000ff)
    elif(ir < 10):
        pycom.rgbled(0x4b0082)
    print(lux, full, ir)
    cnt = cnt + 1
