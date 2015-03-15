import viz
import os
import fnmatch
import random
import math
import vizmat

import vetools

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

#Modes
RAYCASTING = 0
HOMER = 1
WIM = 2

#Global Variables
calibrationPos = [0,0,0]
oldTriggerState = 0
lastSelection = []
obj = []

#States
calibration = False
wimSelect = False
attached = False

mode = RAYCASTING

#Load Models
ray = viz.add('models/ray.obj')
hand = viz.add('models/hand.obj')
controller = viz.add('models/moveController.obj')

#View Setup
viz.MainWindow.fov(FOV, viz.AUTO_COMPUTE)

view = viz.MainView
view.setPosition(0,4,-8)
view.setEuler(0,0,0)

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

#Helpers
setup = vetools.VizardWorldSetup(viz)
interaction = vetools.InteractionTools(viz,ray,hand,virtualHand,body,objParent,posMarker,world)

#Calibration Instructions
setup.setupCalImage('calibrate.png')
view.setScene(viz.Scene2)

#Ray Setup
rayLink = viz.link(ray, objParent, enabled=True)
rayEnd.setPosition([0,0,43])

#Hand Setup
hand.visible(viz.OFF)
hand.parent(virtualHand)

#Lights Setup
headLight = view.getHeadLight()

lightL = setup.addOmniLight([-5,10,0])
lightR = setup.addOmniLight([5,10,0])

#Populate World
room = setup.addModel('models/walls.obj',parent=world)
couch = setup.addModel('models/couch.obj',[0,0,9],parent=world)
chair = setup.addModel('models/chair.obj',[-8,0,3],[-90,0,0],parent=world)
coffeeTable = setup.addModel('models/coffee_table.obj',parent=world)
tvTable = setup.addModel('models/tv_table.obj',[0,0,-9],parent=world)
tv = setup.addModel('models/tv.obj',[0,2.5,-9],[180,0,0],parent=world)
sideTable = setup.addModel('models/side_table.obj',[-8,0,9],parent=world)
lamp = setup.addModel('models/lamp.obj',[-8,2.5,9],parent=world)
cup = setup.addModel('models/cup.obj',[-1,2.02,1],parent=world)
coaster = setup.addModel('models/coaster.obj',[-1,2,1],parent=world)
coaster1 = setup.addModel('models/coaster.obj',[-7.5,2.52,8.5],parent=world)
coaster2 = setup.addModel('models/coaster.obj',[-7.5,2.54,8.5],parent=world)
coaster3 = setup.addModel('models/coaster.obj',[-7.5,2.56,8.5],parent=world)
coaster4 = setup.addModel('models/coaster.obj',[-7.5,2.58,8.5],parent=world)
coasterHolder = setup.addModel('models/coaster_holder.obj',[-7.5,2.5,8.5],parent=world)

#Links Ray to View
viewLink = viz.link(view, ray, enabled=True)
viewLink.setDstFlag(viz.LINK_POS_RAW) #Don't offset viewpoint position with eyeheight
transOperator = viewLink.preTrans([0,0,.1]) #Ray translation from camera
rotateOperator = viewLink.preEuler([0,0,0])

#Links Body to View
bodyLink = viz.link(view, body, enabled=True)
bodyLink.setDstFlag(viz.LINK_POS_RAW)
bodyLink.preTrans([0,-1.2,0])

#Setting up Ray Physics
ray.collideMesh()
ray.disable(viz.DYNAMICS)
ray.enable(viz.COLLIDE_NOTIFY)	

def updateScene():
	global calibrationPos
	global oldTriggerState
	global calibration
	global lastSelection
	global attached
	global obj
	
	data = raySensor.get()
	
	#Ray Position & Orientation Data
	transOperator.setPosition(vetools.configPos(data[0:3],calibrationPos,calibration))
	rotateOperator.setQuat(vetools.configQuat(data[3:7]))
	
	if attached & (mode == HOMER):
		interaction.homerMove()
	
	intersectedObjects = vetools.formatIntersectionResults(viz.intersect(ray.getPosition(viz.ABS_GLOBAL), rayEnd.getPosition(viz.ABS_GLOBAL), all=True),ray,room)
	
	#Highlighting Effect
	if (not attached):
		if intersectedObjects:
			[node.object.emissive([0,0,0]) for node in lastSelection]
			intersectedObjects[0].object.emissive(viz.GREEN)
			lastSelection = intersectedObjects
			
		elif lastSelection:
			[node.object.emissive([0,0,0]) for node in lastSelection]	
	
	button = vetools.int2bits(int(data[10]))

	#Navigation Actions
	if button[2]:
		#view.move([0,0,5*viz.elapsed()],viz.BODY_ORI)
		view.setPosition(vizmat.MoveAlongVector(view.getPosition(viz.ABS_GLOBAL),vizmat.VectorToPoint(ray.getPosition(viz.ABS_GLOBAL),rayEnd.getPosition(viz.ABS_GLOBAL)),5*viz.elapsed()),viz.ABS_GLOBAL)
		
	if (button[5] & (not button[4])) | (button[6] & (not button[7])):
		view.move([0,0,-5*viz.elapsed()],viz.BODY_ORI)
	
	if button[4] & button[5]:
		view.move([5*viz.elapsed(),0,0],viz.BODY_ORI)
		
	if button[6] & button[7]:
		view.move([-5*viz.elapsed(),0,0],viz.BODY_ORI)
		
	if button[4] & (not button[5]):
		view.setEuler([60*viz.elapsed(),0,0],viz.BODY_ORI,viz.REL_PARENT)
			
	if button[7] & (not button[6]):
		view.setEuler([-60*viz.elapsed(),0,0],viz.BODY_ORI,viz.REL_PARENT) 
	
	#Trigger Actions
	if button[1] != oldTriggerState:
		if button[1]:
			if (not calibration):
				#Pos Calibration
				rawRayPos = vetools.configPos(data[0:3],calibrationPos,calibration)
				
				calibrationPos[0] = rawRayPos[0]
				calibrationPos[1] = rawRayPos[1]
				calibrationPos[2] = rawRayPos[2]
				
				calibration = True
				
				#Switch Back to Main Scene
				view.setScene(viz.Scene1)
				headLight.disable()
			
			if intersectedObjects:
				if mode == RAYCASTING:
					interaction.raycastingAttach(intersectedObjects[0])
				if mode == HOMER:
					interaction.homerAttach(intersectedObjects[0])
				
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
vizact.onkeydown('c',resetCalibration)

def reset():
	#Viewpoint reset
	view.setPosition(0,4,-8)
	
	#World reset
	setup.reset(couch,[0,0,9])
	setup.reset(chair,[-8,0,3],[-90,0,0])
	setup.reset(coffeeTable)
	setup.reset(tvTable,[0,0,-9])
	setup.reset(tv,[0,2.5,-9],[180,0,0])
	setup.reset(sideTable,[-8,0,9])
	setup.reset(lamp,[-8,2.5,9])
	setup.reset(cup,[-1,2.02,1])
	setup.reset(coaster,[-1,2,1])
	setup.reset(coaster1,[-7.5,2.52,8.5])
	setup.reset(coaster2,[-7.5,2.54,8.5])
	setup.reset(coaster3,[-7.5,2.56,8.5])
	setup.reset(coaster4,[-7.5,2.58,8.5])
	setup.reset(coasterHolder,[-7.5,2.5,8.5])
vizact.onkeydown('r',reset)

def cycleMode():
	global mode
	
	#Changes mode between Raycasting, Homer, WIM
	if mode == 2:
		mode = 0
	else:
		mode = mode + 1
vizact.onkeydown(viz.KEY_F1,cycleMode)

def rumble(strength,time):
	raySensor.command(1,'',strength)
	viz.waittime(time)
	raySensor.command(1,'',0)

def onCollide(e):
	global attached
	
	if (not attached):
		viz.director(rumble,75,.25)

viz.callback(viz.COLLIDE_BEGIN_EVENT, onCollide )
