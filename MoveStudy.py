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
SCALING_FACTOR = 0.01

#Global Variables
calibrationPos = [0,0,0]
oldTriggerState = 0
lastSelection = []
obj = []

#Trial Variables
participant_id = 0
blockNumber = 0 #1-3
curTrialNumber = 0 #1-10

#States
calibration = False
wimSelect = False
attached = False
wimEnabled = False
start = False
finalStart = False

mode = RAYCASTING
state = PRACTICE

#Load Models
ray = viz.add('models/ray.obj')
hand = viz.add('models/hand.obj')
controller = viz.add('models/moveController.obj')

#View Setup
viz.MainWindow.fov(FOV, viz.AUTO_COMPUTE)
view = viz.MainView

#Connect to Move Sensors
raySensor = viz.add('MoveSensor.dls')
wimSensor = viz.add('MoveSensor.dls')

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

#Helper Classes
setup = vetools.VizardWorldSetup(viz)
interaction = vetools.InteractionTools(viz,ray,hand,virtualHand,body,objParent,posMarker,miniObjParent,world)
room = trialtools.generateRoom(viz,world,view)
dockingTrials = trialtools.generateTrials(viz,world,view,MAX_TRIALS)

#Calibration Instructions
setup.setupCalImage('calibrate.png')
view.setScene(viz.Scene2)

#Ray Setup
rayLink = viz.link(ray, objParent, enabled=True)
rayEnd.setPosition([0,0,43])

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

#Links Body to View
bodyLink = viz.link(view, body, enabled=False)
bodyLink.setDstFlag(viz.LINK_POS_RAW)
bodyLink.preTrans([0,-1.2,0])

#Links MiniWorld to View
wimLink = viz.link(view, miniWorld, enabled=False)
wimLink.setDstFlag(viz.LINK_POS_RAW)
wimTransOperator = wimLink.preTrans([0,0,.1])
wimRotateOperator = wimLink.preEuler([0,0,0])

#Setting up Ray Physics
ray.collideMesh()
ray.disable(viz.DYNAMICS)
ray.enable(viz.COLLIDE_NOTIFY)	

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
dockingTrials.chooseMatchSet(1,systemOrder)

#Set technique for trial
if mode == HOMER:
	bodyLink.setEnabled(True)
elif mode == WIM:
	wimLink.setEnabled(True)
	wimEnabled = True
	wimSelect = True
	
	miniWorld.visible(viz.ON)
	controller.visible(viz.ON)
	ray.visible(viz.OFF)
	rayEnd.setPosition([0,0,.40])

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
	global calibrationPos
	global oldTriggerState
	global calibration
	global lastSelection
	global attached
	global obj
	global wimSelect
	
	global state
	global start
	
	rayData = raySensor.get()
	wimData = wimSensor.get()
		
	#Ray Position & Orientation Data
	transOperator.setPosition(vetools.configPos(calibration,rayData[0:3],SCALING_FACTOR,calibrationPos))
	rotateOperator.setQuat(vetools.configQuat(rayData[3:7]))
	
	if wimEnabled:
		#WIM Position & Orientation Data
		wimTransOperator.setPosition(vetools.configPos(calibration,wimData[0:3],SCALING_FACTOR,calibrationPos,[0,.5,.5]))
		wimRotateOperator.setQuat(vetools.configQuat(wimData[3:7],[0,90,0]))
		
		#Set Controller Model Position & Orientation Data
		controller.setPosition(ray.getPosition())
		controller.setQuat(ray.getQuat())
		
		#Check to see if two moves are close to one another
		#wimSelect = interaction.wimCheck(ray.getPosition(viz.ABS_GLOBAL), miniWorld.getPosition(viz.ABS_GLOBAL), attached, wimSelect, ray, controller, rayEnd)
	
	if attached:
		if (mode == HOMER) & (not wimSelect):
			interaction.homerMove()
		
		if wimSelect:
			interaction.wimMove(obj[0])
			
	if state == DOCKING:
		#Check to see if object is in one another
		goodDrop = dockingTrials.inBounds(2,10)
	
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
	
	button = vetools.int2bits(int(rayData[10]))

	#Navigation Actions
	if state != DOCKING:
		if button[2]:
			view.setPosition(vizmat.MoveAlongVector(view.getPosition(viz.ABS_GLOBAL),vizmat.VectorToPoint(ray.getPosition(viz.ABS_GLOBAL),rayEnd.getPosition(viz.ABS_GLOBAL)),5*viz.elapsed()),viz.ABS_GLOBAL)
			
		if button[4] & (not button[5]):
			view.setEuler([60*viz.elapsed(),0,0],viz.VIEW_ORI,viz.REL_PARENT)
				
		if button[7] & (not button[6]):
			view.setEuler([-60*viz.elapsed(),0,0],viz.VIEW_ORI,viz.REL_PARENT)
		
	#Trigger Actions
	if button[1] != oldTriggerState:
		if button[1]:
			if (not calibration):
				#Pos Calibration
				rawRayPos = vetools.configPos(calibration,rayData[0:3],SCALING_FACTOR,calibrationPos)
				
				calibrationPos[0] = rawRayPos[0]
				calibrationPos[1] = rawRayPos[1]
				calibrationPos[2] = rawRayPos[2]
				
				calibration = True
				
				#Switch Back to Main Scene
				if state != DOCKING:
					viz.clearcolor(viz.BLACK)
					
					view.setPosition(-23.5,10.6,-23)
					view.setEuler(42.4,5,0)
				else:
					viz.clearcolor(.25,.25,.25)
		
					view.setPosition(0,7.5,-21)
					view.setEuler(0,0,0)
				
				view.setScene(viz.Scene1)
				headLight.disable()
			
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
	
	oldTriggerState = button[1]
vizact.ontimer(UPDATE_RATE,updateScene)

#Changes mode between Raycasting & HOMER
def cycleMode():
	global mode
	
	mode = not mode
	
	if mode == HOMER:
		bodyLink.setEnabled(True)
	else:
		bodyLink.setEnabled(False)
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
			
	#recalibrate
	if key == 'c':
		global calibration
	
		calibration = False
					
		#Switch Back to Calibration Scene
		view.setPosition(0,4,-8)
		view.setEuler(0,0,0)
		
		view.setScene(viz.Scene2)
		headLight.enable()
	
	#Viewpoint reset
	if key == 'r':
		view.setPosition([-23.5,10.6,-23])
		view.setEuler([42.4,5,0],viz.VIEW_ORI)
			
viz.callback(viz.KEYBOARD_EVENT,mykeyboard)

def onExit():
	print 'File Closed'
	record.close()
viz.callback(viz.EXIT_EVENT,onExit)

def rumble(strength,time):
	raySensor.command(1,'',strength)
	viz.waittime(time)
	raySensor.command(1,'',0)
	
def onCollide(e):
	global attached
	
	if (not attached):
		viz.director(rumble,75,.25)
viz.callback(viz.COLLIDE_BEGIN_EVENT, onCollide )
