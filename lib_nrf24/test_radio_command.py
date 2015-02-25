#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Example program to send packets to the radio link
#


import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
from lib_nrf24 import NRF24
import time
import spidev



pipes = [[0xF0, 0xF0, 0xF0, 0xF0, 0xD2], [0xF0, 0xF0, 0xF0, 0xF0, 0xE1]]

radio = NRF24(GPIO, spidev.SpiDev())
radio.begin(0, 25)
time.sleep(1)
radio.setRetries(15,15)
radio.setPayloadSize(8)
radio.setChannel(0x4C)

radio.setDataRate(NRF24.BR_1MBPS)
radio.setPALevel(NRF24.PA_MAX)
radio.setAutoAck(True)
radio.enableDynamicPayloads()

radio.openWritingPipe(pipes[1])
radio.openReadingPipe(1, pipes[0])
radio.printDetails()

retryCount   = 10000
retryDelayUs = 1
c=1
while True:
    buf = [c]
    c = (c + 1) & 255
    # send a packet to receiver
    radio.stopListening()
    if radio.write(buf):
        print("Sent: %d" % buf[0])
        
    else:
        print("Tx Failed.")

    # Turn to receiver
    radio.startListening()
    retry = 0
    while (not radio.available()) and retry < retryCount:
        time.sleep(retryDelayUs/1000000.0)
        retry += 1
    if retry < retryCount:
        rx_buf = []
        radio.read(rx_buf, radio.getDynamicPayloadSize())
        print("Received "),
        print(rx_buf),
        print(" after %d us." % (retry * retryDelayUs))
    else:
        print ("Nothing received.")        
    
    time.sleep(3)
