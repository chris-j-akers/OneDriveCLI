from urllib.parse import parse_qs
from http.server import SimpleHTTPRequestHandler, HTTPServer
from time import sleep
from functools import partial
        
class TinyAcceptorServer(HTTPServer):
    """
    When we request an authorisation token from MSFT for our client app, we
    provide it with a redirect URI of http://localhost. This is the address the
    browser is redirected to once login/acceptance flow is completed.

    This small server is started and listens for that response. It's shut-down
    immediately and either the 'code' or 'error' property is set, depending on
    what happened.

    The response could also contain an error, which is also set. The process 
    waiting on this server should check for the existence of error or code.

    NOTE: This is a very basic, simple HTTP server and, though, it doesn't serve
    any files or local directories it's still presents an attack surface that could
    be open for as long as the timeout you have selected. Firewalls etc. should
    mitigate, but it is up to you whether to use it or not.
    """
    class Handler(SimpleHTTPRequestHandler):
        """
        Handle the GET request from MSFT which will contain our authorisation 
        token in the URL as one of the parameters.

        https://learn.microsoft.com/en-us/onedrive/developer/rest-api/getting-started/msa-oauth?view=odsp-graph-online

        Either set the authorisation code (as taken from the URL parameters) or
        an error if one was sent back.
        """
        def do_GET(self):
            data = parse_qs(self.path[2:])
            code = data.get('code','')
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            if code == '':
                self.wfile.write(bytes('error: unable to get authorisation code from MSFT', 'utf8'))
                error = data.get('error', 'no error text found')
                self.server.set_error(error)
            else:
                self.wfile.write(bytes(str(data), 'utf8'))
                self.server.set_code(code[0])

    def __init__(self,):
        super().__init__(server_address=('127.0.0.1',0), RequestHandlerClass=self.Handler)
        self._code = ''
        self._error = ''
        self._shutdown = False

    def get_port(self):
        return self.server_port

    def get_code(self):
        return self._code

    def set_code(self, code):
        self._code = code

    def get_error(self):
        return self._error

    def set_error(self, error):
        self._error = error

    def start(self):
        with self:
            while self._shutdown == False:
                self.handle_request()
                sleep(1)

    def stop(self):
        self._shutdown = True


