import socket as s
import SimpleHTTPServer
import SocketServer
import threading

def _serverRoutine():
	PORT = 8000
	Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
	httpd = SocketServer.TCPServer(("", PORT), Handler)
	print "Server online. Serving at port", PORT
	httpd.serve_forever()

print "FCMkII Provisional HTTP update script"

sk = s.socket(s.AF_INET, s.SOCK_DGRAM)
sk.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
sk.setsockopt(s.SOL_SOCKET, s.SO_BROADCAST, 1)
sk.settimeout(1)

filename = raw_input("Filename: ")
filesize = int(raw_input("File size (bytes): "))

serverThread = threading.Thread(target = _serverRoutine)
serverThread.setDaemon(True)
serverThread.start()

inp = ""

while(inp not in ('X', 'x')):

	inp = raw_input("[x: quit; s: spam broadcast; l: listen] >> ")

	if(inp in ('s', 'S')):
		sk.sendto("U|CT|{}|{}|{}".format(
			sk.getsockname()[1], filename, filesize),('<broadcast>', 65000))
		print "Broadcast sent"
	
	elif (inp in ('l', 'L')):
		try:
			messageReceived, senderAddress = sk.recvfrom(512)
			print "Received \"{}\" from {}".\
				format(messageReceived, senderAddress)

		except socket.error:
			print "Nothing in socket"
