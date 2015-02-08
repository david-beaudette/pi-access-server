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
        # Used to send any command and check for ACK
        
        # Configure the radio on the right RF channel for the machine
        self.radio.setChannel(self.channel)
        
        link_ok    = False
        ack_ok     = False
        machine_ok = False
        
        if self.radio.write([0xA0]):
            # Write successful
            link_ok  = True
            read_buf = []
            if self.radio.read(read_buf) >= 1:
                ack_ok = True
                if read_buf[0] == 0xA0:
                    machine_ok = True

        return {'link_ok': link_ok,
                "machine_ok": machine_ok,
                "ack_ok": ack_ok}    
    
    def register(self):
        return self.send_command([0xA0])
    
    def enable_machine(self):
        return self.send_command([0xA1])

    def disable_machine(self):
        return self.send_command([0xA2])

    def dump_logging(self):
        return self.send_command([0xA3])

    def update_table(self):
        pass


class DummyRadio():
    def __init__(self):
        # Error emulation
        self.b_link_err    = False
        self.b_machine_err = False
        
        self.link_errors    = {}
        self.machine_errors = {}
        
        # Communication buffers
        self.rx_buf = []
        self.tx_buf = []
        
        # Transceiver mode (transmit or receive)
        self.rx_mode = False
        self.channel = -1

    def link_err(self, channel):
        self.link_errors[hex(channel)] = True       

    def link_ok(self, channel):
        self.link_errors[hex(channel)] = False       

    def machine_err(self, channel):
        self.machine_errors[hex(channel)] = True       

    def machine_ok(self, channel):
        self.machine_errors[hex(channel)] = False       

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
            self.rx_buf = [0xA0 + 0x0F * (self.b_machine_err)]

        elif buf[0] == 0xA3:
            # Dump logging command, answer state first
            self.rx_buf = [0xA0 + 0x0F * (self.b_machine_err)]
            if self.log_len == 0:
                # Send empty log buffer
                self.rx_buf.append(0xA3) # command
                self.rx_buf.append(0)
                self.rx_buf.append(0)
                self.rx_buf.append([0,0,0,0])
            else:
                # Dump log entries
                for i in range(self.log_len):
                    # Repeat the command itself
                    self.rx_buf.append(0xA3) 
                    # Number of remaining entries, including this one
                    self.rx_buf.append(self.log_len) 
                    # Current entry code (1 byte) and user (4 bytes)
                    self.rx_buf.append(self.log_code[i])
                    self.rx_buf.append(self.log_user[i])
                # Clear log entries from Arduino
                self.log_len = 0
                del self.log_code[:]
                del self.log_user[:]
        return True
    
    def read(self, buf, buf_len=-1):
        del buf[:]
        # Read and empty RX buffer
        buf.extend(self.rx_buf[:])
        del self.rx_buf[:]
        # Empty TX buffer since it will be sent with ACK
        del self.tx_buf[:]
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

    # Configure first machine (non-powered)
    radio.link_err(channels[0])

    # Configure second machine (failed its self-test)
    radio.machine_err(channels[1])

    # Configure third machine (going fine)
    radio.machine_ok(channels[2])

    # Register each machine
    for link in links:
        print link.register()
    



        
