import socket as s
import http.server
import socketserver
import threading

import time

FILENAME = "ws.bin"
FILESIZE = 161100  # bytes 
VERSION = "SV1"

SPAM_PERIOD = 1 # seconds

print("FCMkII Provisional HTTP update script")

sk = s.socket(s.AF_INET, s.SOCK_DGRAM)
sk.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
sk.setsockopt(s.SOL_SOCKET, s.SO_BROADCAST, 1)
sk.settimeout(1)
"""
ls = s.socket(s.AF_INET, s.SOCK_DGRAM)
ls.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
"""
def _serverTimeout():
	print("SERVER TIMED OUT")

message = "U|CT|12345|{}|{}".format(FILENAME, FILESIZE)

"""
def _listenerRoutine():
	print "Listener online"
	while True:
		messageReceived, senderAddress = ls.recvfrom(512)
		print "Received \"{}\" from {}".format(messageReceived, senderAddress)

listenerThread = threading.Thread(target = _listenerRoutine)
listenerThread.setDaemon(True)
listenerThread.start()
"""

PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler
httpd = socketserver.ForkingTCPServer(("", PORT), Handler)

httpd.socket.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
httpd.timeout = 5

serverThread = threading.Thread(target = httpd.serve_forever)
serverThread.setDaemon(True)
serverThread.start()

inp = ''
slaves = []
numSlaves = 0
try:
	while(inp != 'x'):
		print("\n\nCurrent list: \n")
		for slave in slaves:
			if slave[3] != VERSION:
				print(slave)

		inp = eval(input("[x: quit; s: spam broadcast; c: contact-selective; l: listen; f: find; t: target] >> "))

		if inp == 'b':
			sk.sendto(message, ("<broadcast>", 65000))	

		elif (inp in ('l', 'L')):
			try:
				messageReceived, senderAddress = sk.recvfrom(512)
				print(("Received \"{}\" from {}".\
					format(messageReceived, senderAddress)))

			except s.error:
				print("Nothing in socket")
		
		elif (inp in ('s', 'S')):
			sk.sendto("U|CT|{}|{}|{}".format(
				sk.getsockname()[1], FILENAME, FILESIZE),("<broadcast>", 65000))
			print("Update Broadcast sent")

		elif (inp in ('f', 'F')):
			
			try:
				sk.sendto("N|CT|{}".format(
					sk.getsockname()[1]),('<broadcast>', 65000))
				print("STD Broadcast sent")

				while(True):
					
					try:
						print("Listening... ")
						messageReceived, senderAddress = sk.recvfrom(512)
						print(("Received \"{}\" from {}".\
							format(messageReceived, senderAddress)))
					except s.error:
						print("No responses")
						break

					messageSplitted = messageReceived.split("|")
					found = False

					for slave in slaves:
						if slave[1] == messageSplitted[2]:
							version = "Unknown"
							if len(messageSplitted) == 7:
								version = messageSplitted[6]
							elif messageSplitted[0] == 'B':
								version = "Bootloader"

							slave[1] = messageSplitted[2]
							slave[2] = senderAddress
							slave[3] = version

							print(("Updated Slave {}".format(slave)))
							found = True
							break

					if not found:
						version = "Unknown"
						if len(messageSplitted) == 7:
							version = messageSplitted[6]
						elif messageSplitted[0] == 'B':
							version = "Bootloader"

						new = [numSlaves, messageSplitted[2],senderAddress,version]
						slaves.append(new)
						numSlaves += 1
						print(("Added Slave {}".format(new)))

			except (s.error, IndexError, ValueError) as e:
				print(("[ERROR: {}]".format(e)))
		
		elif (inp in ('c', 'C')):
			
			for slave in slaves:
				if slave[3] != VERSION:
					print(("Sending update message to {}".format(slave)))
					sk.sendto("U|CT|{}|{}|{}".format(
						sk.getsockname()[1], FILENAME, FILESIZE),(slave[2][0], 65000))
					


		elif inp in ('t', 'T'):
			try:
				while True:
					target = None
					try:
						ind = int(eval(input("Slave number (-1 to end): ")))
						if ind == -1:
							break
						else:
							for slave in slaves:
								if slave[0] == ind:
									target = slave
									break
							

					except IndexError:
						print("Index error... Try again")
						continue
					except ValueError:
						print("Value error... Try again")
						continue

					tp = eval(input("Broadcast for {} @{} (N, U, R, L) (x to exit): ".\
						format(target[1], target[3])))

					if tp == 'N' or tp == 'n':
						sk.sendto("N|CT|{}|{}".format(
							sk.getsockname()[1], ),(target[2][0], 65000))
						print(("STD Broadcast sent to {}".format(target[1])))

					elif tp == 'U' or tp == 'u':
						sk.sendto("U|CT|{}|{}|{}".format(
							sk.getsockname()[1], FILENAME, FILESIZE),(target[2][0], 65000))
						print(("Update Broadcast sent to {}".format(target[1])))

					elif tp == 'R' or tp == 'r':
						sk.sendto("R|CT".format(
							sk.getsockname()[1], ),(target[2][0], 65000))
						print(("Shutdown Broadcast sent to {}".format(target[1])))

					elif tp == 'L' or tp == 'l':
						sk.sendto("L|CT".format(
							sk.getsockname()[1], ),(target[2][0], 65000))
						print(("Launch Broadcast sent to {}".format(target[1])))


			except s.error as e:
				print(("[SOCKET ERROR \"{}\"]".format(e)))
except Exception as e:
	print(("[EXCEPTION] \"{}\"".format(e)))

httpd.shutdown()
httpd.server_close()
eval(input("Shut down"))
