# Provisional gimmick for FCMkIII + OptiTrack

import tkinter as Tk

import FCWidget as wg
import auxiliary.errorPopup as ep

import FCMainWindow as mw
import FCCommunicator as cm

import PythonClient.NatNetClient as nc
import time


def process(
	commandQueue,
	mosiMatrixQueue,
	printQueue,
	profile,
	updatePipeOut,
	misoMatrixPipeOut,
):

	try:
		print("Provisional OptiTrack interface started")
		
		tm = [time.time()]
		prev = [0]

		commandQueue.put_nowait((mw.COMMUNICATOR, cm.SET_DC, 5, (1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1), cm.ALL)
		)
		
		# Build widget --------------------

		tl = Tk.Frame(master = None)
		tl.pack()

		beaconFrame = Tk.Frame(tl)
		beaconFrame.pack(fill = Tk.X, expand = True)

		beaconLabel = Tk.Label(beaconFrame, text = "BEACON ")
		beaconLabel.pack(side = Tk.LEFT)

		beaconXVar = Tk.StringVar()
		beaconXLabel = Tk.Label(beaconFrame, text = "   X: ")
		beaconXDisplay = Tk.Label(beaconFrame, text = "None", textvariable = beaconXVar)
		beaconXLabel.pack(side = Tk.LEFT)
		beaconXDisplay.pack(side = Tk.LEFT)
		
		beaconYVar = Tk.StringVar()
		beaconYLabel = Tk.Label(beaconFrame, text = "   Y: ")
		beaconYDisplay = Tk.Label(beaconFrame, text = "None", textvariable = beaconYVar)
		beaconYLabel.pack(side = Tk.LEFT)
		beaconYDisplay.pack(side = Tk.LEFT)
		
		beaconZVar = Tk.StringVar()
		beaconZLabel = Tk.Label(beaconFrame, text = "   Z: ")
		beaconZDisplay = Tk.Label(beaconFrame, text = "None", textvariable = beaconZVar)
		beaconZLabel.pack(side = Tk.LEFT)
		beaconZDisplay.pack(side = Tk.LEFT)


		# ---------------------------------

		# BOT LEFT:
		# X: 1.52m Y: 0.86m Z: 2.27m

		x_0 = 1.52
		y_0 = 0.86
		z_0 = 2.27

		maxDC = 25

		# This is a callback function that gets connected to the NatNet client and called once per mocap frame.
		def receiveNewFrame( frameNumber, markerSetCount, unlabeledMarkersCount, rigidBodyCount, skeletonCount,
							labeledMarkerCount, timecode, timecodeSub, timestamp, isRecording, trackedModelsChanged ):
			pass
		
		# This is a callback function that gets connected to the NatNet client. 
		# It is called once per rigid body per frame
		def receiveRigidBodyFrame( id, position, rotation, tm, prev):
			
			
			#fposition = tuple(map(float, position))
			x = float(position[0]) - x_0
			y = float(position[1]) - y_0
			z = max(z_0 - float(position[2]), 0)
			
			beaconXVar.set("{:.2f} m".format(x))
			beaconYVar.set("{:.2f} m".format(y))
			beaconZVar.set("{:.2f} m".format(z))
			
			if time.time() - tm[0] > 0.20 and abs(z - prev[0]) > abs(0.07*z):
				
				prev[0] = z
				tm = time.time()
				commandQueue.put_nowait(
					(mw.COMMUNICATOR, cm.SET_DC, max(maxDC/(1+z**2),5), (1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1), cm.ALL)
				)
			else:
				return

		# This will create a new NatNet client
		streamingClient = nc.NatNetClient(serverIP = "192.168.88.11", multicastIP = "239.255.42.99")

		# Configure the streaming client to call our rigid body handler on the emulator to send data out.
		streamingClient.newFrameListener = receiveNewFrame
		streamingClient.rigidBodyListener = lambda i,p,r: receiveRigidBodyFrame(i,p,r,tm, prev)

		# Start up the streaming client now that the callbacks are set up.
		# This will run perpetually, and operate on a separate thread.
		streamingClient.run()
		tl.mainloop()
		
		while(True):
			
			if updatePipeOut.poll():
				m = updatePipeOut.recv()
				
				if m[wg.COMMAND] == wg.STOP:
					print("Stop flag received")
					commandQueue.put_nowait(
						(mw.COMMUNICATOR, cm.SET_DC, 0.0, (1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1), cm.ALL)
					)
					break

		

	except:
		ep.errorPopup("Error in PG: ")


	# End process ==============================================================

class PG(wg.FCWidget):

	def __init__(self, master, profile, spawnQueue, printQueue):
				

		self.printQueue = printQueue
		super(PG, self).__init__(
			master = master,
			process = process,
			profile = profile,
			spawnQueue = spawnQueue,
			printQueue = printQueue,
			symbol = "PG"
		)

	

