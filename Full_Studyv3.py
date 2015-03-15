#General Python Modules
import fnmatch
import random
import string
import math

#General Vizard Modules
import viz
import vizmat

#My Modules
import kinecttools
import vetools
import trialtools
import sensors

#Constants
UPDATE_RATE = 0
FOV = 60

RAYCASTING = 0
HOMER = 1
WIM = 2

PRACTICE = 1
DOCKING = 2
CAPSTONE = 3

MAX_TRIALS = 10

IS900 = 0
MOVE = 1
KINECT = 2

#View Setup
viz.MainWindow.fov(FOV, viz.AUTO_COMPUTE)
view = viz.MainView

viz.go()
viz.phys.enable()

#Global Variables
oldTriggerState = 0
nav_state = [0,0,0]

lastSelection = []
obj = []

#Trial Variables
participant_id = 0
blockNumber = 0 #1-3
curTrialNumber = 0 #1-10

#States
wimSelect = False
attached = False
wimEnabled = False

start = False
finalStart = False

wimShow = False

mode = RAYCASTING
state = PRACTICE

#Choose System
choices = ['IS900','Move','Kinect']
system = viz.choose('Choose system',choices)

#Hand Setup
hand = viz.add('models/hand.obj')
hand.visible(viz.OFF)

#Ray Setup
if system == MOVE or system == IS900:
	ray = viz.add('models/ray-long.obj')
	rayEnd = viz.addGroup(parent=ray)
	rayEnd.setPosition([0,0,700])
	
	controller = viz.add('models/moveController.obj')
	controller.setScale([10,10,10])
if system == KINECT:
	ray = viz.add('models/kinectRay-long.obj')
	rayEnd = viz.addGroup(parent=ray)
	rayEnd.setPosition([0,0,-700])
	
	controller = viz.add('models/kinectMoveController.obj')
	controller.setScale([10,10,10])

#WIM Setup
miniWorld = viz.addGroup()

miniWorld.setScale([.05,.05,.05])
miniWorld.visible(viz.OFF)

controller.setScale([.25,.25,.25])
controller.visible(viz.OFF)

if system == IS900:
	#Connect to IS900 Sensors
	intersenseSystem = sensors.intersense(4,viz,1)
	print intersenseSystem.isValid()
	
if system == MOVE:
	#Connect to Move Sensors
	moveSystem = sensors.move(viz,.001)
	print moveSystem.isValid()
	
	#Calibration Instructions
	trialtools.setupCalImage('calibrate.png')
	view.setScene(viz.Scene2)

if system == KINECT:
	#Connect to Kinect Sensor
	kinectSystem = sensors.kinect(viz,.1)
	help = sensors.move(viz,.01)
	
	print kinectSystem.isValid()

#Links Ray to View
viewLink = viz.link(view, ray, enabled=True)
viewLink.setDstFlag(viz.LINK_POS_RAW) #Don't offset viewpoint position with eyeheight
transOperator = viewLink.preTrans([0,0,.1]) #Ray translation from camera
rotateOperator = viewLink.preEuler([0,0,0])
 
#Links View to Head (Head Tracking)
head = viz.addGroup()
headTrackingLink = viz.link(head, view, enabled=True)
headTrans = headTrackingLink.preTrans([0,0,0])
headRot = headTrackingLink.preEuler([0,0,0])

#Links MiniWorld to View
wimLink = viz.link(view, miniWorld, enabled=False)
wimLink.setDstFlag(viz.LINK_POS_RAW)
if system == MOVE or system == IS900:
	wimTransOperator = wimLink.preTrans([0,0,.1])
	wimRotateOperator = wimLink.preEuler([0,0,0])
if system == KINECT:
	wimTransOperator = wimLink.preTrans([0,-1,3])
	wimRotateOperator = wimLink.preEuler([0,-45,0])

#Setting up Ray Physics
ray.collideMesh()
ray.disable(viz.DYNAMICS)
ray.enable(viz.COLLIDE_NOTIFY)

#Helper Classes
interaction = vetools.InteractionTools(viz,ray,hand,miniWorld)
room = trialtools.generateRoom(viz,interaction.world,head)
dockingTrials = trialtools.generateTrials(viz,interaction.world,head,MAX_TRIALS)

#Prompt Tester for Participant Info
participant_id = viz.input( 'Please enter the participant number', str(0) )
while participant_id == 0:
	participant_id = viz.input( 'Please enter the participant number', str(0) )
	
state = viz.input( 'Please enter current block number 1-3', str(0) )
while state != 1 and  state != 2 and state != 3:
	state = viz.input( 'Please enter current block number 1-3', str(0) )

#Start Recording Information
record = trialtools.recorder(participant_id,dockingTrials)

#Determines what the technique and the order based on participant number
mode,systemOrder = trialtools.systemOrder(participant_id)
dockingTrials.chooseMatchSet(system,systemOrder)

#Set technique for trial
if mode == HOMER:
	bodyLink.setEnabled(True)
elif mode == WIM:
	wimLink.setEnabled(True)
	
	if system == MOVE or system == IS900:
		wimEnabled = True
		wimSelect = True
	if system == KINECT:
		wimShow = True
	
	miniWorld.visible(viz.ON)
	controller.visible(viz.ON)
	ray.visible(viz.OFF)
	rayEnd.setPosition([0,0,0.5])

#Set up default view and background color
viz.clearcolor(viz.BLACK)

headLight = view.getHeadLight()
headLight.disable()

#Jump to section
if (state == PRACTICE):
	room.load()
elif (state == DOCKING):
	dockingTrials.setup()
elif (state == CAPSTONE):
	room.load()
	
if system == MOVE:
	head.setPosition(0,4,-8)
	head.setEuler([0,0,0],viz.ABS_GLOBAL)
if system == IS900:
	room.startingPosition()
if system == KINECT:
	#Initialize Head Tracking Data
	room.startingPosition()

def updateScene():
	global lastSelection
	global attached
	global obj
	global state
	
	if system == IS900:
		global start
		
		intersenseSystem.update()
		
		#Update View based on Head Tracking
		if (state != DOCKING):
			headTrans.setPosition(intersenseSystem.headPosition())
			#headRot.setQuat(intersenseSystem.headQuat())
		
		#Ray Position & Orientation Data
		transOperator.setPosition(intersenseSystem.rayPosition())
		rotateOperator.setQuat(intersenseSystem.rayQuat())
		
		if wimEnabled:
			#WIM Position & Orientation Data		
			wimTransOperator.setPosition(intersenseSystem.wimPosition())
			wimRotateOperator.setQuat(intersenseSystem.wimQuat())
			
			#Set Controller Model Position & Orientation Data
			controller.setPosition(ray.getPosition())
			controller.setQuat(ray.getQuat())
					
		if attached:
			if (mode == HOMER) & (not wimSelect):
				interaction.homerMove()
			
			if wimSelect:
				interaction.wimMove(obj[0])
				
		#Navigation Actions
		if state != DOCKING:
			if intersenseSystem.rayJoystick[1] > 191:
				head.setPosition(vizmat.MoveAlongVector(head.getPosition(viz.ABS_GLOBAL),vizmat.VectorToPoint(ray.getPosition(viz.ABS_GLOBAL),rayEnd.getPosition(viz.ABS_GLOBAL)),10*viz.elapsed()),viz.ABS_GLOBAL)
			if intersenseSystem.rayJoystick[0] > 200:
				head.setEuler([60*viz.elapsed(),0,0],viz.REL_PARENT)
			if intersenseSystem.rayJoystick[0] < 55:
				head.setEuler([-60*viz.elapsed(),0,0],viz.REL_PARENT)
	
	if system == MOVE:
		global wimSelect
		global start
		
		moveSystem.update()
		
		#Ray Position & Orientation Data
		transOperator.setPosition(moveSystem.rayPosition())
		rotateOperator.setQuat(moveSystem.rayQuat())
	
		if wimEnabled:
			#WIM Position & Orientation Data
			wimTransOperator.setPosition(moveSystem.wimPosition())
			wimRotateOperator.setQuat(moveSystem.wimQuat())
			
			#Set Controller Model Position & Orientation Data
			controller.setPosition(ray.getPosition())
			controller.setQuat(ray.getQuat())
		
		if attached:
			if (mode == HOMER) & (not wimSelect):
				interaction.homerMove()
			elif wimSelect:
				interaction.wimMove(obj[0])

		button = moveSystem.getButtons()

		#Navigation Actions
		if state != DOCKING:
			if button[2]:
				head.setPosition(vizmat.MoveAlongVector(head.getPosition(viz.ABS_GLOBAL),vizmat.VectorToPoint(ray.getPosition(viz.ABS_GLOBAL),rayEnd.getPosition(viz.ABS_GLOBAL)),10*viz.elapsed()),viz.ABS_GLOBAL)
			if button[4] & (not button[5]):
				head.setEuler([60*viz.elapsed(),0,0],viz.REL_PARENT)
			if button[7] & (not button[6]):
				head.setEuler([-60*viz.elapsed(),0,0],viz.REL_PARENT)
				
		#Trigger Actions
		if button[1] != moveSystem.oldTriggerState:
			if button[1]:
				if (not moveSystem.isCalibrated):
					#Pos Calibration
					moveSystem.calibrate()
					
					#Switch Back to Main Scene
					if state != DOCKING:
						room.startingPosition()
					else:
						dockingTrials.trialView()

					view.setScene(viz.Scene1)
				
				if intersectedObjects:
					if wimEnabled:
						if wimSelect:
							interaction.wimAttach(intersectedObjects[0])
							print 'wim'
					else:
						if mode == RAYCASTING:
							interaction.raycastingAttach(intersectedObjects[0])
							print 'raycasting'
						elif mode == HOMER:
							interaction.homerAttach(intersectedObjects[0])
							print 'homer'
								
					#State variables
					obj = intersectedObjects
					attached = True
					
					if state == DOCKING:
						if not start:
							record.trialStart()
							start = True
			
			elif not button[1]:
				if obj:
					interaction.release(mode,obj[0])
					
					#State variables
					attached = False
					obj = []
					
					if state == DOCKING:
						if goodDrop:
							start = False
							
							record.trialEnd(goodDrop)
							dockingTrials.nextTrial()
						else:
							record.writeDrop(mode)
		
		moveSystem.oldTriggerState = button[1]
	
	if system == KINECT:
		global intersectedObjects
		global initGrabVector
		global nav_state
		
		#WIM Specific
		global XMoveInit
		global initPos
		global wimPos
		
		global wimEnabled
		global wimShow
		
		#Docking Task
		global goodDrop
		
		#Update skeleton position
		kinectSystem.update()
	
		#Set headposition
		if (state != DOCKING):
			headTrans.setPosition(kinectSystem.headPosition())
	
		#Ray position and Orientation
		transOperator.setPosition(kinectSystem.rayPosition())
		rotateOperator.setQuat(kinectSystem.rayQuat())
		
		if (mode == WIM):
			if wimShow:
				if wimSelect:
					if calibration:
						wimDummyObject
						wimTransOperator.setPosition(wimDummyObject.getPosition(viz.ABS_GLOBAL))
						wimRotateOperator.setQuat(wimDummyObject.getQuat(viz.ABS_GLOBAL))
					else:
						wimDummyObject.setPosition(wimTransOperator.getPosition(),viz.ABS_GLOBAL)
						wimDummyObject.setQuat(wimRotateOperator.getQuat(),viz.ABS_GLOBAL)
						
						calibration = True
				if not wimSelect:
					#Set Controller Model Position & Orientation Data
					transOperator.setPosition(kinecttools.addOffset(transOperator.getPosition(),[0,2,.5]))
					
					controller.setPosition(ray.getPosition())
					controller.setQuat(ray.getQuat())
				if not wimSelect and attached:
					interaction.wimMove(obj[0])
					print 'WIM'
					
		if (mode == HOMER) & attached:
			interaction.homerMove()
			print 'Homer'

	if state == DOCKING:
		#Check to see if object is in one another
		goodDrop = dockingTrials.inBounds(10,10)
	
	if state == DOCKING:
		intersectedObjects = vetools.formatIntersectionResults(viz.intersect(ray.getPosition(viz.ABS_GLOBAL), rayEnd.getPosition(viz.ABS_GLOBAL), all=True),ray,controller,dockingTrials.match)
	else:
		intersectedObjects = vetools.formatIntersectionResults(viz.intersect(ray.getPosition(viz.ABS_GLOBAL), rayEnd.getPosition(viz.ABS_GLOBAL), all=True),ray,controller,room.walls)
	
	#Highlighting Effect
	if (not attached):
		if intersectedObjects:
			[node.object.emissive([0,0,0]) for node in lastSelection]
			intersectedObjects[0].object.emissive(viz.GREEN)
			lastSelection = intersectedObjects
			
		elif lastSelection:
			[node.object.emissive([0,0,0]) for node in lastSelection]	
	
	if system == KINECT:
		#Navigation Actions
		if state != DOCKING:
			if nav_state[0]:
				if (mode == WIM):
					head.setPosition(vizmat.MoveAlongVector(head.getPosition(viz.ABS_GLOBAL),vizmat.VectorToPoint(ray.getPosition(viz.ABS_GLOBAL),rayEnd.getPosition(viz.ABS_GLOBAL)),-50*viz.elapsed()),viz.ABS_GLOBAL)
				else:
					head.setPosition(vizmat.MoveAlongVector(head.getPosition(viz.ABS_GLOBAL),vizmat.VectorToPoint(ray.getPosition(viz.ABS_GLOBAL),rayEnd.getPosition(viz.ABS_GLOBAL)),50*viz.elapsed()),viz.ABS_GLOBAL)
			if nav_state[1]:
				head.setEuler([60*viz.elapsed(),0,0],viz.REL_PARENT)
			if nav_state[2]:
				head.setEuler([-60*viz.elapsed(),0,0],viz.REL_PARENT)
		
vizact.ontimer(UPDATE_RATE,updateScene)

def onSensorDown(e):
    if e.object is intersenseSystem.raySensor:
		global intersectedObjects
		global attached
		global obj
		global start
		
		if intersectedObjects:
			if wimEnabled:
				if wimSelect:
					interaction.wimAttach(intersectedObjects[0])
					print 'wim'
			else:
				if mode == RAYCASTING:
					interaction.raycastingAttach(intersectedObjects[0])
					print 'raycasting'
				elif mode == HOMER:
					interaction.homerAttach(intersectedObjects[0])
					print 'homer'
						
			#State variables
			obj = intersectedObjects
			attached = True

			if state == DOCKING:
				if not start:
					record.trialStart()
					start = True
viz.callback(viz.SENSOR_DOWN_EVENT,onSensorDown)

def onSensorUp(e):
	if e.object is intersenseSystem.raySensor:
		global obj
		global attached
		global start
		global goodDrop
		
		global wimSelect
		
		if obj:
			interaction.release(mode,obj[0])
			
			#State variables
			attached = False
			obj = []
			
			if state == DOCKING:
				if goodDrop:
					start = False
					
					record.trialEnd(goodDrop)
					dockingTrials.nextTrial()
				else:
					record.writeDrop(mode)
viz.callback(viz.SENSOR_UP_EVENT,onSensorUp)

#Changes mode between Raycasting & HOMER
def cycleMode():
	global mode
	
	mode = not mode
	
	if mode == HOMER:
		print 'HOMER MODE'
	else:
		print 'RAYCASTING MODE'
vizact.onkeydown('m',cycleMode)

def mykeyboard(key):
	#close file when exiting the system
	if key == viz.KEY_ESCAPE:
		print 'Escape Key'
	
	#start timer for capstone task
	if key == 't':
		global finalStart
		
		if not finalStart:
			print 'start capstone'
			record.startCapstone()
			finalStart = True
		else:
			print 'end capstone'
			record.endCapstone()
			finalStart = False
	
	#move to next task
	if key == ' ':
		global state
	
		state = state + 1
		
		if state == DOCKING:
			room.remove()
			dockingTrials.setup()
		if state == CAPSTONE:
			dockingTrials.clear()
			room.load()
			room.startingPosition()
			
	#Next trial
	if key == 'n':
		global start
		
		start = False
		
		record.trialEnd(False)
		dockingTrials.nextTrial()
			
	#recalibrate
	if key == 'c':
		global calibration
	
		calibration = False
					
		#Switch Back to Calibration Scene
		head.setPosition([0,4,-8])
		head.setEuler([0,0,0],viz.VIEW_ORI)
		
		view.setScene(viz.Scene2)
		headLight.enable()
	
	#Viewpoint reset
	if key == 'r':
		head.setPosition([-23.5,130,-23])
		head.setEuler([42.4,5,0],viz.VIEW_ORI)
			
	#Kinect Drop
	if key == 'd':
		global obj
		global attached
		global start
		global goodDrop
		
		global wimSelect
		global calibration
		
		if wimSelect:
			wimSelect = False
			calibration = False
		
		if obj:
			interaction.release(mode,obj[0])
					
			#State variables
			attached = False
			obj = []
			
			if state == DOCKING:
				if goodDrop:
					start = False
					
					record.trialEnd(goodDrop)
					dockingTrials.nextTrial()
				else:
					record.writeDrop(mode)
					
	#Kinect Pickup
	if key == 'p':
		global intersectedObjects
		global attached
		global obj
		global start
		
		if intersectedObjects:
			if mode == RAYCASTING:
				interaction.raycastingAttach(intersectedObjects[0])
			elif mode == HOMER:
				interaction.homerAttach(intersectedObjects[0])
			elif mode == WIM:
				interaction.wimAttach(intersectedObjects[0])
					
			#State variables
			obj = intersectedObjects
			attached = True
			
			if state == DOCKING:
				if not start:
					record.trialStart()
					start = True
	
	#Navigation Keys
	if key == viz.KEY_UP:
		nav_state[0] = not nav_state[0]
		
	if key == viz.KEY_RIGHT:
		nav_state[1] = not nav_state[1]
		
	if key == viz.KEY_LEFT:
		nav_state[2] = not nav_state[2]
		
	#Wim Select Keys
	if key == 'w':
		wimSelect = True
viz.callback(viz.KEYBOARD_EVENT,mykeyboard)

def onExit():
	print 'File Closed'
	record.close()
viz.callback(viz.EXIT_EVENT,onExit)

def onCollide(e):
	global attached
	
	if (not attached) and (system == MOVE):
		#viz.director(rumble,75,.25)
		viz.director(moveSystem.rumble,75,.25)
viz.callback(viz.COLLIDE_BEGIN_EVENT, onCollide )
