import serial

class Controller:
    '''
    Basic device adaptor for Thorlabs LK220 Thermoelectric Liquid Chiller.
    - More commands are available and have not been implemented.
    Test code runs and seems robust.
    '''
    def __init__(self,
                 which_port,
                 name='LK220',
                 control_mode='Local',
                 control_sensor='External',
                 temp_window=0.1,
                 verbose=True,
                 very_verbose=False):
        self.name = name
        self.verbose = verbose
        self.very_verbose = very_verbose
        if self.verbose: print("%s: opening..."%self.name, end='')
        try:
            self.port = serial.Serial(
                port=which_port, baudrate=115200, timeout=2)
        except serial.serialutil.SerialException:
            raise IOError(
                '%s: no connection on port %s'%(self.name, which_port))
        if self.verbose: print(" done.")
        assert self._get_identity() == 'THORLABS LK220 HV 1.20 FV 1.36'
        self._set_control_mode(control_mode)
        self._set_control_sensor(control_sensor)
        self.set_temp_window(temp_window)
        self.get_target_temp()

    def _send(self, cmd, response_lines=None):
        cmd = cmd + b'\r'
        if self.very_verbose: print('%s: sending cmd ='%self.name, cmd)
        self.port.write(cmd)
        if response_lines is None:
            response = None
            if self.very_verbose:
                print('%s: -> response = '%self.name, response)
        else:
            assert isinstance(response_lines, int) and response_lines > 0
            response = []
            for line in range(response_lines):
                r = self.port.readline()
                if self.very_verbose:
                    print('%s: -> response = '%self.name, r)
                response.append(r.decode('ascii').split('\r')[0])
            if len(response) == 1: # ditch the list
                response = response[0]
        assert self.port.readline() == b'> \r\n', 'ERROR: unexpected response'
        assert self.port.inWaiting() == 0, 'ERROR: serial port not empty'
        return response

    def _get_identity(self):
        if self.verbose:
            print('%s: getting identity'%self.name)
        cmd = b'IDN?'
        self.identity = self._send(cmd, response_lines=1)
        if self.verbose:
            print('%s: -> identity = %s'%(self.name, self.identity))
        return self.identity

    def _get_commands(self):
        if self.verbose:
            print('%s: getting commands'%self.name)
        cmd = b'COMMAND?'
        self.commands = self._send(cmd, response_lines=36)
        if self.verbose:
            for command in self.commands:
                print('%s: -> command = %s'%(self.name, command))
        return self.commands

    def _get_control_mode(self):
        if self.verbose:
            print('%s: getting control mode'%self.name)
        number_to_mode = {
            "0":"Local", "1":"Local-Analog", "2":"Trig", "3":"Trig-Analog"}            
        cmd = b'MOD?'
        self.control_mode = number_to_mode[self._send(cmd, response_lines=1)]
        if self.verbose:
            print('%s: -> control mode = %s'%(self.name, self.control_mode))
        return self.control_mode

    def _set_control_mode(self, control_mode):
        """
        'Local': The device responds to knob and software GUI operation
        'Local-Analog': The target temperature is set by the Analog IN port,
        and the Run/Stop of the chiller is controlled by the knob and GUI.
        'Trig': The target temperature is set by the knob and GUI, and the
        Run/Stop of the chiller is controlled by the Trigger IN port.
        'Trig-Analog': The target temperature is set by the Analog IN port,
        and the Run/Stop of the chiller is controlled by the Trigger IN port.
        """
        if self.verbose:
            print('%s: setting control mode = %s'%(self.name, control_mode))
        mode_to_number = {
            "Local":"0", "Local-Analog":"1", "Trig":"2", "Trig-Analog":"3"}
        assert control_mode in mode_to_number.keys(), (
            'ERROR: "%s" control mode not available'%control_mode)
        cmd = b'MOD=' + bytes(mode_to_number[control_mode], 'ascii')
        self._send(cmd)
        assert self._get_control_mode() == control_mode
        if self.verbose:
            print('%s: done setting control mode'%self.name)
        return None

    def _get_control_sensor(self):
        if self.verbose:
            print('%s: getting control sensor'%self.name)
        number_to_mode = {"0":"Internal", "1":"External"}            
        cmd = b'SENS?'
        self.control_sensor = number_to_mode[self._send(cmd, response_lines=1)]
        if self.verbose:
            print('%s: -> control sensor = %s'%(self.name, self.control_sensor))
        return self.control_sensor

    def _set_control_sensor(self, control_sensor):
        """
        'Internal': The internal sensor measuring the output coolant
        temperature is selected to provide the actual temperature reading.
        'External': The external TSP-TH sensor connected on the front panel
        is selected to provide the actual temperature reading.
        """
        if self.verbose:
            print('%s: setting control sensor = %s'%(self.name, control_sensor))
        mode_to_number = {"Internal":"0", "External":"1"}
        assert control_sensor in mode_to_number.keys(), (
            'ERROR: "%s" control sensor not available'%control_sensor)
        cmd = b'SENS=' + bytes(mode_to_number[control_sensor], 'ascii')
        self._send(cmd)
        assert self._get_control_sensor() == control_sensor
        if self.verbose:
            print('%s: done setting control sensor'%self.name)
        return None

    def get_temp_window(self): # degC
        if self.verbose:
            print('%s: getting temp window'%self.name)            
        cmd = b'WINDOW?'
        self.temp_window = float(self._send(cmd, response_lines=1))
        if self.verbose:
            print('%s: -> temp window = %s'%(self.name, self.temp_window))
        return self.temp_window

    def set_temp_window(self, temp_window): # degC
        if self.verbose:
            print('%s: setting temp window = %s'%(self.name, temp_window))
        assert isinstance(temp_window, int) or isinstance(temp_window, float)
        assert 0.1 <= temp_window <= 5, (
            'temp_window (%0.2f) out of range'%temp_window)
        temp_window = round(temp_window, 1)
        cmd = b'WINDOW=' + bytes(str(int(10 * temp_window)), 'ascii')
        self._send(cmd)
        assert self.get_temp_window() == temp_window
        if self.verbose:
            print('%s: done setting temp window'%self.name)
        return None

    def get_target_temp(self): # degC
        if self.verbose:
            print('%s: getting target temp'%self.name)            
        cmd = b'TSET?'
        self.target_temp = float(self._send(cmd, response_lines=1))
        if self.verbose:
            print('%s: -> target temp = %s'%(self.name, self.target_temp))
        return self.target_temp

    def set_target_temp(self, target_temp): # degC
        if self.verbose:
            print('%s: setting target temp = %s'%(self.name, target_temp))
        assert isinstance(target_temp, int) or isinstance(target_temp, float)
        assert -5 <= target_temp <= 45, (
            'target_temp (%0.2f) out of range'%target_temp)
        target_temp = round(target_temp, 1)
        cmd = b'TSET=' + bytes(str(int(10 * target_temp)), 'ascii')
        self._send(cmd)
        assert self.get_target_temp() == target_temp
        if self.verbose:
            print('%s: done setting target temp'%self.name)
        return None

    def get_actual_temp(self): # degC, from internal or external sensor
        if self.verbose:
            print('%s: getting actual temp'%self.name)            
        cmd = b'TACT?'
        actual_temp = float(self._send(cmd, response_lines=1))
        if self.verbose:
            print('%s: -> actual temp = %s'%(self.name, actual_temp))
        return actual_temp

    def set_enable(self, enable):
        if self.verbose:
            print('%s: setting enable = %s'%(self.name, enable))
        assert isinstance(enable, bool)
        cmd = b'EN=' + bytes(str(int(enable)), 'ascii')
        self._send(cmd)
        if self.verbose:
            print('%s: done setting enable'%self.name)
        self.enable = enable
        return None

    def close(self):
        if self.verbose: print("%s: closing..."%self.name, end='')
        self.port.close()
        if self.verbose: print("done.")
        return None

if __name__ == '__main__':
    import time
    chiller = Controller(
        'COM12',
        control_mode='Local',
        control_sensor='External',
        temp_window=0.1,
        verbose=True,
        very_verbose=False)

##    chiller._get_commands()

    print('\n# Basic operation:')
    chiller.set_target_temp(22)
    chiller.get_actual_temp()
    chiller.set_enable(True)
    print('\n# Do some heating/cooling...\n')
    chiller.set_enable(False)

    chiller.close()
