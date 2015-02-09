import time
from datetime import timedelta, datetime

class LinkCommand():
    def __init__(self, radio, channel, machine_id):
        ''' A single radio is shared between several LinkCommand instances,
        each with its own RF channel (TBD if a different pipe address
        is required)
        '''
        self.radio      = radio
        self.channel    = channel
        self.machine_id = machine_id
        self.wait_rx_sleep = 0.01
        self.wait_rx_retry = 100
        
    def send_command(self, command):
        ''' Used to send any command and check for ACK '''
        
        # Configure the radio on the right RF channel for the machine
        self.radio.setChannel(self.channel)
        
        link_ok    = False
        reply_ok   = False
        machine_ok = False
        
        if self.radio.write(command):
            # Write successful
            link_ok  = True
            read_buf = []

            if (self.wait_rx() and
                self.radio.read(read_buf, 1) == 1):
                # Check received state
                if   read_buf[0] == 0xAF:
                    reply_ok   = True
                elif read_buf[0] == 0xA0:
                    machine_ok = True
                    reply_ok   = True
                    
        return {"link_ok": link_ok,
                "machine_ok": machine_ok,
                "reply_ok": reply_ok}    
    
    def register(self):
        return self.send_command([0xA0])
    
    def enable_machine(self):
        return self.send_command([0xA1])

    def disable_machine(self):
        return self.send_command([0xA2])

    def dump_logging(self):
        # Initialise outputs
        outarg              = {"read_ok": False}
        outarg["log_count"] = 0
        outarg["log_codes"] = []
        outarg["log_users"] = []
        outarg["log_times"] = []
        num_entries = 1
        while num_entries > 0:
            # Send command and validate machine state
            cmd_state = self.send_command([0xA3])
            print(cmd_state)
            outarg.update(cmd_state)

            if not self.wait_rx():
                # No message received
                return outarg

            # Read the remainder of the packet
            read_buf = []                
            if self.radio.read(read_buf, 8) == 8:
                # Make sure first element is the command
                if (read_buf[0] != 0xA3):
                    return outarg
                
                # Retrieve first elements to initialise output
                num_entries = read_buf[1]
                if num_entries == 0:
                    # No log entries to add
                    outarg["read_ok"] = True
                    return outarg
                
                # Only update log count if higher
                outarg["log_count"] = max(num_entries, outarg["log_count"])
                outarg["log_codes"].append(read_buf[2])
                outarg["log_users"].append(read_buf[3:7])
                
                # Immediately convert elapsed time in seconds
                # to UTC date and time for logging
                outarg["log_times"].append([datetime.utcnow() - \
                                       timedelta(seconds=read_buf[7])])

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

    def wait_rx(self):
        num_retry = 0
        while not self.radio.available([0]):
            time.sleep(self.wait_rx_sleep)
            num_retry += 1
            if num_retry == self.wait_rx_retry:
                return False
        return True            

class DummyRadio():
    def __init__(self):
        # Error emulation
        self.b_link_err    = False
        self.b_machine_err = False
        self.b_reply_err = False
        
        self.link_errors    = {}
        self.machine_errors = {}
        self.reply_errors = {}
        
        # Communication buffer
        self.rx_buf = []

        # Current channel
        self.channel = -1

    def link_err(self, channel):    self.link_errors[hex(channel)] = True       
    def link_ok(self, channel):     self.link_errors[hex(channel)] = False       
    def machine_err(self, channel): self.machine_errors[hex(channel)] = True       
    def machine_ok(self, channel):  self.machine_errors[hex(channel)] = False       
    def reply_err(self, channel):   self.reply_errors[hex(channel)] = True       
    def reply_ok(self, channel):    self.reply_errors[hex(channel)] = False       

    def setChannel(self, channel):
        self.channel = channel
        # Set link error if specified for this channel
        if hex(channel) in self.link_errors:
            self.b_link_err = self.link_errors[hex(channel)]
        else:
            self.b_link_err = False
        # Set machine error if specified for this channel
        if hex(channel) in self.machine_errors:
            self.b_machine_err = self.machine_errors[hex(channel)]
        else:
            self.b_machine_err = False
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
            buf[0] == 0xA4):
            # Register, enable, disable or update table command, answer state
            self.rx_buf = [0xA0 + 0x0F * (self.b_machine_err)]
            print("Machine will receive %s command." % hex(buf[0]))

        elif buf[0] == 0xA3:
            # Dump logging command, answer state first
            self.rx_buf = []
            num_entries = len(self.log_code)
            if num_entries == 0:
                # Send empty log buffer
                self.rx_buf.append(0xA0 + 0x0F * (self.b_machine_err)) 
                # Repeat the command itself
                self.rx_buf.append(0xA3)
                # The rest is empty
                self.rx_buf.append(0)
                self.rx_buf.append(0)
                for code_byte in [0,0,0,0]:
                    self.rx_buf.append(code_byte)
                self.rx_buf.append(0)
            else:
                # Dump 1 log entry
                self.rx_buf.append(0xA0 + 0x0F * (self.b_machine_err)) 
                # Repeat the command itself
                self.rx_buf.append(0xA3) 
                # Number of remaining entries, including this one
                self.rx_buf.append(num_entries) 
                # Current entry code (1 byte) and user (4 bytes)
                self.rx_buf.append(self.log_code[0])
                for user_byte in self.log_user[0]:
                    self.rx_buf.append(user_byte)
                self.rx_buf.append(self.log_age[0])
                
                # Remove entry from log
                del self.log_code[0]
                del self.log_user[0]
                del self.log_age[0]
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
        return pipe_num == [0]
    
    def flush_rx(self):
        del self.rx_buf[:]
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
    print("\nThis machine is non-powered.")
    print(links[0].register())
    
    # 2nd machine (failed its self-test)
    radio.machine_err(channels[1])
    print("\nThis machine should report trouble.")
    print(links[1].register())

    # 3rd machine (going fine)
    radio.reply_err(channels[2])
    print("\nThis machine is not ready to acknowledge.")
    print(links[2].register())

    radio.reply_ok(channels[2])
    print("\nThis machine is now ready.")
    print(links[2].register())

    # Disable command
    print("\nDisabling functional machine.")
    print(links[2].disable_machine())

    # Enable command
    print("\nEnabling functional machine.")
    print(links[2].enable_machine())
    
    # Dump log entries command
    print("\nExpecting no log entries from machine.")
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

    print("\nExpecting 5 log entries from machine.")
    print(links[2].dump_logging())
