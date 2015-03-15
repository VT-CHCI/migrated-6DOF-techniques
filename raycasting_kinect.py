import viz
import os
import fnmatch
import random
import math
import vizmat

import vetools
import kinect

import time

#Voice Includes
from win32com.client import constants
import win32com.client
import pythoncom

VOICE_ACTIONS = { "pickup" : 0
				,"drop" : 1
				,"move" : 2
				,"turn right" : 3
				,"turn left" : 4
				,"stop now" : 5 }
				
class SpeechRecognition:
	""" Initialize the speech recognition with the passed in list of words """
	def __init__(self, wordsToAdd):
		# For speech recognition - first create a listener
		self.listener = win32com.client.Dispatch("SAPI.SpSharedRecognizer")
		# Then a recognition context
		self.context = self.listener.CreateRecoContext()
		# which has an associated grammar
		self.grammar = self.context.CreateGrammar()
		# Do not allow free word recognition - only command and control
		# recognizing the words in the grammar only
		self.grammar.DictationSetState(0)
		# Create a new rule for the grammar, that is top level (so it begins
		# a recognition) and dynamic (ie we can change it at runtime)
		self.wordsRule = self.grammar.Rules.Add("wordsRule", constants.SRATopLevel + constants.SRADynamic, 0)
		# Clear the rule (not necessary first time, but if we're changing it
		# dynamically then it's useful)
		self.wordsRule.Clear()
		# And go through the list of words, adding each to the rule
		[ self.wordsRule.InitialState.AddWordTransition(None, word) for word in wordsToAdd ]
		# Set the wordsRule to be active
		self.grammar.Rules.Commit()
		self.grammar.CmdSetRuleState("wordsRule", 1)
		# Commit the changes to the grammar
		self.grammar.Rules.Commit()
		# And add an event handler that's called back when recognition occurs
		self.eventHandler = ContextEvents(self.context)
		
class ContextEvents(win32com.client.getevents("SAPI.SpSharedRecoContext")):
	"""Called when a word/phrase is successfully recognized  -
		ie it is found in a currently open grammar with a sufficiently high
	confidence"""
	def OnRecognition(self, StreamNumber, StreamPosition, RecognitionType, Result):
		newResult = win32com.client.Dispatch(Result)
		print "You said: ",newResult.PhraseInfo.GetText()
		speechParse(VOICE_ACTIONS[newResult.PhraseInfo.GetText()])
		
def speechParse(number):
	global nav_state
	
	if number == 0:
		pickup()
	if number == 1:
		drop()
	if number == 2:
		nav_state[0] = not nav_state[0]
	if number == 3:
		nav_state[1] = not nav_state[1]
	if number == 4:
		nav_state[2] = not nav_state[2]
	if number == 5:
		nav_state = [0,0,0]

speechReco = SpeechRecognition(VOICE_ACTIONS.keys())
vizact.ontimer(0,pythoncom.PumpWaitingMessages)

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
obj = []
lastSelection = []
attached = False
nav_state = [0,0,0]


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

#Head Tracking Specific Groups
head = viz.addGroup()
#headOffset = viz.addGroup(parent=head)

#World Setup Helper
setup = vetools.VizardWorldSetup(viz)

#Ray Setup
rayLink = viz.link(ray, objParent, enabled=True)
rayEnd.setPosition([0,0,-43])

#Hand Setup
hand.visible(viz.OFF)
hand.parent(virtualHand)

#Lights Setup
headLight = view.getHeadLight()

lightL = setup.addOmniLight([-5,10,0])
lightR = setup.addOmniLight([5,10,0])

#Populate World
room = setup.addModel('models/walls.obj',parent=world)

#room_window = setup.addModel('models/walls_window.obj',parent=world)
#room_floor = setup.addModel('models/walls_floor.obj',parent=world)
#room_wall = setup.addModel('models/walls_wall.obj',[-16,0,0],parent=world)

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

#Textures
tile = viz.addTexture('images/tile.jpg')
room.texture(tile)

#Links Ray to View
viewLink = viz.link(view, ray, enabled=True)
viewLink.setDstFlag(viz.LINK_POS_RAW) #Don't offset viewpoint position with eyeheight
transOperator = viewLink.preTrans([0,0,.1]) #Ray translation from camera
rotateOperator = viewLink.preEuler([0,0,0])

headTrackingLink = viz.link(head, view, enabled=True)
headTrans = headTrackingLink.preTrans([0,0,.1])

#Setting up Ray Physics
ray.collideMesh()
ray.disable(viz.DYNAMICS)
ray.enable(viz.COLLIDE_NOTIFY)	

#Initialize Head Tracking Data
head.setPosition([0,0,5],viz.ABS_GLOBAL)
skeleton = kinect.skeleton(sensor.get())

def formatIntersectResults(rawList):
	formatedList = []
	temp = []
	
	global ray
	global room
	#global room_wall
	#global room_window
	#global room_floor
	
	for elem in rawList:
		#if ((elem.object != ray) and (elem.object != room_wall) and (elem.object != room_window) 
		#and (elem.object != room_floor) and (not temp.count(elem.object))):
		if ((elem.object != ray) and (elem.object != room) and (not temp.count(elem.object))):
			formatedList.append(elem)
			temp.append(elem.object)
			
	return formatedList
	
def offsetKinectData(position, offset=45):
	top = viz.addGroup()
	top.setEuler(0,0,0)
	
	child = viz.addGroup(parent=top)
	
	child.setPosition(position,viz.ABS_PARENT)
	top.setEuler(offset,0,0)
	
	return child.getPosition(viz.ABS_GLOBAL)
	
def updateScene():
	global intersectedObjects
	global initGrabVector
	global lastSelection
	global nav_state
	global attached

	skeleton.update(sensor.get())
	
	#headTrans.setPosition(offsetKinectData(kinect.scaleData(skeleton.HEAD[0:3]),-5))
	headTrans.setPosition(kinect.scaleData(skeleton.HEAD[0:3]))
		
	horizontalVector = vizmat.VectorToPoint([-1,0,0],[1,0,0])
	hands = kinect.midpoint(skeleton.HAND_LEFT[0:3],skeleton.HAND_RIGHT[0:3])
	elbows = kinect.midpoint(skeleton.ELBOW_LEFT[0:3],skeleton.ELBOW_RIGHT[0:3])
	
	#hands = midpoint(offsetKinectData(skeleton.HAND_LEFT[0:3]),offsetKinectData(skeleton.HAND_RIGHT[0:3]))
	#elbows = midpoint(offsetKinectData(skeleton.ELBOW_LEFT[0:3]),offsetKinectData(skeleton.ELBOW_RIGHT[0:3]))
	
	rayVector = kinect.unmirror(vizmat.VectorToPoint(elbows,hands))
	rotVector = vizmat.VectorToPoint(skeleton.HAND_LEFT[0:3],skeleton.HAND_RIGHT[0:3])
	
	#rotVector = vizmat.VectorToPoint(offsetKinectData(skeleton.HAND_LEFT[0:3]),offsetKinectData(skeleton.HAND_RIGHT[0:3]))
	
	m = viz.Matrix()
	m.makeVecRotVec(rotVector,horizontalVector)
	m.postQuat(vizmat.LookToQuat(rayVector))
	
	rotateOperator.setQuat(m.getQuat())
	transOperator.setPosition(vetools.subtract(kinect.scaleData(hands),kinect.scaleData(skeleton.HEAD[0:3])),viz.ABS_GLOBAL)
	
	intersectedObjects = formatIntersectResults(viz.intersect(ray.getPosition(viz.ABS_GLOBAL), rayEnd.getPosition(viz.ABS_GLOBAL), all=True))
	
	#Highlighting Effect
	if (not attached):
		if intersectedObjects:
			[node.object.emissive([0,0,0]) for node in lastSelection]
			intersectedObjects[0].object.emissive(viz.GREEN)
			lastSelection = intersectedObjects
			
		elif lastSelection:
			[node.object.emissive([0,0,0]) for node in lastSelection]
	
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
	global initGrabVector
	
	if intersectedObjects:
		X1 = intersectedObjects[0].object.getMatrix(viz.ABS_GLOBAL)
		initGrabVector = vizmat.VectorToPoint(skeleton.HAND_LEFT[0:3],skeleton.HAND_RIGHT[0:3])
			
		#Attach
		intersectedObjects[0].object.parent(objParent)
		intersectedObjects[0].object.setMatrix(X1,viz.ABS_GLOBAL)
		attached = True
				
		obj = intersectedObjects
vizact.onkeydown('p', pickup)

def drop():
	global obj
	global attached
	
	if obj:
		X1 = obj[0].object.getMatrix(viz.ABS_GLOBAL)
		
		#Release
		obj[0].object.parent(world)
		obj[0].object.setMatrix(X1,viz.ABS_GLOBAL)
		attached = False
			
		obj = []
vizact.onkeydown('d', drop)

def rotateState():
	head.setEuler(90,0,0)
	
vizact.onkeydown('g', rotateState)

def endSession():
	sensor.command(9)
	time.sleep(2)
	viz.quit()
vizact.onkeydown('q', endSession)
