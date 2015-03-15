#General Python Modules
import fnmatch
import random
import string
import math

#General Vizard Modules
import viz
import vizmat

#My Modules
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

viz.go()
viz.phys.enable()

#Trial Variables
participant_id = 0
blockNumber = 0 #1-3
curTrialNumber = 0 #1-10

block = PRACTICE

'''
#Choose System
choices = ['IS900','Move','Kinect']
system = viz.choose('Choose system',choices)
'''
#system = IS900
#system = MOVE
system = KINECT

#General Group
workspace = viz.addGroup(parent=viz.WORLD)

#HandModel Setup
handModel = viz.add('models/hand.obj')
handModel.setScale([10,10,10])
handModel.visible(viz.OFF)

#RayModel Setup
rayModel = viz.add('models/ray-long.obj')
rayEnd = viz.addGroup(parent=rayModel)
rayEnd.setPosition([0,0,700])
rayModel.setScale([2,2,2])
	
controllerModel = viz.add('models/moveController.obj')
	
#Setting up Ray Physics
rayModel.collideMesh()
rayModel.disable(viz.DYNAMICS)
rayModel.enable(viz.COLLIDE_NOTIFY)

#WIM Setup
miniWorld = viz.addGroup(parent=viz.WORLD)
workspace.duplicate(viz.Scene1,parent=miniWorld)

miniWorld.setScale([.015,.015,.015])
miniWorld.setEuler([0,90,0]) #Offset for WIM on Tracker
miniWorld.visible(viz.OFF)

controllerModel.visible(viz.OFF)

#User Navigation Group
user = viz.addGroup(parent=viz.WORLD)
head = viz.addGroup(parent=user)
eye = viz.addGroup(parent=head)
handRay = viz.addGroup(parent=user)
handWim = viz.addGroup(parent=user)

rayModel.setParent(handRay)
rayModel.setPosition(0,0,-1.75) #For some reason obj center doesn't match causing rotation offset

controllerModel.setParent(handRay)
controllerModel.setPosition(0,0,-1.75) #For some reason obj center doesn't match causing rotation offset

miniWorld.setParent(handWim)

viewLink = viz.link(eye,viz.MainView,priority=2)
viewLink.setSrcFlag(viz.ABS_GLOBAL)

if system == IS900:
	#Connect to IS900 Sensors
	intersenseSystem = sensors.intersense(5,viz,20,head,handRay,handWim)
	print intersenseSystem.isValid()
	
if system == MOVE:
	#Connect to Move Sensors
	moveSystem = sensors.move(viz,.02,head,handRay,handWim)
	print moveSystem.isValid()
	
	#Calibration Instructions
	trialtools.setupCalImage('calibrate.png')

if system == KINECT:
	#Connect to Kinect Sensor
	kinectSystem = sensors.kinect(viz,20,head,handRay,handWim)
	print kinectSystem.isValid()

#Helper Classes
interaction = vetools.InteractionTools(viz,rayModel,handModel,head,handRay,handWim,miniWorld,workspace)
room = trialtools.generateRoom(viz,workspace,user)
dockingTrials = trialtools.generateTrials(viz,workspace,user,MAX_TRIALS)
state = vetools.states()

'''
#Prompt Tester for Participant Info
participant_id = viz.input( 'Please enter the participant number', str(0) )
while participant_id == 0:
	participant_id = viz.input( 'Please enter the participant number', str(0) )
	
block = viz.input( 'Please enter current block number 1-3', str(0) )
while block != 1 and  block != 2 and block != 3:
	block = viz.input( 'Please enter current block number 1-3', str(0) )
'''	
participant_id = 1000
block = 1
	
#Start Recording Information
record = trialtools.recorder(participant_id,dockingTrials)

#Determines what the technique and the order based on participant number
mode,systemOrder = trialtools.systemOrder(participant_id)
dockingTrials.chooseMatchSet(system,systemOrder)

room.load()

#mode = RAYCASTING
mode = HOMER
#mode = WIM

#Set technique for trial
if mode == WIM:
	state.wimEnabled = True
	state.wimSelect = True
	
	if system == KINECT:
		miniWorld.setParent(head)
		miniWorld.setPosition([0,-.5,9])
		miniWorld.setEuler([0,-35,0])
	
	miniWorld.visible(viz.ON)
	controllerModel.visible(viz.ON)
	rayModel.visible(viz.OFF)
	rayEnd.setPosition([0,0,0.5])

def pickup():	
	if state.intersectedObjects:
			if state.wimEnabled:
				if state.wimSelect:
					interaction.wimAttach(state.intersectedObjects[0])
					print 'wim'
			else:
				if mode == RAYCASTING:
					interaction.raycastingAttach(state.intersectedObjects[0])
					print 'raycasting'
				elif mode == HOMER:
					interaction.homerAttach(state.intersectedObjects[0])
					print 'homer'
						
			#block variables
			state.obj = state.intersectedObjects
			state.attached = True

			if block == DOCKING:
				if not state.start:
					record.trialStart()
					state.start = True
					
def drop():
	if state.obj:
		interaction.release(mode,state.obj[0])
		
		#block variables
		state.attached = False
		state.obj = []
		
		if block == DOCKING:
			if state.goodDrop:
				state.start = False
				
				record.trialEnd(state.goodDrop)
				viz.playSound('OOT_Fanfare_Item.wav')
				dockingTrials.nextTrial()
			else:
				record.writeDrop(mode)

def onButtonUp(button):
	if system == IS900:
		if button == 5:
			drop()
	if system == MOVE:
		if button == 1:
			if not moveSystem.isCalibrated:
				moveSystem.calibrate()
				print "calibrate"
			else:
				drop()
		if button == 2:
			state.nav_state[0] = False
		if button == 7:
			state.nav_state[2] = False
		if button == 4:
			state.nav_state[1] = False
viz.callback(sensors.BUTTON_UP,onButtonUp)

def onButtonDown(button):
	if system == IS900:
		if button == 5:
			pickup()
	if system == MOVE:
		if button == 1:
			pickup()
		if button == 2:
			state.nav_state[0] = True
		if button == 7:
			state.nav_state[2] = True
		if button == 4:
			state.nav_state[1] = True
viz.callback(sensors.BUTTON_DOWN,onButtonDown)

def onSensorDown(e):
	print e
	
	if e.object is intersenseSystem.raySensor:
		pickup()

viz.callback(viz.SENSOR_DOWN_EVENT,onSensorDown)

def onSensorUp(e):
	if e.object is intersenseSystem.raySensor:
		drop()

viz.callback(viz.SENSOR_UP_EVENT,onSensorUp)

def updateScene():
	#update tracker information
	if system == IS900:
		intersenseSystem.update()
		
		if intersenseSystem.rayJoystick[9] > .8:
			state.nav_state[0] = True
			
		else:
			state.nav_state[0] = False
			
		if intersenseSystem.rayJoystick[8] > .8:
			state.nav_state[2] = False
			state.nav_state[1] = True
			
		elif intersenseSystem.rayJoystick[8] < -.8:
			state.nav_state[2] = True
			state.nav_state[1] = False

		else:
			state.nav_state[2] = False
			state.nav_state[1] = False
		
		'''
		if intersenseSystem.rayJoystick[1] < -.8:
			state.nav_state[0] = True
			
			print intersenseSystem.rayJoystick
		else:
			state.nav_state[0] = False
			
		if intersenseSystem.rayJoystick[0] > .8:
			state.nav_state[2] = False
			state.nav_state[1] = True
			
			print intersenseSystem.rayJoystick
		elif intersenseSystem.rayJoystick[0] < -.8:
			state.nav_state[2] = True
			state.nav_state[1] = False
			
			print intersenseSystem.rayJoystick
		else:
			state.nav_state[2] = False
			state.nav_state[1] = False
		'''
	if system == MOVE:
		moveSystem.update()
	if system == KINECT:
		kinectSystem.update()
		
		if state.wimAttached == True:
			interaction.wimUpdate()
		
	if state.attached:
		if (mode == HOMER) & (not state.wimSelect):
			interaction.homerMove()
		
		if state.wimSelect:
			interaction.wimMove(state.obj[0])
	
	if block == DOCKING:
		state.intersectedObjects = vetools.formatIntersectionResults(viz.intersect(rayModel.getPosition(viz.ABS_GLOBAL), rayEnd.getPosition(viz.ABS_GLOBAL), all=True),[rayModel,controllerModel,dockingTrials.match,dockingTrials.backdrop])
		state.goodDrop = dockingTrials.inBounds(10,10)
	else:		
		state.intersectedObjects = vetools.formatIntersectionResults(viz.intersect(rayModel.getPosition(viz.ABS_GLOBAL), rayEnd.getPosition(viz.ABS_GLOBAL), all=True),[rayModel,controllerModel,room.walls])
		
		
		#Navigation Actions
		user.setCenter(head.getPosition())
		if state.nav_state[0]:
			user.setPosition(vizmat.MoveAlongVector(user.getPosition(viz.ABS_GLOBAL),vizmat.VectorToPoint(rayModel.getPosition(viz.ABS_GLOBAL),rayEnd.getPosition(viz.ABS_GLOBAL)),100*viz.elapsed()),viz.ABS_GLOBAL)
		if state.nav_state[1]:
			user.setEuler([60*viz.elapsed(),0,0],viz.RELATIVE)
		if state.nav_state[2]:
			user.setEuler([-60*viz.elapsed(),0,0],viz.RELATIVE)
				
	#Highlighting Effect
	if (not state.attached):
		if state.intersectedObjects:
			[node.object.emissive([0,0,0]) for node in state.lastSelection]
			state.intersectedObjects[0].object.emissive(viz.GREEN)
			state.lastSelection = state.intersectedObjects
			
		elif state.lastSelection:
			[node.object.emissive([0,0,0]) for node in state.lastSelection]	

vizact.ontimer(UPDATE_RATE,updateScene)

def mykeyboard(key):
	#close file when exiting the system
	if key == viz.KEY_ESCAPE:
		print 'Escape Key'
	
	#start timer for capstone task
	if key == 't':
		if not state.finalStart:
			print 'start capstone'
			record.startCapstone()
			state.finalStart = True
		else:
			print 'end capstone'
			record.endCapstone(room)
			state.finalStart = False
	
	#move to next task
	if key == ' ':
		global block
		
		block = block + 1
		
		if block == DOCKING:
			room.remove()
			dockingTrials.setup()
		if block == CAPSTONE:
			dockingTrials.clear()
			room.load()
			room.startingPosition()
			
	#Next trial
	if key == 'n':
		state.start = False
		
		record.trialEnd(False)
		dockingTrials.nextTrial()
			
	#recalibrate
	if key == 'c':
		if system == MOVE:
			moveSystem.head.setPosition([0,0,0])
			moveSystem.isCalibrated = False
			trialtools.setupCalImage('calibrate.png')
		
	#Viewpoint reset
	if key == 'r':
		user.setPosition(13, 1.8, 11)
		head.setEuler([42.4,5,0],viz.VIEW_ORI)
	
	#Navigation Keys
	if key == viz.KEY_UP:
		state.nav_state[0] = not state.nav_state[0]
		
	if key == viz.KEY_RIGHT:
		state.nav_state[1] = not state.nav_state[1]
		
	if key == viz.KEY_LEFT:
		state.nav_state[2] = not state.nav_state[2]
		
	#Wim Select Keys
	if key == 'w':
		if state.wimAttached == False:
			state.wimAttached = True
			controllerModel.visible(viz.OFF)
			
			interaction.wimPickup()
		else:
			state.wimAttached = False
			controllerModel.visible(viz.ON)
			
			interaction.wimRelease(head)
			
	if key == 'h':
		if miniWorld.getVisible() == viz.ON:
			miniWorld.visible(viz.OFF)
		else:
			miniWorld.visible(viz.ON)
			
	if key == 'i':
		z = miniWorld.getPosition()
		z[2] = z[2]-.25
		miniWorld.setPosition(z)
		
	if key == 'o':
		z = miniWorld.getPosition()
		z[2] = z[2]+.25
		miniWorld.setPosition(z)
		
	#Mode select
	if key == 'm':
		global mode
		
		mode = not mode
		
		if mode == HOMER:
			print 'HOMER MODE'
		else:
			print 'RAYCASTING MODE'
			
	#Pickup
	if key == 'p':
		pickup()
		
	#Drop
	if key == 'd':
		drop()
		
viz.callback(viz.KEYBOARD_EVENT,mykeyboard)

def onExit():
	print 'File Closed'
	record.close()
viz.callback(viz.EXIT_EVENT,onExit)

def onCollide(e):
	if (not state.attached) and (system == MOVE):
		#viz.director(rumble,75,.25)
		viz.director(moveSystem.rumble,75,.25)
viz.callback(viz.COLLIDE_BEGIN_EVENT, onCollide )

