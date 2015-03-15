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
UPDATE_RATE = 0
TV_HEIGHT = 20.75/12
CAMERA_TV_DISTANCE = 9/12
FOV = 60

#Global Variables
oldTriggerState = 0
obj = []
calibration = False
calibrationPos = [0,0,0]
lastSelection = []
attached = False

#Load Models
ray = viz.add('models/moveController.obj')
rayLine = viz.add('models/pointer.obj')
hand = viz.add('models/hand.obj')

#View Setup
viz.MainWindow.fov(FOV, viz.AUTO_COMPUTE)

view = viz.MainView
view.setPosition(0,4,-8)
view.setEuler(0,0,0)

#Connect to a Move Sensor
raySensor = viz.add('MoveSensor.dls')
wimSensor = viz.add('MoveSensor.dls')

#Declare Groups
world = viz.addGroup()
objParent = viz.addGroup(parent=world)
rayEnd = viz.addGroup(parent=ray)
virtualHand = viz.addGroup(parent=world)

miniWorld = viz.addGroup()
world.duplicate(viz.Scene1,parent=miniWorld)
miniWorld.setScale([.05,.05,.05])

#World Setup Helper
setup = vetools.VizardWorldSetup(viz)

#Calibration Instructions
setup.setupCalImage('calibrate.png')
view.setScene(viz.Scene2)

#Ray Setup
rayLink = viz.link(ray, objParent, enabled=True)
rayEnd.setPosition([0,0,43])

viz.link(ray, rayLine, enabled=True)

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

wimLink = viz.link(view, miniWorld, enabled=True)
wimLink.setDstFlag(viz.LINK_POS_RAW)
wimTransOperator = wimLink.preTrans([0,0,.1])
wimRotateOperator = wimLink.preEuler([0,0,0])

#Setting up Ray Physics
ray.collideMesh()
ray.disable(viz.DYNAMICS)
ray.enable(viz.COLLIDE_NOTIFY)

rayLine.collideMesh()
rayLine.disable(viz.DYNAMICS)
rayLine.enable(viz.COLLIDE_NOTIFY)

#Temporary
text_2D = viz.addText( 'In Proximity', viz.SCREEN )
count = 0

def formatIntersectResults(rawList):
	formatedList = []
	temp = []
	
	global ray
	global room
	
	for elem in rawList:
		if ((elem.object != ray) and (elem.object != room) and (elem.object != rayLine) and (not temp.count(elem.object))):
			formatedList.append(elem)
			temp.append(elem.object)
	
	return formatedList
	
def configQuat(dataQuat):
	quat = [-dataQuat[0],-dataQuat[1],dataQuat[2],dataQuat[3]] #use if model is facing forward in blender
	
	return quat
	
def configPos(dataPos,calPos,calibrated,offset=[0,0,0]):
	pos = [point*0.0032808399 for point in dataPos] #scaling factor
	
	if calibrated:
		pos = [pos - calPos for pos,calPos in zip(pos,calPos)]
		pos[2] = -pos[2]
		pos = [pos + offset for pos,offset in zip(pos,offset)]
		
	return pos
	
def checkDist(pt1,pt2):
	moveDist = vizmat.Distance(pt1,pt2)
	
	if moveDist < 1.25:
		text_2D.color(viz.GREEN)
		
		rayLine.visible(viz.OFF)
		rayLine.disable(viz.COLLIDE_NOTIFY)
		
		ray.setScale([.5,.5,.5])
		rayEnd.setPosition([0,0,.5])
		
	else:
		text_2D.color(viz.RED)

		rayLine.visible(viz.ON)
		rayLine.enable(viz.COLLIDE_NOTIFY)

		ray.setScale([1,1,1])
		rayEnd.setPosition([0,0,43])
		
	return

def updateScene():
	global calibrationPos
	global oldTriggerState
	global obj
	global calibration
	global lastSelection
	global attached
	
	global count
	
	data = raySensor.get()
	data2 = wimSensor.get()
	
	#Ray Position & Orientation Data
	transOperator.setPosition(configPos(data[0:3],calibrationPos,calibration))
	rotateOperator.setQuat(configQuat(data[3:7]))
	
	#WIM Position & Orientation Data
	wimTransOperator.setPosition(configPos(data2[0:3],calibrationPos,calibration,[0,.5,.5]))
	wimRotateOperator.setQuat(configQuat(data2[3:7]))
	
	checkDist(ray.getPosition(viz.ABS_GLOBAL),miniWorld.getPosition(viz.ABS_GLOBAL))
	
	intersectedObjects = formatIntersectResults(viz.intersect(ray.getPosition(viz.ABS_GLOBAL), rayEnd.getPosition(viz.ABS_GLOBAL), all=True))
	
	#Highlighting Effect
	if (not attached):
		if intersectedObjects:
			[node.object.emissive([0,0,0]) for node in lastSelection]
			intersectedObjects[0].object.emissive(viz.GREEN)
			
			if lastSelection and (intersectedObjects[0].object != lastSelection[0].object) and (lastSelection[0].object.getEmissive() != viz.GREEN):
				if (intersectedObjects[0].object == lastSelection[0].object) and (lastSelection[0].object.getEmissive() != viz.GREEN):
					print 'new',intersectedObjects[0].object,count
					count = count + 1	
					
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
		X1 = vizmat.Transform()
		
		if button[1]:
			if (not calibration):
				#Pos Calibration
				rawRayPos = configPos(data[0:3],calibrationPos,calibration)
				
				calibrationPos[0] = rawRayPos[0]
				calibrationPos[1] = rawRayPos[1]
				calibrationPos[2] = rawRayPos[2]
				
				calibration = True
				
				#Switch Back to Main Scene
				view.setScene(viz.Scene1)
				headLight.disable()
			
			if intersectedObjects:
				X1 = intersectedObjects[0].object.getMatrix(viz.ABS_GLOBAL)
				
				#Attach
				intersectedObjects[0].object.parent(objParent)
				intersectedObjects[0].object.setMatrix(X1,viz.ABS_GLOBAL)
				attached = True
				
				obj = intersectedObjects
		
		elif not button[1]:
			if obj:
				X1 = obj[0].object.getMatrix(viz.ABS_GLOBAL)
			
				#Release
				obj[0].object.parent(world)
				obj[0].object.setMatrix(X1,viz.ABS_GLOBAL)
				attached = False
			
				obj = []
	
	oldTriggerState = button[1]
vizact.ontimer(UPDATE_RATE,updateScene)

def rumble(strength,time):
	raySensor.command(1,'',strength)
	viz.waittime(time)
	raySensor.command(1,'',0)

def onCollide(e):
	global attached

	if (e.obj2 != ray) and (e.obj2 != rayLine) and (not attached):
		viz.director(rumble,75,.25)

viz.callback(viz.COLLIDE_BEGIN_EVENT, onCollide )