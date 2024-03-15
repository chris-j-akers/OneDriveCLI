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
    be open for as long as the timeout you have selected.
    
    Firewalls etc. should mitigate and it lets your OS pick the port. We also 
    check the state value returned with the authorisation code is the one that 
    we sent. Ultimately, up to you whether to use it or not.
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
            state = data.get('state', '')
            error = data.get('error','')
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            if error != '':
                print(f'error: got error in MSFT response: {error}.')
                return ''                
            if self.server.get_state() != state[0]:
                print(f'error: state returned from MSFT does not match state sent in authorisation request (sent: {state[0]}, recvd: {self.server.get_state()}).')
                return ''
            if code == '':
                self.wfile.write(bytes('error: didn\'t seem to get authorisation code from MSFT, and no error.', 'utf8'))
                return ''
            else:
                self.server.set_state(state[0])
                self.server.set_code(code[0])
                self.wfile.write(bytes('Authorised. You can close this browser window, now.', 'utf8'))

    def __init__(self):
        super().__init__(server_address=('127.0.0.1',0), RequestHandlerClass=self.Handler)
        self._code = ''
        self._state = ''
        self._error = ''

    def get_port(self):
        return self.server_port

    def get_code(self):
        return self._code
    
    def set_code(self, code):
        self._code = code

    def get_state(self):
        return self._state

    def set_state(self, state):
        self._state = state

    def get_error(self):
        return self._error

    def wait_for_authorisation_code(self, timeout=20):
        self.timeout = timeout
        with self:
            self.handle_request()

    def handle_timeout(self):
        print("error: timeout while waiting for microsoft authorisation code.")
        self._error = f'timeout after {self.timeout} seconds.'
        return ''


