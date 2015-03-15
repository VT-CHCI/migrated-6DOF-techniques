import viz
import os
import fnmatch
import random
import math
import vizmat
import time

#My Modules
import vetools
import kinecttools
import trialtools

'''
viz.go(viz.FULLSCREEN,viz.STEREO)
viz.MainWindow.stereo(viz.STEREO_HORZ)
viz.MainWindow.ipd(.06)
viz.viewdist(1)
'''

viz.go()
viz.phys.enable()

#Constants
CAMERA_TV_DISTANCE = 9/12
TV_HEIGHT = 20.75/12
UPDATE_RATE = 0
FOV = 60
SCALING_FACTOR = .01

#Modes
RAYCASTING = 0
HOMER = 1

#Global Variables
calibrationPos = [0,0,0]
oldTriggerState = 0
lastSelection = []
obj = []

#States
calibration = False
wimSelect = False
attached = False
wimEnabled = False
headTrackingEnabled = False

mode = RAYCASTING

#Load Models
ray = viz.add('models/ray-long.obj')
hand = viz.add('models/hand.obj')
controller = viz.add('models/moveController.obj')

hand.setScale(10,10,10)

#View Setup
viz.MainWindow.fov(FOV, viz.AUTO_COMPUTE)

view = viz.MainView
view.setPosition(0,4,-8)
view.setEuler(0,0,0)

#Connect to Move Sensors
raySensor = viz.add('MoveSensor.dls')
wimSensor = viz.add('MoveSensor.dls')
#kinectSensor = viz.add('KinectSensor.dls')
kinect = False

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

#Helpers
setup = vetools.VizardWorldSetup(viz)
interaction = vetools.InteractionTools(viz,ray,hand,virtualHand,body,objParent,posMarker,miniObjParent,world)
room = trialtools.generateRoom(viz,world,view,head)

#Calibration Instructions
setup.setupCalImage('calibrate.png')
view.setScene(viz.Scene2)

#Ray Setup
rayLink = viz.link(ray, objParent, enabled=True)
rayEnd.setPosition([0,0,700])

#Hand Setup
hand.visible(viz.OFF)
hand.parent(virtualHand)

#WIM Setup
world.duplicate(viz.Scene1,parent=miniWorld)
miniWorld.setScale([.01,.01,.01])
miniWorld.visible(viz.OFF)

controller.setScale([.25,.25,.25])
controller.visible(viz.OFF)

#Lights Setup
headLight = view.getHeadLight()

room.addLights()
room.load()

#Links Ray to View
viewLink = viz.link(view, ray, enabled=True)
viewLink.setDstFlag(viz.LINK_POS_RAW) #Don't offset viewpoint position with eyeheight
transOperator = viewLink.preTrans([0,0,.1]) #Ray translation from camera
rotateOperator = viewLink.preEuler([0,0,0])

#Links View to Head
headTrackingLink = viz.link(head, view, enabled=True)
headTrans = headTrackingLink.preTrans([0,0,.1])
headRot = headTrackingLink.preEuler([0,0,0])

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

#Initialize Head Tracking Data
head.setPosition([0,4,-8],viz.ABS_GLOBAL)
view.setEuler([0,0,0],viz.VIEW_ORI)
head.setEuler([0,0,0])

if kinect:
	skeleton = kinecttools.skeleton(kinectSensor.get())

def updateScene():
	global calibrationPos
	global oldTriggerState
	global calibration
	global lastSelection
	global attached
	global obj
	global wimSelect
	
	rayData = raySensor.get()
	wimData = wimSensor.get()

	if headTrackingEnabled:
		#Set headposition
		skeleton.update(kinectSensor.get())
		headTrans.setPosition(kinecttools.scaleData(skeleton.HEAD[0:3]))
		
	#Ray Position & Orientation Data
	transOperator.setPosition(vetools.configPos(calibration,rayData[0:3],SCALING_FACTOR,calibrationPos))
	rotateOperator.setQuat(vetools.configQuat(rayData[3:7]))
	
	if wimEnabled:
		#WIM Position & Orientation Data
		wimTransOperator.setPosition(vetools.configPos(calibration,wimData[0:3],SCALING_FACTOR,calibrationPos,[0,3,0]))
		wimRotateOperator.setQuat(vetools.configQuat(wimData[3:7],[0,90,0]))
			
		#Set Controller Model Position & Orientation Data
		controller.setPosition(ray.getPosition())
		controller.setQuat(ray.getQuat())
			
	if attached:
		if (mode == HOMER) & (not wimSelect):
			interaction.homerMove()
			
		if wimSelect:
			interaction.wimMove(obj[0])

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
	
	if button[2]:
		head.setPosition(vizmat.MoveAlongVector(head.getPosition(viz.ABS_GLOBAL),vizmat.VectorToPoint(ray.getPosition(viz.ABS_GLOBAL),rayEnd.getPosition(viz.ABS_GLOBAL)),50*viz.elapsed()),viz.ABS_GLOBAL)
		
	if button[4] & (not button[5]):
		view.setEuler([60*viz.elapsed(),0,0],viz.BODY_ORI,viz.REL_PARENT)
			
	if button[7] & (not button[6]):
		view.setEuler([-60*viz.elapsed(),0,0],viz.BODY_ORI,viz.REL_PARENT)
	
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
		
		elif not button[1]:
			if obj:
				interaction.release(mode,obj[0])
				
				#State variables
				attached = False
				obj = []
	
	oldTriggerState = button[1]
vizact.ontimer(UPDATE_RATE,updateScene)

def resetCalibration():
	global calibration
	
	calibration = False
				
	#Switch Back to Calibration Scene
	view.setScene(viz.Scene2)
	headLight.enable()
	head.setPosition(0,4,-8)
	view.setEuler([0,0,0],viz.VIEW_ORI)
	head.setEuler([0,0,0])
vizact.onkeydown('c',resetCalibration)

def reset():
	#Viewpoint reset
	head.setPosition(0,4,-8)
	view.setEuler([0,0,0],viz.VIEW_ORI)
	head.setEuler([0,0,0])
	
	#World reset
	room.remove()
	room.load()
	
vizact.onkeydown('r',reset)


#Changes mode between Raycasting & HOMER
def cycleMode():
	global mode
	
	mode = not mode
	
	if mode == HOMER:
		bodyLink.setEnabled(True)
	else:
		bodyLink.setEnabled(False)
vizact.onkeydown('m',cycleMode)

#Allows WIM to be ON or OFF
def cycleWIM():
	global wimEnabled
	global wimSelect

	wimEnabled = not wimEnabled

	if wimEnabled:
		wimLink.setEnabled(True)
		miniWorld.visible(viz.ON)
		
		controller.visible(viz.ON)
		ray.visible(viz.OFF)
		rayEnd.setPosition([0,0,0.5])
		
		wimSelect = True
	else:
		wimLink.setEnabled(False)
		miniWorld.visible(viz.OFF)
		
		controller.visible(viz.OFF)
		ray.visible(viz.ON)
		rayEnd.setPosition([0,0,700])
		
		wimSelect = False
vizact.onkeydown('w',cycleWIM)

#Allows Head Tracking with Kinect ON or OFF
def cycleHeadTracking():
	global headTrackingEnabled
	
	headTrackingEnabled = not headTrackingEnabled
	
	if headTrackingEnabled:
		head.setPosition(vetools.subtract(view.getPosition(viz.ABS_GLOBAL),kinect.scaleData(skeleton.HEAD[0:3])),viz.ABS_GLOBAL)
	else:
		head.setPosition(vetools.add(view.getPosition(viz.ABS_GLOBAL),kinect.scaleData(skeleton.HEAD[0:3])),viz.ABS_GLOBAL)
vizact.onkeydown('h',cycleHeadTracking)		
	
def endSession():
	kinectSensor.command(9)
	time.sleep(2)
	viz.quit()
vizact.onkeydown('q', endSession)

def rumble(strength,time):
	raySensor.command(1,'',strength)
	viz.waittime(time)
	raySensor.command(1,'',0)
	
def changeHue():
	raySensor.command(2,"250")
vizact.onkeydown('y', changeHue)

def onCollide(e):
	global attached
	
	if (not attached):
		viz.director(rumble,75,.25)

viz.callback(viz.COLLIDE_BEGIN_EVENT, onCollide )
