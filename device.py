import requests
import struct

import aux
import device_handler


class Device(aux.Hardware):

    def __init__(self, aldebaran_address, ioport_number, device_descriptor, device_address):
        aux.Hardware.__init__(self, aux.Log())
        self.aldebaran_host, self.aldebaran_device_handler_port = aldebaran_address
        self.ioport_number = ioport_number
        self.device_type, self.device_id = device_descriptor
        self.device_host, self.device_port = device_address
        self.aldebaran_url = 'http://%s:%s/%s' % (self.aldebaran_host, self.aldebaran_device_handler_port, self.ioport_number)
        self.log.log('device', 'Initialized.')

    def _send_request(self, command, data=None):
        if data is None:
            data = ''
        r = requests.post(
            self.aldebaran_url,
            data=struct.pack('B', command) + data,
            headers={'content-type': 'application/octet-stream'},
        )
        self.log.log('device', 'Request sent.')
        return r

    def register(self):
        self.log.log('device', 'Registering...')
        try:
            r = self._send_request(device_handler.COMMAND_REGISTER, struct.pack(
                'BBBB255pH',
                self.device_type,
                self.device_id >> 16, (self.device_id >> 8) & 0xFF, self.device_id & 0xFF,
                self.device_host,
                self.device_port,
            ))
        except requests.exceptions.ConnectionError:
            self.log.log('device', 'ERROR: Cannot connect to ALD.')
            return False
        self.log.log('device', '[ALD] %s' % r.text)
        self.log.log('device', 'Registered.')
        return True

    def unregister(self):
        self.log.log('device', 'Unregistering...')
        try:
            r = self._send_request(device_handler.COMMAND_UNREGISTER)
        except requests.exceptions.ConnectionError:
            self.log.log('device', 'ERROR: Disconnected from ALD.')
            return False
        self.log.log('device', '[ALD] %s' % r.text)
        self.log.log('device', 'Unregistered.')
        return True

    def send_data(self, data):
        self.log.log('device', 'Sending data...')
        try:
            r = self._send_request(device_handler.COMMAND_DATA, data)
        except requests.exceptions.ConnectionError:
            self.log.log('device', 'ERROR: Disconnected from ALD.')
            return False
        self.log.log('device', '[ALD] %s' % r.text)
        self.log.log('device', 'Data sent.')
        return True
