'''
Primitive terminal device
'''

from devices import device


DEVICE_TYPE = 0x01
DEVICE_ID = 0xABCDEF
DEVICE_CLASS = 'Terminal'


class Terminal(device.Device):
    '''
    Terminal
    '''

    def run(self, args):
        while True:
            try:
                text = input('Type some text: ')
            except (KeyboardInterrupt, SystemExit, EOFError):
                print()
                break
            self.send_text(text)

    def handle_data(self, data):
        print('\033[0;36m%s\033[0m' % data.decode('utf-8'))
        return 200, 'Ok\n'
