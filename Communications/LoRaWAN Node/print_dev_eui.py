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
import binascii

# Colors
off = 0x000000
red = 0xff0000
green = 0x00ff00
blue = 0x0000ff

pycom.heartbeat(False)
# Initialise LoRa in LORAWAN mode.
# Please pick the region that matches where you are using the device:
# Asia = LoRa.AS923
# Australia = LoRa.AU915
# Europe = LoRa.EU868
# United States = LoRa.US915
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.US915, tx_power=20, bandwidth = LoRa.BW_500KHZ, sf=7, frequency = 903900000)

def lora_cb(lora):
    events = lora.events()
    if events & LoRa.RX_PACKET_EVENT:
        print('Lora packet received')
    if events & LoRa.TX_PACKET_EVENT:
        print('Lora packet sent')
lora.nvram_erase()
#lora.nvram_restore()
# remove all the channels the gateway doesn't use
for channel in range(16, 72):
    lora.remove_channel(channel)
for channel in range(0,7):
    lora.remove_channel(channel)
#create an OTAA authentication parameters for test lopy
dev_eui = ubinascii.unhexlify('70B3D54997802DF8') # these settings can be found from TTN
app_eui = ubinascii.unhexlify('70B3D57ED0028A4F')
app_key = ubinascii.unhexlify('CE46C01958A612D102F0D106AB415862')

# create an OTAA authentication parameters for lopy with ring/ckt
#dev address  = 26012DBE
#dev_eui = ubinascii.unhexlify('70B3D549952757BF') # these settings can be found from TTN
#app_eui = ubinascii.unhexlify('70B3D57ED0028A4F')
#app_key = ubinascii.unhexlify('88397B010F71D34BEDF77DA003C3A54C')

# create an OTAA authentication parameters for no ring lopy
#dev address = 260125A9
#dev_eui = ubinascii.unhexlify('70B3D54990435DFE') # these settings can be found from TTN
#app_eui = ubinascii.unhexlify('70B3D57ED0028A4F')
#app_key = ubinascii.unhexlify('CE46C01958A612D102F0D106AB415862')

# join a network using OTAA (Over the Air Activation)
print(binascii.hexlify(lora.mac()).upper().decode('utf-8'))
