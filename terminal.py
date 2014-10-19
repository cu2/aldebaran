import device
import sys


class Terminal(device.OutputDevice):

    def handle_input(self, command, data):
        # if command == 'ack':
        #     print 'Acknowledged.'
        if command == 'data':
            print '\033[0;36m%s\033[0m' % data
        return 200, 'Ok\n'


def main(args):
    if len(args) < 2:
        print 'Usage: python terminal.py <ioport_number> <device_port>'
        return 1
    ioport_number = int(args[0])
    device_port = int(args[1])
    terminal = Terminal(
        aldebaran_address=('localhost', 35001),
        ioport_number=ioport_number,
        device_descriptor=(0x01, 0xABCDEF),
        device_address=('localhost', device_port),
    )
    retval = terminal.start()
    if retval != 0:
        return retval
    retval = terminal.register()
    if retval != 0:
        return retval
    try:
        while True:
            text = raw_input('Type some text: ')
            retval = terminal.send_data(text)
            if retval == 1:
                break
            if retval == 2:
                print 'Text could not be sent: %s' % text
    except:
        pass
    print ''
    retval = terminal.unregister()
    if retval != 0:
        return retval
    return 0


if __name__ == '__main__':
    main(sys.argv[1:])
