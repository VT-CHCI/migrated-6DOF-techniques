import viz
import os
import fnmatch
import random
import math
import vizmat
import vetools

import kinect
import time

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

#Load Models
ray = viz.add('models/kinectRay.obj')
hand = viz.add('models/hand.obj')

#View Setup
viz.MainWindow.fov(FOV, viz.AUTO_COMPUTE)

view = viz.MainView
view.setPosition(0,4,-8)
view.setEuler(0,0,0)

#Connect to a Move Sensor
sensor = viz.add('KinectSensor.dls')

#Declare Groups
world = viz.addGroup()
objParent = viz.addGroup(parent=world)
rayEnd = viz.addGroup(parent=ray)
virtualHand = viz.addGroup(parent=world)

#World Setup Helper
setup = vetools.VizardWorldSetup(viz)

#Ray Setup
rayLink = viz.link(ray, objParent, enabled=True)
rayEnd.setPosition([0,0,43])

#Hand Setup
#hand.visible(viz.OFF)
#hand.parent(virtualHand)

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

#Setting up Ray Physics
ray.collideMesh()
ray.disable(viz.DYNAMICS)
ray.enable(viz.COLLIDE_NOTIFY)	
#ray.visible(viz.OFF)

#Setting up Skeleton Helper
skeleton = kinect.skeleton(sensor.get())

def endSession():
	sensor.command(9)
	time.sleep(2)
	viz.quit()
vizact.onkeydown(viz.KEY_ESCAPE, endSession)

def scaleData(pos):
	pos[0] = pos[0]*7.25
	pos[1] = pos[1]*7.25
	pos[2] = -pos[2]
	
	return pos
	
def midpoint(pt1, pt2):
	distance = vizmat.Distance(pt1,pt2)
	vector = vizmat.VectorToPoint(pt1,pt2)
	
	finalPos = vizmat.MoveAlongVector(pt1,vector,distance/2)
	
	return finalPos
	
def unmirror(vector):
	yFlip = vizmat.ReflectionVector(vector,[0,1,0])
	xFlip = vizmat.ReflectionVector(yFlip,[1,0,0])
	
	return xFlip
	
def add(a,b):
	sum = [a + b for a, b in zip(a,b)]
	
	return sum

def updateScene():
	skeleton.update(sensor.get())
	
	view.setPosition(scaleData(skeleton.HEAD[0:3]),viz.ABS_GLOBAL)
	hand.setPosition(scaleData(skeleton.HAND_RIGHT[0:3]),viz.ABS_GLOBAL)
	
	'''
	armVector = vizmat.VectorToPoint(skeleton.ELBOW_RIGHT[0:3],skeleton.HAND_RIGHT[0:3])
	rayVector = vizmat.ReflectionVector(armVector,[0,1,0])
	rayVector = vizmat.ReflectionVector(rayVector,[1,0,0])
	
	tempQuat = vizmat.LookToQuat(rayVector)
	
	rotateOperator.setQuat(tempQuat)
	transOperator.setPosition([0,0,5])
	'''
	
	hands = midpoint(skeleton.HAND_LEFT[0:3],skeleton.HAND_RIGHT[0:3])
	elbows = midpoint(skeleton.ELBOW_LEFT[0:3],skeleton.ELBOW_RIGHT[0:3])
	
	rayVector = unmirror(vizmat.VectorToPoint(elbows,hands))
	
	rotateOperator.setQuat(vizmat.LookToQuat(rayVector))
	transOperator.setPosition(hands,viz.ABS_GLOBAL)
	
	print 'view', view.getPosition(viz.ABS_GLOBAL)
	print 'hands', scaleData(hands)
	
	#print skeleton.ID
	
vizact.ontimer(UPDATE_RATE,updateScene)