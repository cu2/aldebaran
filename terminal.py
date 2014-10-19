import device


class Terminal(device.Device):
    pass


def main():
    terminal = Terminal(
        aldebaran_address=('localhost', 35001),
        ioport_number=0,
        device_descriptor=(0x01, 0xABCDEF),
        device_address=('localhost', 4567),
    )
    if not terminal.register():
        return 1
    try:
        while True:
            text = raw_input('Type some text: ')
            if not terminal.send_data(text):
                break
    except:
        pass
    print ''
    if not terminal.unregister():
        return 1
    return 0


if __name__ == '__main__':
    main()
