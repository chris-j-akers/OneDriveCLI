from MSALATPersistence import MSALTokenHandler

ONEDRIVE_ENDPOINT = 'https://graph.microsoft.com/v1.0'
CLIENT_ID='9806a116-6f7d-4154-a06e-0c887dd51eed'
AUTHORITY='https://login.microsoftonline.com/consumers'
SCOPES=['Files.ReadWrite.All', 'Files.ReadWrite', 'offline_access']


th = MSALTokenHandler('my_test_app', CLIENT_ID, AUTHORITY, ' '.join(SCOPES), "./cja_settings.db")
th.get_token2()


# def _tiny_accept_server():
#     from http.server import BaseHTTPRequestHandler, HTTPServer
#     class Handler(BaseHTTPRequestHandler):
#         def do_GET(self):
#             print(self.path)
#     httpd = HTTPServer(('127.0.0.1', 0), Handler)
#     httpd.timeout = 0.5
#     with httpd:  # to make sure httpd.server_close is called
#         httpd.serve_forever()

# _tiny_accept_server()



