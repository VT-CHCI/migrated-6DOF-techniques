#General Python Modules
import fnmatch
import random
import string
import math
import time
import sys
import os

#General Vizard Modules
import viz
import vizmat

#My Modules
import kinect
import vetools
import trialtools

viz.go()
viz.phys.enable()

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

#Global Variables
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

calibration = False

mode = RAYCASTING
state = PRACTICE

#Load Models
ray = viz.add('models/kinectRay.obj')
hand = viz.add('models/hand.obj')
controller = viz.add('models/kinectMoveController.obj')

#View Setup
viz.MainWindow.fov(FOV, viz.AUTO_COMPUTE)
view = viz.MainView

#Connect to Kinect Sensor
sensor = viz.add('KinectSensor.dls')

#Declare Groups
world = viz.addGroup()
objParent = viz.addGroup(parent=world)
rayEnd = viz.addGroup(parent=ray)

#HOMER Specific Groups
body = viz.addGroup()
virtualHand = viz.addGroup(parent=world)
posMarker = viz.addGroup(parent=body)

#WIM Specific Groups
miniWorld = viz.addGroup()
miniObjParent = viz.addGroup(parent=miniWorld)
wimDummyObject = viz.addGroup(parent=objParent)

#Head Tracking Specific Groups
head = viz.addGroup()

#Helper Classes
setup = vetools.VizardWorldSetup(viz)
interaction = vetools.InteractionTools(viz,ray,hand,virtualHand,body,objParent,posMarker,miniObjParent,world)
room = trialtools.generateRoom(viz,world,head)
dockingTrials = trialtools.generateTrials(viz,world,head,MAX_TRIALS)

#Ray Setup
rayLink = viz.link(ray, objParent, enabled=True)
rayEnd.setPosition([0,0,-43])

#Hand Setup
hand.visible(viz.OFF)
hand.parent(virtualHand)

#WIM Setup
world.duplicate(viz.Scene1,parent=miniWorld)
miniWorld.setScale([.05,.05,.05])
miniWorld.visible(viz.OFF)

controller.setScale([.5,.5,.5])
controller.visible(viz.OFF)

#Lights Setup
headLight = view.getHeadLight()
room.addLights()

#Links Ray to View
viewLink = viz.link(view, ray, enabled=True)
viewLink.setDstFlag(viz.LINK_POS_RAW) #Don't offset viewpoint position with eyeheight
transOperator = viewLink.preTrans([0,0,.1]) #Ray translation from camera
rotateOperator = viewLink.preEuler([0,0,0])

#Links View to Head
headTrackingLink = viz.link(head, view, enabled=True)
headTrans = headTrackingLink.preTrans([0,0,.1])

#Links Body to View
bodyLink = viz.link(view, body, enabled=False)
bodyLink.setDstFlag(viz.LINK_POS_RAW)
bodyLink.preTrans([0,-1.2,0])

#Links MiniWorld to View
wimLink = viz.link(view, miniWorld, enabled=True)
wimLink.setDstFlag(viz.LINK_POS_RAW)
wimTransOperator = wimLink.preTrans([0,-1,3])
wimRotateOperator = wimLink.preEuler([0,-45,0])

#Setting up Ray Physics
ray.collideMesh()
ray.disable(viz.DYNAMICS)
ray.enable(viz.COLLIDE_NOTIFY)

#Initialize Head Tracking Data
head.setPosition([0,0,5],viz.ABS_GLOBAL)
skeleton = kinect.skeleton(sensor.get())

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
dockingTrials.chooseMatchSet(2,systemOrder)

#Set technique for trial
if mode == HOMER:
	bodyLink.setEnabled(True)
elif mode == WIM:
	wimShow = True
	
	miniWorld.visible(viz.ON)
	controller.visible(viz.ON)
	ray.visible(viz.OFF)
	rayEnd.setPosition([0,0,-.40])

#Jump to test section
if (state == PRACTICE):
	room.load()
elif (state == DOCKING):
	dockingTrials.startTrials()
elif (state == CAPSTONE):
	room.load()

#Set up default view and background color
viz.clearcolor(viz.BLACK)

view.setPosition(0,4,-8)
view.setEuler(0,0,0)

def updateScene():
	global intersectedObjects
	global initGrabVector
	global lastSelection
	global nav_state
	global attached
	global obj
	
	#WIM Specific
	global calibration
	global XMoveInit
	global initPos
	global wimPos
	
	global wimEnabled
	global wimShow
	
	#Docking Task
	global goodDrop
	
	#Update skeleton position
	skeleton.update(sensor.get())
	
	#Set headposition
	headTrans.setPosition(kinect.scaleData(skeleton.HEAD[0:3]))
	
	#Ray posiiton and Orientation
	horizontalVector = vizmat.VectorToPoint([-1,0,0],[1,0,0])
	
	hands = kinect.midpoint(skeleton.HAND_LEFT[0:3],skeleton.HAND_RIGHT[0:3])
	elbows = kinect.midpoint(skeleton.ELBOW_LEFT[0:3],skeleton.ELBOW_RIGHT[0:3])
	
	rayVector = kinect.unmirror(vizmat.VectorToPoint(elbows,hands))
	rotVector = vizmat.VectorToPoint(skeleton.HAND_LEFT[0:3],skeleton.HAND_RIGHT[0:3])
	
	m = viz.Matrix()
	m.makeVecRotVec(rotVector,horizontalVector)
	m.postQuat(vizmat.LookToQuat(rayVector))
	
	rotateOperator.setQuat(m.getQuat())
	transOperator.setPosition(vetools.subtract(kinect.scaleData(hands),kinect.scaleData(skeleton.HEAD[0:3])),viz.ABS_GLOBAL)
	
	if (mode == WIM):
		if wimShow:
			if wimSelect:
				if calibration:
					wimTransOperator.setPosition(wimDummyObject.getPosition(viz.ABS_GLOBAL))
					wimRotateOperator.setQuat(wimDummyObject.getQuat(viz.ABS_GLOBAL))
				else:
					wimDummyObject.setPosition(wimTransOperator.getPosition(),viz.ABS_GLOBAL)
					wimDummyObject.setQuat(wimRotateOperator.getQuat(),viz.ABS_GLOBAL)
					
					calibration = True
			if not wimSelect:
				#Set Controller Model Position & Orientation Data
				transOperator.setPosition(kinect.addOffset(transOperator.getPosition(),[0,2,.5]))
				
				controller.setPosition(ray.getPosition())
				controller.setQuat(ray.getQuat())
			if not wimSelect and attached:
				interaction.wimMove(obj[0])
				
	if (mode == HOMER) & attached:
		interaction.homerMove()
		print 'Homer'
		
	if state == DOCKING:
		#Check to see if object is in one another
		goodDrop = dockingTrials.inBounds(1,5)

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

	#Navigation Actions
	if state != DOCKING:
		if nav_state[0]:
			head.setPosition(vizmat.MoveAlongVector(head.getPosition(viz.ABS_GLOBAL),vizmat.VectorToPoint(ray.getPosition(viz.ABS_GLOBAL),rayEnd.getPosition(viz.ABS_GLOBAL)),5*viz.elapsed()),viz.ABS_GLOBAL)
		if nav_state[1]:
			head.setEuler([60*viz.elapsed(),0,0],viz.REL_PARENT)
		if nav_state[2]:
			head.setEuler([-60*viz.elapsed(),0,0],viz.REL_PARENT)

vizact.ontimer(UPDATE_RATE,updateScene)

def pickup():
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
vizact.onkeydown('p', pickup)

def drop():
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
vizact.onkeydown('d', drop)

def mykeyboard(key):
	global nav_state
	global wimSelect
	
	global calibration
	global wimPos
	
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
			dockingTrials.startTrials()
		if state == CAPSTONE:
			dockingTrials.clear()
			room.load()
			
	#Next trial
	if key == 'n':
		global start
		
		start = False
		
		record.trialEnd(False)
		dockingTrials.nextTrial()
	
	#Viewpoint reset
	if key == 'r':
		head.setPosition(-23.5,10.6,-23)
		head.setEuler(42.4,5,0)
	
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
