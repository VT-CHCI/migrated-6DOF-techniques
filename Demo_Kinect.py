import viz
import os
import fnmatch
import random
import math
import vizmat
import time

#My Modules
import vetools
import kinect

#Voice Includes
from win32com.client import constants
import win32com.client
import pythoncom

VOICE_ACTIONS = { "kinect pickup" : 0
				,"kinect drop" : 1
				,"kinect move" : 2
				,"kinect turn right" : 3
				,"kinect turn left" : 4
				,"kinect stop now" : 5 }
				
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
	global selection_state
	
	if number == 0:
		selection_state = True
	if number == 1:
		selection_state = False
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

#Global Variables
calibrationPos = [0,0,0]
oldTriggerState = 0
lastSelection = []
obj = []
nav_state = [0,0,0]
selection_state = False

#States
calibration = False
wimSelect = False
attached = False
wimEnabled = False
headTrackingEnabled = False

mode = RAYCASTING

#Load Models
ray = viz.add('models/kinectRay.obj')
hand = viz.add('models/hand.obj')
controller = viz.add('models/moveController.obj')

#View Setup
viz.MainWindow.fov(FOV, viz.AUTO_COMPUTE)

view = viz.MainView
view.setPosition(0,4,-8)
view.setEuler(0,0,0)

#Connect to Move Sensors
kinectSensor = viz.add('KinectSensor.dls')

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
eyes = viz.addGroup()

#Helpers
setup = vetools.VizardWorldSetup(viz)
interaction = vetools.InteractionTools(viz,ray,hand,virtualHand,body,objParent,posMarker,miniObjParent,world)

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

lightL = setup.addOmniLight([-5,15,0])
lightR = setup.addOmniLight([5,15,0])
center = setup.addOmniLight([0,0,0])
lightCL = setup.addOmniLight([-15,5,0])
lightCR = setup.addOmniLight([15,5,0])

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
eyes.setPosition(view.getPosition(viz.ABS_GLOBAL),viz.ABS_GLOBAL)
skeleton = kinect.skeleton(kinectSensor.get())

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

def updateScene():
	global calibrationPos
	global oldTriggerState
	global calibration
	global lastSelection
	global attached
	global obj
	global wimSelect

	skeleton.update(kinectSensor.get())
	view.setPosition(vetools.add(eyes.getPosition(viz.ABS_GLOBAL),kinect.scaleData(skeleton.HEAD[0:3])),viz.ABS_GLOBAL)
	
	#Ray Position & Orientation Data
	horizontalVector = vizmat.VectorToPoint([-1,0,0],[1,0,0])
	
	hands = midpoint(skeleton.HAND_LEFT[0:3],skeleton.HAND_RIGHT[0:3])
	elbows = midpoint(skeleton.ELBOW_LEFT[0:3],skeleton.ELBOW_RIGHT[0:3])
	
	rayVector = unmirror(vizmat.VectorToPoint(hands,elbows))
	rotVector = vizmat.VectorToPoint(skeleton.HAND_LEFT[0:3],skeleton.HAND_RIGHT[0:3])

	m = viz.Matrix()
	m.makeVecRotVec(rotVector,horizontalVector)
	m.postQuat(vizmat.LookToQuat(rayVector))
		
	rotateOperator.setQuat(m.getQuat())
	transOperator.setPosition(hands,viz.ABS_GLOBAL)
	
	if wimEnabled:
		#WIM Position & Orientation Data
		wimTransOperator.setPosition(vetools.configPos(wimData[0:3],calibrationPos,calibration,[0,.5,.5]))
		wimRotateOperator.setQuat(vetools.configQuat(wimData[3:7],[0,90,0]))
		
		#Set Controller Model Position & Orientation Data
		controller.setPosition(ray.getPosition())
		controller.setQuat(ray.getQuat())
		
		#Check to see if two moves are close to one another
		wimSelect = interaction.wimCheck(ray.getPosition(viz.ABS_GLOBAL), miniWorld.getPosition(viz.ABS_GLOBAL), attached, wimSelect, ray, controller, rayEnd)
	
	if attached:
		if (mode == HOMER) & (not wimSelect):
			interaction.homerMove()
		
		if wimSelect:
			interaction.wimMove(obj[0])

	intersectedObjects = vetools.formatIntersectionResults(viz.intersect(ray.getPosition(viz.ABS_GLOBAL), rayEnd.getPosition(viz.ABS_GLOBAL), all=True),ray,controller,room)
	
	#Highlighting Effect
	if (not attached):
		if intersectedObjects:
			[node.object.emissive([0,0,0]) for node in lastSelection]
			intersectedObjects[0].object.emissive(viz.GREEN)
			lastSelection = intersectedObjects
			
		elif lastSelection:
			[node.object.emissive([0,0,0]) for node in lastSelection]	

	#Navigation Actions
	if nav_state[0]:
		eyes.setPosition(vizmat.MoveAlongVector(eyes.getPosition(viz.ABS_GLOBAL),vizmat.VectorToPoint(ray.getPosition(viz.ABS_GLOBAL),rayEnd.getPosition(viz.ABS_GLOBAL)),5*viz.elapsed()),viz.ABS_GLOBAL)
	if nav_state[1]:
		view.setEuler([60*viz.elapsed(),0,0],viz.BODY_ORI,viz.REL_PARENT)
	if nav_state[2]:
		view.setEuler([-60*viz.elapsed(),0,0],viz.BODY_ORI,viz.REL_PARENT) 
	
	#Trigger Actions
	if selection_state:
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
	
	elif not selection_state:
		if obj:
			interaction.release(mode,obj[0])
			
			#State variables
			attached = False
			obj = []
	
vizact.ontimer(UPDATE_RATE,updateScene)

def reset():
	#Viewpoint reset
	eyes.setPosition(0,4,-8)
	
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
	else:
		wimLink.setEnabled(False)
		miniWorld.visible(viz.OFF)
		
		controller.visible(viz.OFF)
		ray.visible(viz.ON)
		rayEnd.setPosition([0,0,43])
		
		wimSelect = False
vizact.onkeydown('w',cycleWIM)	
	
def endSession():
	kinectSensor.command(9)
	time.sleep(2)
	viz.quit()
vizact.onkeydown('q', endSession)
