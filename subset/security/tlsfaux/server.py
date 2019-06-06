import socket, ssl, pprint, absolute_filepath, sys

arguments = sys.argv

directory_name = arguments[1]

filepath = "/".join(absolute_filepath.script_directory) + "/" + directory_name + "/"

hostname = '0.0.0.0'
port = 443

filename_cert = filepath + 'server.crt'
filename_key = filepath + 'server.key'

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile=filename_cert, keyfile=filename_key)

bind_socket = socket.socket()
bind_socket.bind((hostname,port))
bind_socket.listen(5)

def test_data(connstream,data):
	print("test_data:",data)
	return false

def read_client_data(connstream):
	data = connstream.read()
	while data:
		if not test_data(connstream,data):
			break
		data = connstream.read()

print("SSL Server started...")
while True:
	newsocket, fromaddr = bind_socket.accept()
	connstream = context.wrap_socket(newsocket, server_side=True)
	try:
		read_client_data(connstream)
	finally:
		connstream.shutdown(socket.SHUT_RDWR)
		connstream.close()
