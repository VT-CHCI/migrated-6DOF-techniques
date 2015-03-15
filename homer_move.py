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
scalingFactor = 0.0

#Load Models
ray = viz.add('models/ray.obj')
hand = viz.add('models/hand.obj')

#View Setup
viz.MainWindow.fov(FOV, viz.AUTO_COMPUTE)

view = viz.MainView
view.setPosition(0,4,-8)
view.setEuler(0,0,0)

#Connect to a Move Sensor
sensor = viz.add('MoveSensor.dls')

#Declare Groups
world = viz.addGroup()
body = viz.addGroup()
objParent = viz.addGroup(parent=world)
rayEnd = viz.addGroup(parent=ray)
virtualHand = viz.addGroup(parent=world)

posMarker = viz.addGroup(parent=body)

#World Setup Helper
setup = vetools.VizardWorldSetup(viz)

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
'''
room = setup.addModel('models/walls.obj',physics=False,parent=world)
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
'''
room = setup.addModel('textenmodels/walls.obj',physics=False,parent=world)
couch = setup.addModel('textenmodels/couch.obj',[0,0,9],parent=world)
chair = setup.addModel('textenmodels/chair.obj',[-8,0,3],[-90,0,0],parent=world)
coffeeTable = setup.addModel('textenmodels/coffee_table.obj',parent=world)
tvTable = setup.addModel('textenmodels/tv_table.obj',[0,0,-9],parent=world)
tv = setup.addModel('textenmodels/tv.obj',[0,2.5,-9],[180,0,0],parent=world)
sideTable = setup.addModel('textenmodels/side_table.obj',[-8,0,9],parent=world)
lamp = setup.addModel('textenmodels/lamp.obj',[-8,2.5,9],parent=world)
cup = setup.addModel('textenmodels/cup.obj',[-1,2.02,1],parent=world)
coaster = setup.addModel('textenmodels/coaster.obj',[-1,2,1],parent=world)
coaster1 = setup.addModel('textenmodels/coaster.obj',[-7.5,2.52,8.5],parent=world)
coaster2 = setup.addModel('textenmodels/coaster.obj',[-7.5,2.54,8.5],parent=world)
coaster3 = setup.addModel('textenmodels/coaster.obj',[-7.5,2.56,8.5],parent=world)
coaster4 = setup.addModel('textenmodels/coaster.obj',[-7.5,2.58,8.5],parent=world)
coasterHolder = setup.addModel('textenmodels/coaster_holder.obj',[-7.5,2.5,8.5],parent=world)

#Texture objects
couch_texture = viz.addTexture('images/couch.jpg')
tile = viz.addTexture('images/tile.jpg')
glass = viz.addTexture('images/glass.jpg')
wood = viz.addTexture('images/wood.jpg')
tv_texture = viz.addTexture('images/tv_screen.png')

room.texture(tile)
couch.texture(couch_texture)
chair.texture(couch_texture)
coffeeTable.texture(wood)
tvTable.texture(wood)
tv.texture(tv_texture)
sideTable.texture(wood)
lamp.texture(glass)
cup.texture(glass)
coaster.texture(tile)
coaster1.texture(tile)
coaster2.texture(tile)
coaster3.texture(tile)
coaster4.texture(tile)
coasterHolder.texture(tile)

#Links Ray to View
viewLink = viz.link(view, ray, enabled=True)
viewLink.setDstFlag(viz.LINK_POS_RAW) #Don't offset viewpoint position with eyeheight
transOperator = viewLink.preTrans([0,0,.1]) #Ray translation from camera
rotateOperator = viewLink.preEuler([0,0,0])

bodyLink = viz.link(view, body, enabled=True)
bodyLink.setDstFlag(viz.LINK_POS_RAW)
bodyLink.preTrans([0,-1.2,0])

#Setting up Ray Physics
ray.collideMesh()
ray.disable(viz.DYNAMICS)
ray.enable(viz.COLLIDE_NOTIFY)

def formatIntersectResults(rawList):
	formatedList = []
	temp = []
	
	global ray
	global room
	
	for elem in rawList:
		if ((elem.object != ray) and (elem.object != room) and (not temp.count(elem.object))):
			formatedList.append(elem)
			temp.append(elem.object)
	
	return formatedList
	
def scalingFactor(userPos,movePos,objPos):
	global scalingFactor
	
	return scalingFactor
	
def subtract(a,b):
	difference = [a - b for a, b in zip(a,b)]
	
	return difference

def updateScene():
	global calibrationPos
	global oldTriggerState
	global obj
	global calibration
	global lastSelection
	global attached
	global scalingFactor
	global objDistance
	global XMoveInit
	
	data = sensor.get()
	
	#Ray Position & Orientation Data
	transOperator.setPosition(vetools.configPos(data[0:3],calibrationPos,calibration))
	rotateOperator.setQuat(vetools.configQuat(data[3:7]))
	
	if attached:
		#Homer Rotation
		XMoveCurrent = objParent.getMatrix(viz.ABS_GLOBAL)
		XMoveCurrent.preMult(XMoveInit.inverse())
		
		virtualHand.setQuat(XMoveCurrent.getQuat(),viz.ABS_GLOBAL)
		
		#Homer Position
		objDistance = scalingFactor * vizmat.Distance(body.getPosition(viz.ABS_GLOBAL),ray.getPosition(viz.ABS_GLOBAL))
		
		body.lookat(ray.getPosition(viz.ABS_GLOBAL),viz.ABS_GLOBAL)
		tempVector = vizmat.VectorToPoint(body.getPosition(viz.ABS_GLOBAL),posMarker.getPosition(viz.ABS_GLOBAL))
		virtualHandPos = vizmat.MoveAlongVector(body.getPosition(viz.ABS_GLOBAL),tempVector,objDistance)
		
		virtualHand.setPosition(virtualHandPos,viz.ABS_GLOBAL)

	intersectedObjects = formatIntersectResults(viz.intersect(ray.getPosition(viz.ABS_GLOBAL), rayEnd.getPosition(viz.ABS_GLOBAL), all=True))
	
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
		X1 = vizmat.Transform()
		
		if button[1]:
			
			if (not calibration):
				#Calibration Position
				rawRayPos = vetools.configPos(data[0:3],calibrationPos,calibration)
				
				calibrationPos[0] = rawRayPos[0]
				calibrationPos[1] = rawRayPos[1]
				calibrationPos[2] = rawRayPos[2]
				
				calibration = True
				
				#Switch Back to Main Scene
				view.setScene(viz.Scene1)
				headLight.disable()
			
			if intersectedObjects:
				#Set Matrices
				XMoveInit = objParent.getMatrix(viz.ABS_GLOBAL)
				X1 = intersectedObjects[0].object.getMatrix(viz.ABS_GLOBAL)
				
				#Add object to virtual hand
				virtualHand.setPosition(intersectedObjects[0].point)
				virtualHand.setQuat([0,0,0,1],viz.ABS_GLOBAL)
				intersectedObjects[0].object.parent(virtualHand)
				intersectedObjects[0].object.setMatrix(X1,viz.ABS_GLOBAL)
				
				#Replace move controller with virtual hand at intersection point with proper rotation
				hand.visible(viz.ON)
				hand.setQuat(ray.getQuat(viz.ABS_GLOBAL),viz.ABS_GLOBAL)
				ray.visible(viz.OFF)
				
				#Calculate scaling Factor
				objDistance = vizmat.Distance(body.getPosition(viz.ABS_GLOBAL),virtualHand.getPosition(viz.ABS_GLOBAL))
				handDistance = vizmat.Distance(body.getPosition(viz.ABS_GLOBAL),ray.getPosition(viz.ABS_GLOBAL))
				
				if handDistance == 0.0 or handDistance < 0.0:
					handDistance = .001
					
				scalingFactor = objDistance/handDistance
				
				#Setup marker to calculate HOMER movements
				body.lookat(ray.getPosition(viz.ABS_GLOBAL),viz.ABS_GLOBAL)
				posMarker.setPosition(virtualHand.getPosition(viz.ABS_GLOBAL),viz.ABS_GLOBAL)

				#State variables
				obj = intersectedObjects
				attached = True
		
		elif not button[1]:
			if obj:
				X1 = obj[0].object.getMatrix(viz.ABS_GLOBAL)
				
				obj[0].object.parent(world)
				obj[0].object.setMatrix(X1,viz.ABS_GLOBAL)
				
				hand.visible(viz.OFF)
				ray.visible(viz.ON)
				attached = False
			
				obj = []
	
	oldTriggerState = button[1]
vizact.ontimer(UPDATE_RATE,updateScene)

def rumble(strength,time):
	sensor.command(1,'',strength)
	viz.waittime(time)
	sensor.command(1,'',0)

def onCollide(e):
	global attached
	
	if (not attached):
		viz.director(rumble,75,.25)

viz.callback(viz.COLLIDE_BEGIN_EVENT, onCollide )
