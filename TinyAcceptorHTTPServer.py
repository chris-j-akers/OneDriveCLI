from urllib.parse import parse_qs
from http.server import SimpleHTTPRequestHandler, HTTPServer
from time import sleep
from functools import partial
        
class TinyAcceptorHTTPServer(HTTPServer):
    """
    When we request an authorisation token from MSFT for our client app we
    provide it with a redirect URI of http://localhost. This is the address the
    browser is redirected to once login/acceptance flow is completed. The actual
    authorisation token is included in the parameters of the URL.

    This small server listens for the above response so it can extract the token
    from the parameter. Either an error is reported (because MSFT sent one back)
    or the auth_code property is set.

    NOTE: This is a very basic, simple HTTP server and, though, it doesn't serve
    any files or local directories it's still an attack surface that could be 
    open for as long as the timeout. 
    
    To mitigate this:

        * The port is random (chosen by the OS)
        * We wait for one request and one request only, then close the server
        * We check state value received in the result matches the one we sent
          with the original authorisation request (see MSFT docs)
        * After a timeout (default 20 seconds) we close the server with an error

    The request comes locally from the browser, not from public internet, so
    ensure firewalls/windows defender etc are configured appropriately.
    
    Ultimately, up to you whether to use it or not.
    """
    class Handler(SimpleHTTPRequestHandler):
        """
        Handle the GET request from MSFT which will contain our authorisation 
        token in the URL as one of the parameters (or an error!).

        https://learn.microsoft.com/en-us/onedrive/developer/rest-api/getting-started/msa-oauth?view=odsp-graph-online

        Also checks the state code returned matches the one we sent with the 
        original authorisation request.
        
        Sets the authorisation code in the server so it can be retrieved later.
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
            if self.server.get_expected_state() != state[0]:
                print(f'error: state returned from MSFT does not match state sent in authorisation request (sent: {state[0]}, recvd: {self.server.get_state()}).')
                return ''
            if code == '':
                self.wfile.write(bytes('error: didn\'t seem to get authorisation code from MSFT, and no error.', 'utf8'))
                return ''
            else:
                self.server.set_auth_code(code[0])
                self.wfile.write(bytes('Authorised. You can close this browser window, now.', 'utf8'))

    def __init__(self):
        super().__init__(server_address=('127.0.0.1',0), RequestHandlerClass=self.Handler)
        self._auth_code = ''
        self._state = ''

    def get_port(self):
        return self.server_port

    def get_auth_code(self):
        return self._auth_code
    
    def set_auth_code(self, code):
        self._auth_code = code

    def get_expected_state(self):
        return self._state

    def set_expected_state(self, state):
        self._state = state

    def wait_for_authorisation_code(self, timeout=300):
        self.timeout = timeout
        with self:
            # We're only expecting one request
            self.handle_request()

    def handle_timeout(self):
        print("error: timeout while waiting for microsoft authorisation code.")
        self._error = f'timeout after {self.timeout} seconds.'
        return ''


