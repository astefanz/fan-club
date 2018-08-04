# Provisional gimmick for FCMkIII + OptiTrack


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
		
		tm = [time.time()]
		prev = [0]

		# This is a callback function that gets connected to the NatNet client and called once per mocap frame.
		def receiveNewFrame( frameNumber, markerSetCount, unlabeledMarkersCount, rigidBodyCount, skeletonCount,
							labeledMarkerCount, timecode, timecodeSub, timestamp, isRecording, trackedModelsChanged ):
			#print( "Received frame", frameNumber )
			pass
		# This is a callback function that gets connected to the NatNet client. It is called once per rigid body per frame
		def receiveRigidBodyFrame( id, position, rotation, tm, prev):
			
			
			#fposition = tuple(map(float, position))
			y = float(position[1])
			#frotation = tuple(map(float, rotation))
			#print( "Received frame for rigid body ", id,"\n\tposition: {:.2f}, {:.2f}, {:.2f}\n\trotation: {:.2f}, {:.2f}, {:.2f}".format(fposition[0], fposition[1], fposition[2], frotation[0], frotation[1], frotation[2]))
			
			#print("Position: {:3.4f} DC: {:3.2f}%".format(fposition[1], fposition[1]*100/2))
			
			if time.time() - tm[0] > 0.1 and abs(y - prev[0]) > abs(0.1*y):
				#print("p: ", prev[0], "a: ", abs(y-prev), ".1y: ", abs(0.1*y))
				prev[0] = y
				tm = time.time()
				commandQueue.put_nowait(
					(mw.COMMUNICATOR, cm.SET_DC, y*70/2, (1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1), cm.ALL)
				)
			else:
				return

		# This will create a new NatNet client
		streamingClient = nc.NatNetClient()

		# Configure the streaming client to call our rigid body handler on the emulator to send data out.
		streamingClient.newFrameListener = receiveNewFrame
		streamingClient.rigidBodyListener = lambda i,p,r: receiveRigidBodyFrame(i,p,r,tm, prev)

		# Start up the streaming client now that the callbacks are set up.
		# This will run perpetually, and operate on a separate thread.
		streamingClient.run()
		
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

	

