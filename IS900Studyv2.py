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
SCALING_FACTOR = 1

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

#Connect to IS900 Sensors
headSensor = viz.add('intersense.dls')
raySensor = viz.add('intersense.dls')
wimSensor = viz.add('intersense.dls')

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

#Head Tracking Specific Groups
head = viz.addGroup()

#Helper Classes
setup = vetools.VizardWorldSetup(viz)
interaction = vetools.InteractionTools(viz,ray,hand,virtualHand,body,objParent,posMarker,miniObjParent,world)
room = trialtools.generateRoom(viz,world,head)
dockingTrials = trialtools.generateTrials(viz,world,view,MAX_TRIALS)

#Ray Setup
rayLink = viz.link(ray, objParent, enabled=True)
rayEnd.setPosition([0,0,43])

#Hand Setup
hand.visible(viz.OFF)
hand.parent(virtualHand)

#WIM Setup
world.duplicate(viz.Scene1,parent=miniWorld)
miniWorld.setScale([.025,.025,.025])
miniWorld.visible(viz.OFF)

controller.setScale([.5,.5,.5])
controller.visible(viz.OFF)

#Lights Setup
headLight = view.getHeadLight()
headLight.disable()
room.addLights()

#Links Ray to View
viewLink = viz.link(view, ray, enabled=True)
viewLink.setDstFlag(viz.LINK_POS_RAW) #Don't offset viewpoint position with eyeheight
transOperator = viewLink.preTrans([0,0,.1]) #Ray translation from camera
rotateOperator = viewLink.preEuler([0,0,0])

#Links View to Head
headTrackingLink = viz.link(head, view, enabled=True)
headTrans = headTrackingLink.preTrans([0,0,.1])
headRot = headTrackingLink.preEuler([0,0,0])
headRotPost = headTrackingLink.postEuler([0,0,0])

#Links Body to View
bodyLink = viz.link(view, body, enabled=False)
bodyLink.setDstFlag(viz.LINK_POS_RAW)
bodyLink.preTrans([0,-1.2,0])

#Links MiniWorld to View
wimLink = viz.link(view, miniWorld, enabled=True)
wimLink.setDstFlag(viz.LINK_POS_RAW)
wimTrans = wimLink.preTrans([0,0,.1])
wimRot = wimLink.preEuler([0,0,0])

#Setting up Ray Physics
ray.collideMesh()
ray.disable(viz.DYNAMICS)
ray.enable(viz.COLLIDE_NOTIFY)	

#Initialize Head Tracking Data
head.setPosition([0,0,5],viz.ABS_GLOBAL)

#Prompt Tester for Participant Info
participant_id = viz.input( 'Please enter the participant number', str(0) )
while participant_id == 0:
	participant_id = viz.input( 'Please enter the participant number', str(0) )
	
blockNumber = viz.input( 'Please enter current block number 1-3', str(0) )
while blockNumber != 1 and  blockNumber != 2 and blockNumber != 3:
	blockNumber = viz.input( 'Please enter current block number 1-3', str(0) )

#Determines what the technique and the order based on participant number
mode,systemOrder = trialtools.systemOrder(participant_id)
dockingTrials.chooseMatchSet(1,systemOrder)

#Set technique for trial
if mode == HOMER:
	bodyLink.setEnabled(True)
elif mode == WIM:
	wimTrackingLink.setEnabled(True)
	wimEnabled = True
	wimSelect = True

	miniWorld.visible(viz.ON)
	controller.visible(viz.ON)
	ray.visible(viz.OFF)
	rayEnd.setPosition([0,0,.40])
	
#Jump to test section
if (blockNumber == PRACTICE):
	room.load()
elif (blockNumber == DOCKING):
	dockingTrials.startTrials()
elif (blockNumber == CAPSTONE):
	room.load()
	
state = blockNumber

localtime = time.localtime(time.time())
data = open('Trials/'+'ID '+str(participant_id)+' '+str(localtime[1])+'.'+str(localtime[2])+'.'+str(localtime[0])+' '+str(localtime[3])+str(localtime[4])+str(localtime[5])+'.txt', 'w')

#Set up default view and background color
viz.clearcolor(viz.BLACK)

view.setPosition(0,4,-8)
view.setEuler(0,0,0)

#Transformation Groups
group1 = viz.addGroup()
group2 = viz.addGroup()

def updateScene():
	global calibrationPos
	global oldTriggerState
	global calibration
	global lastSelection
	global attached
	global obj
	global wimSelect
	
	global state
	global timer
	global start
	
	rayData = raySensor.get()
	#wimData = wimSensor.get()
	
	#Update View based on Head Tracking
	headTrans.setPosition(vetools.configPos(calibration,headSensor.getPosition(),SCALING_FACTOR))
	#headTrans.setPosition(headSensor.getPosition())
	headRot.setQuat(headSensor.getQuat())
	
	#Ray Position & Orientation Data
	#rayTrans.setPosition(vetools.configPos(calibration,raySensor.getPosition(),SCALING_FACTOR))
	#rayRot.setQuat(raySensor.getQuat())
	
	group1.setParent(world)
	group2.setParent(world)
	
	group1.setMatrix(raySensor.getMatrix(viz.ABS_GLOBAL),viz.ABS_GLOBAL)
	group2.setMatrix(headSensor.getMatrix(viz.ABS_GLOBAL),viz.ABS_GLOBAL)
	
	X11 = group1.getMatrix(viz.ABS_GLOBAL)
	
	group1.setParent(group2)
	group1.setMatrix(X11,viz.ABS_GLOBAL)
	
	transOperator.setPosition(vetools.configPos(calibration,group1.getPosition(),SCALING_FACTOR))
	rotateOperator.setQuat(group1.getQuat())
	
	if wimEnabled:
		#WIM Position & Orientation Data
		wimTrans.setPosition(vetools.configPos(calibration,wimSensor.getPosition(),SCALING_FACTOR))
		wimRot.setQuat(wimSensor.getQuat())
		
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
			
	button = vetools.int2bits(int(rayData[7]))
	
	#Navigation Actions
	if state != DOCKING:
		if rayData[9] > 0.5:
			head.setPosition(vizmat.MoveAlongVector(head.getPosition(viz.ABS_GLOBAL),vizmat.VectorToPoint(ray.getPosition(viz.ABS_GLOBAL),rayEnd.getPosition(viz.ABS_GLOBAL)),50*viz.elapsed()),viz.ABS_GLOBAL)
		if rayData[8] > 0.8:
			head.setEuler([60*viz.elapsed(),0,0],viz.REL_PARENT)
		if rayData[8] < -0.8:
			head.setEuler([-60*viz.elapsed(),0,0],viz.REL_PARENT)
		
	#Trigger Actions
	if button[5] != oldTriggerState:
		if button[5]:
			if intersectedObjects:
				if wimEnabled:
					if wimSelect:
						interaction.wimAttach(intersectedObjects[0])
						print 'wim'
						if state == DOCKING:
							data.write('WIM Drop - ' + time.asctime(time.localtime(time.time()))+'\n')
				else:
					if mode == RAYCASTING:
						interaction.raycastingAttach(intersectedObjects[0])
						print 'raycasting'
						if state == DOCKING:
							data.write('Raycasting Drop - '+ time.asctime(time.localtime(time.time()))+'\n')
					elif mode == HOMER:
						interaction.homerAttach(intersectedObjects[0])
						print 'homer'
						if state == DOCKING:
							data.write('HOMER Drop - ' + time.asctime(time.localtime(time.time()))+'\n')
							
				#State variables
				obj = intersectedObjects
				attached = True
				
				if state == DOCKING:
					if not start:
						timer = time.time()
						start = True
		
		elif not button[5]:
			if obj:
				interaction.release(mode,obj[0])
				
				#State variables
				attached = False
				obj = []
				
				if state == DOCKING:
					if goodDrop:
						print 'Final:',(time.time() - timer)
						data.write('Trial '+str(dockingTrials.getTrial()+1)+' Time: '+ str((time.time() - timer))+'\n'+'\n')
						
						start = False
						dockingTrials.nextTrial()
	
	oldTriggerState = button[5]
vizact.ontimer(UPDATE_RATE,updateScene)

def onSensorDown(e):
    if e.object is tracker:
        print 'Button',e.button,'down'
viz.callback(viz.SENSOR_DOWN_EVENT,onSensorDown)

def onSensorUp(e):
    if e.object is tracker:
        print 'Button',e.button,'up'
viz.callback(viz.SENSOR_UP_EVENT,onSensorUp)

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
		global finalTimer
		global finalStart
		
		if not finalStart:
			print 'start timer'
			data.write('Capstone Start Time: '+time.asctime(time.localtime(time.time()))+'\n')
			finalTimer = time.time()
			finalStart = True
		else:
			print 'end timer'
			print 'Capstone Time:',(time.time() - finalTimer)
			data.write('Capstone Time: '+ str((time.time() - finalTimer))+'\n'+'\n')
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
		global timer
		
		print 'Final:',(time.time() - timer)
		data.write('Skipped Trial '+str(dockingTrials.getTrial()+1)+' Time: '+ str((time.time() - timer))+'\n'+'\n')
		
		start = False
		dockingTrials.nextTrial()
	
	#Viewpoint reset
	if key == 'r':
		view.setPosition([-23.5,10.6,-23])
		view.setEuler([42.4,5,0],viz.VIEW_ORI)
			
viz.callback(viz.KEYBOARD_EVENT,mykeyboard)

def onExit():
	print 'File Closed'
	data.close()
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
