import threading
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn

import aux


class InterruptHandler(aux.Hardware):

    class RequestHandler(BaseHTTPRequestHandler):

        def do_POST(self):
            interrupt_number = self.path.lstrip('/')
            self.server.log.log('interrupt_handler', 'Caught: %s' % interrupt_number)
            self.server.interrupt_queue.put(interrupt_number)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(interrupt_number)
            self.wfile.write('\n')

        def log_message(self, format, *args):
            return

    class Server(ThreadingMixIn, HTTPServer):

        def __init__(self, server_address, request_handler, interrupt_queue, log):
            HTTPServer.__init__(self, server_address, request_handler)
            self.interrupt_queue = interrupt_queue
            self.log = log
            self.daemon_threads = True

    def __init__(self, host, port, log=None):
        aux.Hardware.__init__(self, log)
        self.address = (host, port)
        self.interrupt_queue = None

    def register_architecture(self, interrupt_queue):
        self.interrupt_queue = interrupt_queue

    def start(self):
        if not self.interrupt_queue:
            self.log.log('interrupt_handler', 'ERROR: Cannot run without Interrupt Queue.')
            return 1
        self.log.log('interrupt_handler', 'Starting...')
        self.server = self.Server(self.address, self.RequestHandler, self.interrupt_queue, self.log)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.log.log('interrupt_handler', 'Started.')
        return 0

    def stop(self):
        self.log.log('interrupt_handler', 'Stopping...')
        self.server.shutdown()
        self.log.log('interrupt_handler', 'Stopped.')
