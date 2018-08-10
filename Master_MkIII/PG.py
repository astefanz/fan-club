# Provisional gimmick for FCMkIII + OptiTrack

import tkinter as Tk

import FCWidget as wg
import auxiliary.errorPopup as ep

import FCMainWindow as mw
import FCCommunicator as cm
import auxiliary.hardcoded as hc

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
		
		coordinateFrame = Tk.Frame(tl)
		coordinateFrame.pack(side = Tk.LEFT, fill = Tk.X, expand = True)
		
		# RAW BEACON COORDS ---------

		beaconRawFrame = Tk.Frame(coordinateFrame, bd = 1, relief = Tk.RIDGE)
		beaconRawFrame.pack(side = Tk.LEFT, fill = Tk.X, expand = True)

		beaconRawLabel = Tk.Label(beaconRawFrame, text = "RAW: ", font = ('TkDefaultFont','12','bold'))
		beaconRawLabel.pack(side = Tk.LEFT)

		beaconRawXVar = Tk.StringVar()
		beaconRawXLabel = Tk.Label(beaconRawFrame, text = "   X: ")
		beaconRawXDisplay = Tk.Label(beaconRawFrame, text = "None", textvariable = beaconRawXVar)
		beaconRawXLabel.pack(side = Tk.LEFT)
		beaconRawXDisplay.pack(side = Tk.LEFT)
		
		beaconRawYVar = Tk.StringVar()
		beaconRawYLabel = Tk.Label(beaconRawFrame, text = "   Y: ")
		beaconRawYDisplay = Tk.Label(beaconRawFrame, text = "None", textvariable = beaconRawYVar)
		beaconRawYLabel.pack(side = Tk.LEFT)
		beaconRawYDisplay.pack(side = Tk.LEFT)
		
		beaconRawZVar = Tk.StringVar()
		beaconRawZLabel = Tk.Label(beaconRawFrame, text = "   Z: ")
		beaconRawZDisplay = Tk.Label(beaconRawFrame, text = "None", textvariable = beaconRawZVar)
		beaconRawZLabel.pack(side = Tk.LEFT)
		beaconRawZDisplay.pack(side = Tk.LEFT)
		
		# ADJUSTED BEACON COORDS ---------

		beaconAdjustedFrame = Tk.Frame(coordinateFrame, bd = 1, relief = Tk.RIDGE)
		beaconAdjustedFrame.pack(side = Tk.LEFT, fill = Tk.X, expand = True)
	
		beaconAdjustedLabel = Tk.Label(beaconAdjustedFrame, text = "  ADJUSTED: ", font = ('TkDefaultFont','12','bold'))
		beaconAdjustedLabel.pack(side = Tk.LEFT)
		
		beaconAdjustedX = 0
		beaconAdjustedXVar = Tk.StringVar()
		beaconAdjustedXLabel = Tk.Label(beaconAdjustedFrame, text = "   X: ")
		beaconAdjustedXDisplay = Tk.Label(beaconAdjustedFrame, text = "None", textvariable = beaconAdjustedXVar)
		beaconAdjustedXLabel.pack(side = Tk.LEFT)
		beaconAdjustedXDisplay.pack(side = Tk.LEFT)
		
		beaconAdjustedY = 0
		beaconAdjustedYVar = Tk.StringVar()
		beaconAdjustedYLabel = Tk.Label(beaconAdjustedFrame, text = "   Y: ")
		beaconAdjustedYDisplay = Tk.Label(beaconAdjustedFrame, text = "None", textvariable = beaconAdjustedYVar)
		beaconAdjustedYLabel.pack(side = Tk.LEFT)
		beaconAdjustedYDisplay.pack(side = Tk.LEFT)
		
		beaconAdjustedZ = 0
		beaconAdjustedZVar = Tk.StringVar()
		beaconAdjustedZLabel = Tk.Label(beaconAdjustedFrame, text = "   Z: ")
		beaconAdjustedZDisplay = Tk.Label(beaconAdjustedFrame, text = "None", textvariable = beaconAdjustedZVar)
		beaconAdjustedZLabel.pack(side = Tk.LEFT)
		beaconAdjustedZDisplay.pack(side = Tk.LEFT)

		# ARRAY ORIGIN ---------------------

		arrayOriginFrame = Tk.Frame(coordinateFrame, bd = 1, relief = Tk.RIDGE)
		arrayOriginFrame.pack(side = Tk.LEFT, fill = Tk.X, expand = True)
	
		arrayOriginLabel = Tk.Label(arrayOriginFrame, text = "  ORIGIN: ", font = ('TkDefaultFont','12','bold'))
		arrayOriginLabel.pack(side = Tk.LEFT)
		
		arrayOriginX = 0
		arrayOriginXVar = Tk.StringVar()
		arrayOriginXLabel = Tk.Label(arrayOriginFrame, text = "   X: ")
		arrayOriginXDisplay = Tk.Label(arrayOriginFrame, text = "None", textvariable = arrayOriginXVar)
		arrayOriginXLabel.pack(side = Tk.LEFT)
		arrayOriginXDisplay.pack(side = Tk.LEFT)
		
		arrayOriginY = 0
		arrayOriginYVar = Tk.StringVar()
		arrayOriginYLabel = Tk.Label(arrayOriginFrame, text = "   Y: ")
		arrayOriginYDisplay = Tk.Label(arrayOriginFrame, text = "None", textvariable = arrayOriginYVar)
		arrayOriginYLabel.pack(side = Tk.LEFT)
		arrayOriginYDisplay.pack(side = Tk.LEFT)
		
		arrayOriginZ = 0
		arrayOriginZVar = Tk.StringVar()
		arrayOriginZLabel = Tk.Label(arrayOriginFrame, text = "   Z: ")
		arrayOriginZDisplay = Tk.Label(arrayOriginFrame, text = "None", textvariable = arrayOriginZVar)
		arrayOriginZLabel.pack(side = Tk.LEFT)
		arrayOriginZDisplay.pack(side = Tk.LEFT)

		arrayOriginXVar.set("{:.2f} m".format(arrayOriginX))
		arrayOriginYVar.set("{:.2f} m".format(arrayOriginY))
		arrayOriginZVar.set("{:.2f} m".format(arrayOriginZ))
		global arrayOriginSetFlag
		arrayOriginSetFlag = False
		def arrayOriginSetFlagCallback():
			arrayOriginSetFlag = True
		
		arrayOriginSetButton = Tk.Button(
			arrayOriginFrame,
			text = "Set",
			command = arrayOriginSetFlagCallback
		)
		arrayOriginSetButton.pack(side = Tk.LEFT)

		moduleSide = 0.24 # meters

		# AXIS CONFIGURATION ---------------------
		verticalAxis = beaconAdjustedY
		verticalSign = 1
	
		horizontalAxis = beaconAdjustedX
		horizontalSign = 1

		depthAxis = beaconAdjustedZ
		depthSign = 1

		# DUTY CYCLE LABEL:
		dcFrame = Tk.Frame(tl)
		dcFrame.pack(side = Tk.LEFT)

		dcLabel = Tk.Label(dcFrame, text = "  DC: ")
		dcLabel.pack(side = Tk.LEFT)
		dcVar = Tk.StringVar()
		dcDisplay = Tk.Label(dcFrame, textvariable = dcVar,width = 10, bd = 1, relief = Tk.SUNKEN)
		dcDisplay.pack(side = Tk.LEFT)

		# ACTION MENU:
		actionFrame = dcFrame
		actionLabel = Tk.Label(actionFrame)
		actionVar = Tk.StringVar()
		actionVar.set("HEIGHT")
		actionMenu = Tk.OptionMenu(
			actionFrame,
			actionVar,
			"HEIGHT",
			"PROXIMITY"
		)
		actionMenu.pack(side = Tk.LEFT)

		# ---------------------------------
		# Requirements:
		# - Bottom left coords
		# - Module size
		# - Array side
		# - vert axis and sign
		# - horiz axis and sign
		# - away axis and sign

		# BOT LEFT:
		# X: 1.52m Y: 0.86m Z: 2.27m

		x_0 = 1.52
		y_0 = 0.86
		z_0 = 2.27

		maxDC = 40

		tolerance = 0.07
		commandQueue.put_nowait(
			(mw.COMMUNICATOR, cm.SET_DC, 5, (1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1), cm.ALL)
		)
		dcVar.set("{:.2f} %".format(5))

		# This is a callback function that gets connected to the NatNet client and called once per mocap frame.
		def receiveNewFrame( frameNumber, markerSetCount, unlabeledMarkersCount, rigidBodyCount, skeletonCount,
							labeledMarkerCount, timecode, timecodeSub, timestamp, isRecording, trackedModelsChanged ):
			pass
		
		# This is a callback function that gets connected to the NatNet client. 
		# It is called once per rigid body per frame
		def receiveRigidBodyFrame( id, position, rotation, tm, prev):
			
			"""
			if arrayOriginSetFlag:
				arrayOriginX, arrayOriginY, arrayOriginZ = tuple(position)		
				arrayOriginXVar.set("{:.2f} m".format(position[0]))
				arrayOriginYVar.set("{:.2f} m".format(position[1]))
				arrayOriginZVar.set("{:.2f} m".format(position[2]))
				arrayOriginSetFlag = False
			"""

			#fposition = tuple(map(float, position))
			beaconAdjustedX = float(position[0]) - arrayOriginX
			beaconAdjustedY = float(position[1]) - arrayOriginY
			beaconAdjustedZ = float(position[2]) - arrayOriginZ
			
			beaconRawXVar.set("{:.2f} m".format(position[0]))
			beaconRawYVar.set("{:.2f} m".format(position[1]))
			beaconRawZVar.set("{:.2f} m".format(position[2]))
			
			beaconAdjustedXVar.set("{:.2f} m".format(beaconAdjustedX))
			beaconAdjustedYVar.set("{:.2f} m".format(beaconAdjustedY))
			beaconAdjustedZVar.set("{:.2f} m".format(beaconAdjustedZ))

			

			if time.time() - tm[0] > 0.2:

				tm[0] = time.time()

				if actionVar.get() == "HEIGHT" and abs(beaconAdjustedY - prev[0]) > abs(prev[0]*tolerance):
					dc = max((beaconAdjustedY/4)*100,5)
					prev[0] = beaconAdjustedY
					commandQueue.put_nowait(
						(mw.COMMUNICATOR, cm.SET_DC, dc, (1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1), cm.ALL)
					)
					dcVar.set("{:.2f} %".format(dc))

				elif actionVar.get() == "PROXIMITY" and abs(beaconAdjustedX - prev[0]) > abs(prev[0]*tolerance):
					dc = max(maxDC/(1+beaconAdjustedX), 5)
					prev[0] = beaconAdjustedX
					commandQueue.put_nowait(
						(mw.COMMUNICATOR, cm.SET_DC, dc, (1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1), cm.ALL)
					)
					dcVar.set("{:.2f} %".format(dc))

					
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

	

