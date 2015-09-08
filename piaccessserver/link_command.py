import time
from datetime import timedelta, datetime
import logging

class LinkCommand():
    """ A single radio is shared between several LinkCommand instances,
    each with its own RF channel.
    """
    def __init__(self, radio, channel, commutator_id, commutator_name):
        self.radio         = radio
        self.channel       = channel
        self.commutator_id    = commutator_id
        self.commutator_name  = commutator_name
        self.wait_rx_sleep = 0.000001
        self.wait_rx_retry = 10000
        self.num_retries   = 10
        self.retry_len     = 0.05
        
    def init_radio(self):
        """ Used to send any command and check for ACK """
        # Configure the radio on the right RF channel for the commutator
        self.radio.stopListening()
        self.radio.powerDown()
        self.radio.setChannel(self.channel)
        self.radio.powerUp()

        logging.debug("LinkCommand-init_radio: Radio initialised for %s on channel %d.",
                      self.commutator_name, self.channel)
        
    def send_command(self, command, rx_len = 1):
        """ Used to send any command and check for ACK """
        
        # Initialise radio
        self.init_radio()

        # Initialise outputs
        outarg = {"link_ok":    False,
                  "commutator_ok": False,
                  "reply_ok":   False,
                  "reply_buf":  []}
        
        read_buf = []
        read_check = False
        check_iter = 0
        while not read_check and check_iter < self.num_retries:
            if self.radio.write(command):
                # Write successful
                outarg["link_ok"] = True
                self.radio.startListening()
                if self.wait_rx():
                    logging.debug("Transmission of %s command acknowledged.",
                                  hex(command[0]))
                    self.radio.read(read_buf, rx_len)
                    if len(read_buf) == rx_len:
                        # Check received state
                        if   read_buf[0] == 0xA0:
                            outarg["reply_ok"]   = True
                            logging.error("Machine %s has a problem. Please verify.",
                                          self.commutator_name)
                            read_check = True
                        elif read_buf[0] == 0xAF:
                            outarg["commutator_ok"] = True
                            outarg["reply_ok"]   = True
                            read_check = True
                        else:
                            # The value is not expected
                            logging.warning("Machine %s reply state (%d) is unexpected (expecting 0 or 175).",
                                            self.commutator_name, read_buf[0])
                    else:
                        logging.warning("Machine %s reply data length (%d) should be %d.",
                                        self.commutator_name, len(read_buf), rx_len)

                else:
                    logging.warning("No response from %s.",
                                    self.commutator_name)
            check_iter += 1
            time.sleep(self.retry_len)
            
        for byte in read_buf:
            outarg["reply_buf"].append(byte)
        return outarg    
    
    def check(self):
        """ Send the check command."""
        return self.send_command([0xA9])
    
    def double_activation(self):
        """ Send the double_activation command."""
        return self.send_command([0xA7])
    
    def single_activation(self):
        """ Send the single_activation command."""
        return self.send_command([0xA8])
    
    def auto(self):
        """ Send the auto command."""
        return self.send_command([0xA0])
    
    def enable_commutator(self):
        """ Send the enable command."""
        return self.send_command([0xA1])

    def disable_commutator(self):
        """ Send the disable command."""
        return self.send_command([0xA2])

    def erase_log(self):
        """ Send the disable command."""
        return self.send_command([0xB0])

    def dump_logging(self):
        """ Send the dump logging command."""
        # Initialise outputs
        outarg = {"read_ok": False}
        outarg["log_count"] = 0
        outarg["log_codes"] = []
        outarg["log_users"] = []
        outarg["log_times"] = []

        # Ask for remaining entries one by one
        num_entries = 1
        while num_entries > 0:
            # Send command and validate commutator state
            cmd_state = self.send_command([0xA3], 12)
            outarg.update(cmd_state)

            if not (outarg["link_ok"] and
                    outarg["reply_ok"] and
                    outarg["commutator_ok"]):
                # Command was not executed successfully
                logging.warning("Unable to retrieve log entries from %s",
                                self.commutator_name)
                return outarg

            # Read the remainder of the packet
            read_buf = outarg["reply_buf"][1:]
            if len(read_buf) == 11:
                # Make sure first element is the command
                if (read_buf[0] != 0xA3):
                    logging.error("%s did not answer with sent command as expected.",
                                  self.commutator_name)
                    return outarg
                
                # Read number of remaining entries
                num_entries = read_buf[1]
                if num_entries == 0:
                    # No log entries to add
                    outarg["read_ok"] = True
                    logging.debug("No new log entries for %s.",
                                  self.commutator_name)
                    return outarg
                
                # Only update log count if higher
                outarg["log_count"] = max(num_entries, outarg["log_count"])
                outarg["log_codes"].append(read_buf[2])
                outarg["log_users"].append(read_buf[3:7])
                
                # Immediately convert elapsed time in seconds
                # to UTC date and time for logging
                unsigned_long_time = read_buf[7] + 256 * (read_buf[8] + 256 * (read_buf[9] + 256 * read_buf[10]))
                outarg["log_times"].append(datetime.now() - \
                                       timedelta(seconds=unsigned_long_time))
                logging.info("Machine: %s; Time: %s; Event code %s; User %s",
                             self.commutator_name,
                             str(outarg["log_times"][-1].strftime("%Y-%m-%d %H:%M:%S")),
                             hex(outarg["log_codes"][-1]),
                             hex(0x01000000 * outarg["log_users"][-1][0] + 
                             0x00010000 * outarg["log_users"][-1][1] + 
                             0x00000100 * outarg["log_users"][-1][2] + 
                             outarg["log_users"][-1][3]))
                             
                # Command commutator to erase this entry
                cmd_state = self.send_command([0xB0])
                outarg.update(cmd_state)
                if not (outarg["link_ok"] and
                        outarg["reply_ok"] and
                        outarg["commutator_ok"]):
                    # Command was not executed successfully
                    logging.warning("Unable to make %s delete an entry that's been written to event log file.",
                                    self.commutator_name)
                    return outarg

            else:
                # Not enough data bytes were received
                logging.error("Machine %s reply data length (%d) should be %d.",
                                  self.commutator_name, len(read_buf), 11)
                return outarg
        
        # Everything went fine
        outarg["read_ok"] = True  
        return outarg                
                    
    def update_table(self, table):
        """ Send each access table entry. The table is a 2 elements list:
            [0] List of 4 bytes card IDs (ex: table[0][14] = [112, 64, 132, 11])
            [1] List of booleans (ex: table[1][14] = True if card is authorized)
        """
        # Initialise outputs
        table_size = len(table[0])
        outarg = {"send_ok":    False,
                  "recv_ok":    False,
                  "commutator_ok": False,
                  "update_ok":  False,
                  "num_entries": table_size,
                  "num_authmod": 0,
                  "num_newcard": 0}
    
        # Initialise radio
        self.init_radio()
        
        for i in range(table_size):
            # Prepare data to be sent
            command = [0xA4, table_size-i]
            command.append(int(table[1][i])) # authorisation
            for byte_num in range(0, len(table[0][i]), 2):
                command.append(int(table[0][i][byte_num], 16) * 0x10 + 
                               int(table[0][i][byte_num+1], 16))
            num_retries = 0
            while not self.radio.write(command):
                time.sleep(0.010)
                num_retries = num_retries + 1
                if num_retries > 10:
                    logging.warning("Unable to write %s command to %s. Radio link is down.",
                                     hex(command[0]), self.commutator_name)
                    return outarg
            logging.debug("Command #%d sent.", i)
            # Wait for answer
            read_buf = []
            self.radio.startListening()
            if not self.wait_rx():
                # Only write operation succeeded, exit
                outarg["send_ok"] = True
                logging.warning("No response from %s.",
                                self.commutator_name)
                return outarg
            
            # Read received buffer
            self.radio.read(read_buf, 3)
            print read_buf
            if not len(read_buf) == 3:
                outarg["recv_ok"] = False
                logging.warning("Machine %s reply data length (%d) is abnormal.",
                                self.commutator_name, len(read_buf))
                return outarg
            
            # Check received state
            if read_buf[0] != 0xAF:
                # Machine has a problem, exit
                outarg["send_ok"] = True
                outarg["recv_ok"] = True
                logging.error("Machine %s has a problem. Please verify.",
                                  self.commutator_name)
                return outarg
                
            # Check command byte
            if read_buf[1] != 0xA4:
                # Returned command does not match, exit
                outarg["send_ok"] = True
                logging.error("%s did not answer with sent command as expected.",
                               self.commutator_name)
                return outarg
            
            # Check how this entry was managed
            if read_buf[2] == 0xD1:
                # No update was required for this card
                pass
            elif read_buf[2] == 0xD2:
                # Authorisation was modified for this card
                outarg["num_authmod"] += 1
            elif read_buf[2] == 0xD3:
                # New card added
                outarg["num_newcard"] += 1
            elif read_buf[2] == 0xDF:
                # Memory full, exit
                outarg["send_ok"] = True
                outarg["recv_ok"] = True
                logging.error("Memory full on %s. Upgrade Arduino device or remove unused user cards from database.")
                return outarg
            else:
                # Receive error, code not recognised, exit
                outarg["send_ok"] = True
                return outarg
            self.radio.stopListening()
            
        outarg["send_ok"] = True
        outarg["recv_ok"] = True
        outarg["update_ok"] = True
        outarg["commutator_ok"] = True

        logging.info("Table updated on %s; table size: %d; %d card numbers were added; %d authorisations were modified.",
                     self.commutator_name,
                     outarg["num_entries"],
                     outarg["num_newcard"],
                     outarg["num_authmod"])
                       
        return outarg
    
    def check_memory(self):
        outarg = {"read_ok": False}
        # Send command and validate commutator state
        cmd_state = self.send_command([0xA5], 6)
        outarg.update(cmd_state)
        
        if not (outarg["link_ok"] and
                outarg["reply_ok"] and
                outarg["commutator_ok"]):
            # Command was not executed successfully
            logging.warning("Unable to get memory size from %s",
                             self.commutator_name)
            return outarg

        # Read the remainder of the packet
        read_buf = outarg["reply_buf"][1:]
        if not len(read_buf) == 5:
            # Invalid message received
            logging.error("%s did not answer with enough bytes.",
                          self.commutator_name)
            return outarg

        # Make sure first element is the command
        if (read_buf[0] != 0xA5):
            logging.error("%s did not answer with sent command as expected.",
                               self.commutator_name)
            return outarg
        
        # Read memory state
        outarg["mem_size"] = read_buf[2] + read_buf[1] * 0x100
        outarg["mem_used"] = read_buf[4] + read_buf[3] * 0x100
        
        logging.info("Memory state on %s: %d/%d used.",
                     self.commutator_name, outarg["mem_used"],
                     outarg["mem_size"])

        outarg["read_ok"] = True
        return outarg

    def clear_memory(self):
        """ Send the clear memory command."""
        return self.send_command([0xA6])
    
    def wait_rx(self):
        num_retry = 0
        while not self.radio.available([0]):
            time.sleep(self.wait_rx_sleep)
            num_retry += 1
            if num_retry == self.wait_rx_retry:
                return False
        return True            

class DummyRadio():
    """ This test class mimics the behaviour of the lib_nrf24.py has used
        for this project. It also allows testing various errors that are
        less practical to generate with real hardware.
    """
    def __init__(self):
        # Error emulation
        self.b_link_err    = False
        self.b_commutator_err = False
        self.b_reply_err   = False
        
        self.link_errors    = {}
        self.commutator_errors = {}
        self.reply_errors   = {}
        
        # Communication buffers
        self.rx_buf = []
        self.tx_buf = []

        # Current channel
        self.channel = -1

        # Machine access table
        self.access_table = [[], []]
        self.mem_size = 0
        self.mem_used = 0

    def link_err(self, channel):    self.link_errors[hex(channel)] = True       
    def link_ok(self, channel):     self.link_errors[hex(channel)] = False       
    def commutator_err(self, channel): self.commutator_errors[hex(channel)] = True       
    def commutator_ok(self, channel):  self.commutator_errors[hex(channel)] = False       
    def reply_err(self, channel):   self.reply_errors[hex(channel)] = True       
    def reply_ok(self, channel):    self.reply_errors[hex(channel)] = False       
    def powerUp(self): pass
    def powerDown(self): pass

    def setChannel(self, channel):
        self.channel = channel
        # Set link error if specified for this channel
        if hex(channel) in self.link_errors:
            self.b_link_err = self.link_errors[hex(channel)]
        else:
            self.b_link_err = False
        # Set commutator error if specified for this channel
        if hex(channel) in self.commutator_errors:
            self.b_commutator_err = self.commutator_errors[hex(channel)]
        else:
            self.b_commutator_err = False
        # Set reply error if specified for this channel
        if hex(channel) in self.reply_errors:
            self.b_reply_err = self.reply_errors[hex(channel)]
        else:
            self.b_reply_err = False
        
    def write(self, buf):
        # Necessarily in TX mode
        self.rx_mode = False
        # Wait 10 ms
        time.sleep(0.010)
        if self.b_link_err:
            # No ack on write
            return False

        if self.b_reply_err:
            # Ack succeeded  but no reply was received
            return True
        
        # Return the expected reply from Arduino
        if (buf[0] == 0xA0 or
            buf[0] == 0xA1 or
            buf[0] == 0xA2 or
            buf[0] == 0xA7 or
            buf[0] == 0xA8 or
            buf[0] == 0xA9 or
            buf[0] == 0xB0):
            # Register, enable or disable command, answer state
            self.rx_buf = [0xAF - 0x0F * (self.b_commutator_err)]
            print("Machine would receive %s command, sending back %d." % (hex(buf[0]), self.rx_buf[0]))

        elif buf[0] == 0xA3:
            # Dump logging command, answer state first
            num_entries = len(self.log_code)
            if num_entries == 0:
                # Send empty log buffer
                self.rx_buf.append(0xAF + 0x0F * (self.b_commutator_err)) 
                # Repeat the command itself
                self.rx_buf.append(0xA3)
                # Number of remaining entries, including this one
                self.rx_buf.append(0)
                # Current entry code (1 byte) and user (4 bytes)
                self.rx_buf.append(0)
                for code_byte in [0,0,0,0]:
                    self.rx_buf.append(code_byte)
                # Current entry code time(4 bytes)
                self.rx_buf.append(0)
                self.rx_buf.append(0)
                self.rx_buf.append(0)
                self.rx_buf.append(0)
            else:
                # Dump 1 log entry
                self.rx_buf.append(0xAF + 0x0F * (self.b_commutator_err)) 
                # Repeat the command itself
                self.rx_buf.append(0xA3) 
                # Number of remaining entries, including this one
                self.rx_buf.append(num_entries) 
                # Current entry code (1 byte) and user (4 bytes)
                self.rx_buf.append(self.log_code[0])
                for user_byte in self.log_user[0]:
                    self.rx_buf.append(user_byte)
                # Current entry code time(4 bytes)
                age_bytes = struct.unpack("4B", struct.pack("I", self.log_age[0]))
                self.rx_buf.append(age_bytes[0])
                self.rx_buf.append(age_bytes[1])
                self.rx_buf.append(age_bytes[2])
                self.rx_buf.append(age_bytes[3])
                
                # Remove entry from log
                del self.log_code[0]
                del self.log_user[0]
                del self.log_age[0]
                print self.rx_buf

        elif buf[0] == 0xA4:
            # Table update
            # Machine state
            self.rx_buf.append(0xAF + 0x0F * (self.b_commutator_err)) 
            # Repeat the command itself
            self.rx_buf.append(0xA4)
            # Do nothing if the number of remaining entries is 0
            if buf[1] == 0:
                return True
            # Check if the card ID is in memory
            card_id = buf[3:7]
            user_auth = buf[2]
            if card_id in self.access_table[0]:
                user_auth_prev = self.access_table[1] \
                                [self.access_table[0].index(card_id)]
                # Check if authorisation was updated
                if user_auth_prev == user_auth:
                    self.rx_buf.append(0xD1)
                else:
                    self.rx_buf.append(0xD2)
            else:
                # Check if another user can fit in memory
                self.mem_used = len(self.access_table[0])
                if self.mem_used < self.mem_size:
                    self.rx_buf.append(0xD3)
                    self.access_table[0].append(card_id)
                    self.access_table[1].append(user_auth)
                else:
                    self.rx_buf.append(0xDF)
            
        elif buf[0] == 0xA5:
            # Dump 1 log entry
            self.rx_buf.append(0xAF + 0x0F * (self.b_commutator_err)) 
            # Repeat the command itself
            self.rx_buf.append(0xA5) 
            # Memory total size
            self.rx_buf.append(self.mem_size % 0x100) 
            self.rx_buf.append(int(self.mem_size / 0x100)) 
            # Memory used
            self.mem_used = len(self.access_table[0])
            self.rx_buf.append(self.mem_used % 0x100) 
            self.rx_buf.append(int(self.mem_used / 0x100))
            
        elif buf[0] == 0xA6:
            # Answer state
            self.rx_buf = [0xAF + 0x0F * (self.b_commutator_err)]
            # Remove all cards from memory
            self.access_table = [[],[]]
            radio.mem_used = 0
            
        return True
    
    def read(self, buf, buf_len=-1):
        del buf[:]
        # Read and empty RX buffer entries
        buf.extend(self.rx_buf[0:buf_len])
        del self.rx_buf[0:buf_len]
        return len(buf)
    
    def getDynamicPayloadSize(self):
        return len(self.rx_buf)

    def available(self, pipe_num):        
        return pipe_num == [0] and self.rx_mode
    
    def startListening(self):
        self.rx_mode = True
        return
    
    def stopListening(self):
        self.rx_mode = False
        return
    
    def flush_rx(self):
        del self.rx_buf[:]
        return True
    
    def flush_tx(self):
        del self.tx_buf[:]
        return True
    
# UNIT TEST (if script is executed directly)
if __name__ == '__main__':
    import struct
    logging.basicConfig(filename='test_link_command.log',
                        format='%(asctime)s:%(levelname)s:%(funcName)s:%(message)s',
                        level=logging.DEBUG)
    # Init shared radio
    radio = DummyRadio()

    # Define commutators
    num_commutators = 3
    channels = [32, 33, 34]
    commutator_ids = [0xA, 0xB, 0xC]
    commutator_names = ['Tour', 'Toupie', 'Banc de scie']

    # Create a link for each commutator
    links = []
    for n in range(num_commutators):
        links.append(LinkCommand(radio, channels[n],
                                 commutator_ids[n], commutator_names[n]))

    # 1st commutator (non-powered)
    radio.link_err(channels[0])
    print("\nThis commutator is non-powered.")
    print(links[0].check())
    
    # 2nd commutator (failed its self-test)
    radio.commutator_err(channels[1])
    print("\nThis commutator should report trouble.")
    print(links[1].check())

    # 3rd commutator (going fine)
    radio.reply_err(channels[2])
    print("\nThis commutator is not ready to acknowledge.")
    print(links[2].check())

    radio.reply_ok(channels[2])
    print("\nThis commutator is now ready.")
    print(links[2].check())

    print("\nReply from auto command.")
    print(links[2].auto())

    print("\nReply from double activation command.")
    print(links[2].double_activation())

    print("\nReply from single activation command.")
    print(links[2].single_activation())

    # Disable command
    print("\nDisabling functional commutator.")
    print(links[2].disable_commutator())

    # Enable command
    print("\nEnabling functional commutator.")
    print(links[2].enable_commutator())
    
    # Dump log entries command
    print("\nExpecting no log entries from commutator.")
    radio.log_code = []
    radio.log_age  = []
    radio.log_user = []
    print(links[2].dump_logging())
    
    # Fill commutator with dummy log entries
    radio.log_code = [0x30, 0x33, 0x30, 0x31, 0x33]    
    radio.log_age  = [300, 270, 180, 150, 60]    
    radio.log_user = [[0x70, 0x40, 0x84, 0x0B], # User1 attempted 5 min ago
                      [0x70, 0x40, 0x84, 0x0B], # User1 tried to activate
                                                #(for example in double
                                                # activation mode) 30 s later
                      [0x70, 0x40, 0x84, 0x0B], # User1 attempted 3 min ago 
                      [0x45, 0x55, 0x55, 0x55], # User2 confirms 30 s later
                      [0x70, 0x40, 0x84, 0x0B]] # User1 logs out 1 min ago 

    print("\nExpecting 5 log entries from commutator.")
    print(links[2].dump_logging())

    # Check empty memory
    print("\nExpecting empty memory.")
    print(links[2].check_memory())    

    # Fill commutator access table prior to update
    radio.access_table = [[['7040840B'],
                           ['45555555'],
                           ['67892311'],
                           ['A55F78BC']],
                          [True, False, True, False]]
    # Check memory
    print("\nExpecting 4 used, 6 total entries in memory.")
    radio.mem_size = 6
    print(links[2].check_memory())    

    # Create updated table
    new_table =          [['7040840B',
                           '45555555',
                           '67892311',
                           'A55F78BC',
                           '5555840B',
                           '892311DE'],
                          [False, True, True, False, False, True]]

    # Send updated table
    print("\nUpdating access table.")
    print(links[2].update_table(new_table))
    
    # Check memory after update
    print("\nExpecting full memory.")
    print(links[2].check_memory())    

    # Add another user (exceeding memory)
    new_table =          [['7040840B',
                           '45555555',
                           '67892311',
                           'A55F78BC',
                           '5555840B',
                           '599589FB',
                           '892311DE'],
                          [False, True, True, True, False, False, True]]

    # Send updated table
    print("\nUpdating access table with too many users.")
    print(links[2].update_table(new_table))
    
    # Check memory after update
    print("\nExpecting full memory.")
    print(links[2].check_memory())    

    # Clear memory 
    print("\nClear memory command.")
    print(links[2].clear_memory())    

    # Check memory after clearing
    print("\nExpecting empty memory.")
    print(links[2].check_memory())    


