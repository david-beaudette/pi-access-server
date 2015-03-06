#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Example program to send packets to the radio link
#


import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
from lib_nrf24 import NRF24
import time
import logging
import spidev

import link_command

GPIO.setwarnings(False)

logging.basicConfig(format='%(levelname)s:%(message)s',
                    level=logging.DEBUG)

pipes = [[0xF0, 0xF0, 0xF0, 0xF0, 0xD2], [0xF0, 0xF0, 0xF0, 0xF0, 0xE1]]

radio = NRF24(GPIO, spidev.SpiDev())

# Use configuration file parameter values to setup radio
radio.begin(0, 25)
time.sleep(1)
radio.setRetries(15,15)
radio.setPayloadSize(10)
#radio.setChannel(0x4C)

radio.setDataRate(NRF24.BR_1MBPS)
radio.setPALevel(NRF24.PA_MAX)
radio.setAutoAck(True)
radio.enableDynamicPayloads()

radio.openWritingPipe(pipes[1])
radio.openReadingPipe(1, pipes[0])
radio.printDetails()

link = link_command.LinkCommand(radio, 0x4C, 1, "Degauchisseuse")

print link.auto()
print link.enable_machine()
print link.disable_machine()

new_table =          [[[0x70, 0x40, 0x84, 0x0B],
                       [0x45, 0x55, 0x55, 0x55],
                       [0x67, 0x89, 0x23, 0x11],
                       [0xA5, 0x5F, 0x78, 0xBC],
                       [0x55, 0x55, 0x84, 0x0B],
                       [0x89, 0x23, 0x11, 0xDE]],
                      [False, True, True, False, False, True]]

print link.dump_logging()

print link.update_table(new_table)

print link.check_memory()

print link.clear_memory()
    
