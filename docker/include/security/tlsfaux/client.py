from __future__ import absolute_import
import ssl
import sys
import time

arguments = sys.argv
HOST = ""
PORT = 443
VERSION = arguments[1]

try:
    HOST = arguments[2]
except Exception:
    pass

SSL_VERSION = None
if(VERSION == "1.2"):
    # Force TLS 1.2
    SSL_VERSION = ssl.PROTOCOL_TLSv1_2
elif(VERSION == "1.3"):
    # Pick highest version which should be 1.3
    SSL_VERSION = ssl.PROTOCOL_TLS


print("SSL Client Started...")
while len(HOST) > 0:
    try:
        print("Getting Server Certificate...")
        cert = ssl.get_server_certificate((HOST, PORT), ssl_version=SSL_VERSION)
        if(len(cert) > 0):
            print("Server Certificate Resolved")
        else:
            print("No Certificate Resolved")
    except Exception as e:
        print("Server Certificate Failure")
        print(e)
    finally:
        time.sleep(30)
print("SSL Client Stopped")
