import requests


def send_request(url, command, data=None):
    command = '%04s' % command
    if data is None:
        data = ''
    return requests.post(
        url,
        data=command + data,
        headers={'content-type': 'application/octet-stream'},
    )


def main():
    aldebaran_host = 'localhost'
    aldebaran_device_handler_port = 35001
    ioport_number = 0
    device_type = 0x01
    device_id = 0xABCDEF
    device_host = 'localhost'
    device_port = 4567
    aldebaran_url = 'http://%s:%s/%s' % (aldebaran_host, aldebaran_device_handler_port, ioport_number)
    try:
        r = send_request(aldebaran_url, 'HELO', '%s,%s,%s,%s' % (device_type, device_id, device_host, device_port))
    except requests.exceptions.ConnectionError:
        print 'ERROR: Cannot connect to ALD.'
        return 1
    print '[ALD] %s' % r.text
    try:
        while True:
            text = raw_input('Type some text: ')
            r = send_request(aldebaran_url, 'DATA', text)
            print '[ALD] %s' % r.text
    except:
        pass
    print ''
    try:
        r = send_request(aldebaran_url, 'BYE!')
    except requests.exceptions.ConnectionError:
        print 'ERROR: Disconnected from ALD.'
        return 1
    print '[ALD] %s' % r.text
    return 0


if __name__ == '__main__':
    main()
