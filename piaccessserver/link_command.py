import time

class LinkCommand():
    def __init__(self, radio, channel, machine_id):
        ''' This radio is shared between several LinkCommand instances,
        each with its own RF channel (TBD if a different pipe address
        is required)
        '''
        self.radio      = radio
        self.channel    = channel
        self.machine_id = machine_id
        
    def send_command(self, command):
        ''' Used to send any command and check for ACK '''
        
        # Configure the radio on the right RF channel for the machine
        self.radio.setChannel(self.channel)
        
        link_ok    = False
        ack_ok     = False
        machine_ok = False
        
        if self.radio.write(command):
            # Write successful
            link_ok  = True
            read_buf = []
            if self.radio.read(read_buf, 1) == 1:
                ack_ok = True
                if read_buf[0] == 0xA0:
                    machine_ok = True

        return {"link_ok": link_ok,
                "machine_ok": machine_ok,
                "ack_ok": ack_ok}    
    
    def register(self):
        return self.send_command([0xA0])
    
    def enable_machine(self):
        return self.send_command([0xA1])

    def disable_machine(self):
        return self.send_command([0xA2])

    def dump_logging(self):
        outarg = self.send_command([0xA3])
        outarg["read_ok"] = False
        read_buf = []
        if self.radio.read(read_buf, 8) == 8:
            # Make sure first element is the command
            if not read_buf[0] == 0xA3:
                return outarg
            
            # Retrieve first elements to initialise output
            outarg["log_count"] = read_buf[1]
            outarg["log_codes"] = [read_buf[2]]
            outarg["log_users"] = [read_buf[3:7]]
            outarg["log_times"] = [read_buf[7]]
            
            # Iterate through expected number of log entries
            for i in range(read_buf[1]-1):
                read_buf = []
                if self.radio.read(read_buf, 8) == 8:
                    # Make sure first element is the command
                    if not read_buf[0] == 0xA3:
                        outarg["read_ok"] = False
                        return outarg
                    # TODO: check decreasing number of entries in read_buf[1]
                    
                    # Append log entry
                    outarg["log_codes"].append(read_buf[2])
                    outarg["log_users"].append(read_buf[3:7])
                    outarg["log_times"].append(read_buf[7])
        else:
            # Not enough data bytes were received
            print("Log entry packet incomplete (only %d bytes)." % len(read_buf))
            return outarg
        
        # Everything went fine
        outarg["read_ok"] = True
        return outarg                
                    
    def update_table(self):
        # TODO: implement sending data table
        pass


class DummyRadio():
    def __init__(self):
        # Error emulation
        self.b_link_err    = False
        self.b_machine_err = False
        self.b_autoack_err = False
        
        self.link_errors    = {}
        self.machine_errors = {}
        self.autoack_errors = {}
        
        # Communication buffers
        self.rx_buf = []
        self.tx_buf = []
        
        # Transceiver mode (transmit or receive)
        self.rx_mode = False
        self.channel = -1

    def link_err(self, channel):    self.link_errors[hex(channel)] = True       
    def link_ok(self, channel):     self.link_errors[hex(channel)] = False       
    def machine_err(self, channel): self.machine_errors[hex(channel)] = True       
    def machine_ok(self, channel):  self.machine_errors[hex(channel)] = False       
    def autoack_err(self, channel): self.autoack_errors[hex(channel)] = True       
    def autoack_ok(self, channel):  self.autoack_errors[hex(channel)] = False       

    def setChannel(self, channel):
        self.channel = channel
        # Set link error if specified for this channel
        if self.link_errors.has_key(hex(channel)):
            self.b_link_err = self.link_errors[hex(channel)]
        else:
            self.b_link_err = False
        # Set machine error if specified for this channel
        if self.machine_errors.has_key(hex(channel)):
            self.b_machine_err = self.machine_errors[hex(channel)]
        else:
            self.b_machine_err = False
        # Set auto acknowledgment error if specified for this channel
        if self.autoack_errors.has_key(hex(channel)):
            self.b_autoack_err = self.autoack_errors[hex(channel)]
        else:
            self.b_autoack_err = False
        
    def write(self, buf):
        # Necessarily in TX mode
        self.rx_mode = False
        # Wait 10 ms
        time.sleep(0.010)
        if self.b_link_err:
            del self.rx_buf[:]
            return False
        
        # Return the expected reply from Arduino
        if (buf[0] == 0xA0 or
            buf[0] == 0xA1 or
            buf[0] == 0xA2 or
            buf[0] == 0xA4):
            # Register, enable, disable or update table command, answer state
            if not self.b_autoack_err:
                self.rx_buf = [0xA0 + 0x0F * (self.b_machine_err)]
                print("Machine will receive %s command." % hex(buf[0]))

        elif buf[0] == 0xA3:
            # Dump logging command, answer state first
            if not self.b_autoack_err:
                self.rx_buf = [0xA0 + 0x0F * (self.b_machine_err)]
                if len(self.log_code) == 0:
                    # Send empty log buffer
                    self.rx_buf.append(0xA3) # command
                    self.rx_buf.append(0)
                    self.rx_buf.append(0)
                    for code_byte in [0,0,0,0]:
                        self.rx_buf.append(code_byte)
                    self.rx_buf.append(0)
                else:
                    # Dump log entries
                    for i in range(len(self.log_code)):
                        # Repeat the command itself
                        self.rx_buf.append(0xA3) 
                        # Number of remaining entries, including this one
                        self.rx_buf.append(len(self.log_code)) 
                        # Current entry code (1 byte) and user (4 bytes)
                        self.rx_buf.append(self.log_code[i])
                        for code_byte in self.log_user[i]:
                            self.rx_buf.append(code_byte)
                        self.rx_buf.append(self.log_age[i])
                    # Clear log entries from Arduino
                    self.log_len = 0
                    del self.log_code[:]
                    del self.log_user[:]
                    del self.log_age[:]
        return True
    
    def read(self, buf, buf_len=-1):
        del buf[:]
        # Read and empty RX buffer
        buf.extend(self.rx_buf[0:buf_len])
        del self.rx_buf[0:buf_len]
        return len(buf)
    
    def isAckPayloadAvailable(self):
        return (len(self.rx_buf) > 0)
    
    def getDynamicPayloadSize(self):
        return len(self.rx_buf)

    def available(self):
        return True

    def writeAckPayload(self, buf):
        # Usually set in RX mode
        self.rx_mode = True
        self.tx_buf.extend(buf)
        return True



# UNIT TEST (if script is executed directly)
if __name__ == '__main__':
    # Init shared radio
    radio = DummyRadio()

    # Define machines
    num_machines = 3
    channels = [32, 33, 34]
    machine_ids = [0xA, 0xB, 0xC]

    # Create a link for each machine
    links = []
    for n in range(num_machines):
        links.append(LinkCommand(radio, channels[n], machine_ids[n]))

    # 1st machine (non-powered)
    radio.link_err(channels[0])
    print("This machine is non-powered.")
    print(links[0].register())
    
    # 2nd machine (failed its self-test)
    radio.machine_err(channels[1])
    print("This machine failed its self-test.")
    print(links[1].register())

    # 3rd machine (going fine)
    radio.autoack_err(channels[2])
    print("This machine is not ready to acknowledge.")
    print(links[2].register())

    radio.autoack_ok(channels[2])
    print("This machine is now ready.")
    print(links[2].register())

    # Disable command
    print("Disabling functional machine.")
    print(links[2].disable_machine())

    # Enable command
    print("Enabling functional machine.")
    print(links[2].enable_machine())
    
    # Dump log entries command
    print("Expecting no log entries from machine.")
    radio.log_code = []
    radio.log_age  = []
    radio.log_user = []
    print(links[2].dump_logging())
    
    # Fill machine with dummy log entries
    radio.log_code = [0x30, 0x33, 0x30, 0x31, 0x33]    
    radio.log_age  = [300, 270, 180, 150, 60]    
    radio.log_user = [[0x70, 0x40, 0x84, 0x0B], # User1 attempted 5 min ago
                      [0x70, 0x40, 0x84, 0x0B], # User1 tried to activate
                                                #(for example in double
                                                # activation mode) 30 s later
                      [0x70, 0x40, 0x84, 0x0B], # User1 attempted 3 min ago 
                      [0x45, 0x55, 0x55, 0x55], # User2 confirms 30 s later
                      [0x70, 0x40, 0x84, 0x0B]] # User1 logs out 1 min ago 

    print("Expecting 5 log entries from machine.")
    print(links[2].dump_logging())
