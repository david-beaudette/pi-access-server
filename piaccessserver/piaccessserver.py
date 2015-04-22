#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# The server main program
#

import sys
import ConfigParser
import time
import logging
import argparse

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
from lib_nrf24 import NRF24
import time
import spidev

import db_connect
import link_command
import csv_csvw

class PiAccessServer():
    """ Main application class for the access server of the RFID card
    control system.
    """
    def __init__(self, config_filename):
        # Get server parameters
        self.config_filename = config_filename
        self.config = ConfigParser.RawConfigParser()    
        self.config.read(self.config_filename)
        
        self.name = self.config.get('ACCESS_SERVER',
                                    'name')
        self.csv_filename = self.config.get('ACCESS_SERVER',
                                            'csv_filename')
        self.log_filename = self.config.get('ACCESS_SERVER',
                                               'log_filename')
        self.number_machines = self.config.get('MACHINES',
                                               'number_machines')
        self.mem_usage_threshold = self.config.getfloat('MACHINES',
                                               'mem_usage_threshold')

        # Initialise log file (time not added by default because machine
        # log entries have a differed timestamp
        logging.basicConfig(filename=self.log_filename,
                            format='%(levelname)s:%(message)s',
                            level=logging.DEBUG)
    
        # Get machine names from database
        if not self.load():
            return False

        # Initialise radio
        if not self.radio_init():
            return False

        # Create a link for each machine
        for machine in self.machines:
            # Load machine specific section from config file
            channel    = self.config.get(machine, 'channel')
            machine_id = self.config.get(machine, 'machine_id')
            # Initialise link for machine
            self.link[machine] = link_command.LinkCommand(self.radio,
                                                          channel,
                                                          machine_id)
        
    def load(self):
        # Initialise output arguments
        machines_db = []
        members_db = []
        cards_db = []
        tags_db = []
        
        # Read data from database
        if db_connect.read_db(machines_db, members_db,
                              cards_db, tags_db, self.config_filename):

            # If successful, write result in csv file
            member_access_write(self.csv_filename, machines_db,
                                members_db, cards_db, tags_db)

        # In any case, read from csv file
        machines_csv = []
        cards_csv = []
        authorisations_csv = []
        if not member_access_read(self.csv_filename,
                                  machines_csv,
                                  cards_csv,
                                  authorisations_csv):
            return False

        # Update cards list
        self.cards = cards_csv
        
        # Build an access table for each machine found in database AND config file
        self.machines = []
        self.authorisations = {}
        num_machines = 0
        for machine_num in range(len(machines_csv)):
            # Check if machine exists in config file
            machine_name = machines_csv[machine_num]
            if config.has_section(machine_name):
                self.machines.append(machine_name)
                self.authorisations[machine_name] = authorisations_csv[machine_num]
                num_machines += 1
        
        if self.number_machines > num_machines:
            logging.warning('Some of the machines in config file were not \
                             found in database.',
                            num_machines, self.number_machines)
            self.number_machines = num_machines
        
        return True
        
    def loop(self, config_filename, radio):
        # Initialise output arguments
        machines_db = []
        members_db = []
        cards_db = []
        tags_db = []
        
        # Refresh server configuration
        
        
        # Read data from database
        if not piaccessserver_load():
            return False

        # Update access entries for all machines
        for machine in self.machines:
            # Send command
            status = link_command.update_table([self.cards, self.authorisations[machine]])        

        # Retrieve log entries from all machines
        
            # Send command
            link_command.dump_logging
            
            # If there are any entries, write them to local log

        
        # Check memory usage on all machine

            # Send command

            # If memory exceeds threshold, write warning to local log
            
        # Wait for next loop iteration
        time.sleep(config.getfloat('ACCESS_SERVER', 'loop_delay'))


    def radio_init(self, config_filename):
        # TODO: Check what are those for and validate parameters
        # TODO: Check for initialisation errors from radio
        self.pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]

        self.radio = NRF24(GPIO, spidev.SpiDev())
        self.radio.begin(0, 25)
        time.sleep(1)
        # Set retries (delay, count)
        self.number_machines = self.config.get('MACHINES',
                                               'number_machines')
        self.radio.setRetries(15,15)
        self.radio.setPayloadSize(32)
        self.radio.setChannel(0x60)

        self.radio.setDataRate(NRF24.BR_2MBPS)
        self.radio.setPALevel(NRF24.PA_MIN)
        self.radio.setAutoAck(True)
        self.radio.enableDynamicPayloads()
        self.radio.enableAckPayload()

        self.radio.openWritingPipe(pipes[1])
        self.radio.openReadingPipe(1, pipes[0])
        self.radio.printDetails()

        return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Access server software on Raspberry Pi for managing RFID card readers on machines.')    
    
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    
    config_filename = 'piaccessserver.ini'
    server = PiAccessServer(config_filename)
    # Initialise server
    if not server.piaccessserver_init():
        sys.exit('Initialisation failed. Check log for details.')

    # Process server tasks
    while True:
        
        # Process tasks
        if not piaccessserver_loop(config_filename):
            sys.exit('Main loop failed. Check log for details.')

        
         

        
        
