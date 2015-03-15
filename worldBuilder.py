#General Python Modules
import fnmatch
import random
import string
import math

#General Vizard Modules
import viz
import vizact
import vizmat
import vizshape

#My Modules
import vetools
import trialtools
import sensors

#Constants
UPDATE_RATE = 0
FOV = 60

HOMER = 1
MOVE = 1

#View Setup
viz.MainWindow.fov(FOV, viz.AUTO_COMPUTE)

viz.go()
viz.phys.enable()

#Trial Variables
system = MOVE
mode = HOMER

#General Groups
workspace = viz.addGroup(parent=viz.WORLD)
miniWorld = viz.addGroup(parent=viz.WORLD)

#HandModel Setup
handModel = viz.add('models/hand.obj')
handModel.setScale([10,10,10])
handModel.visible(viz.OFF)

#RayModel Setup
rayModel = viz.add('models/ray-long.obj')
rayEnd = viz.addGroup(parent=rayModel)
rayEnd.setPosition([0,0,700])
rayModel.setScale([2,2,2])
	
#Setting up Ray Physics
rayModel.collideMesh()
rayModel.disable(viz.DYNAMICS)
rayModel.enable(viz.COLLIDE_NOTIFY)

#User Navigation Group
user = viz.addGroup(parent=viz.WORLD)
head = viz.addGroup(parent=user)
eye = viz.addGroup(parent=head)
handRay = viz.addGroup(parent=user)
handWim = viz.addGroup(parent=user)
 
rayModel.setParent(handRay)
rayModel.setPosition(0,0,-1.75) #For some reason obj center doesn't match causing rotation offset

viewLink = viz.link(eye,viz.MainView,priority=2)
viewLink.setSrcFlag(viz.ABS_GLOBAL)

#Connect to Move Sensors
moveSystem = sensors.move(viz,.02,head,handRay,handWim)

#Calibration Instructions
trialtools.setupCalImage('calibrate.png')

#Helper Classes
interaction = vetools.InteractionTools(viz,rayModel,handModel,head,handRay,handWim,miniWorld,workspace)
state = vetools.states()

viz.setMultiSample(4)
env = viz.addEnvironmentMap('sky.jpg')
sky = viz.addCustomNode('skydome.dlc')
sky.texture(env)

design_space = viz.add('design_space.osg')
train = viz.add('train.osg')

menu1 = vizshape.addCube(size=.1,color = viz.BLUE,parent=viz.SCREEN)
menu1.setPosition(0,0,0)
menu1.setEuler(0,0,45)

menu2 = vizshape.addSphere(radius=.05,color = viz.RED,parent=viz.SCREEN)
menu2.setPosition(1,1,0)

menu3 = vizshape.addSphere(radius=.05,color = viz.GREEN,parent=viz.SCREEN)
menu3.setPosition(1,0,0)

menu4 = vizshape.addSphere(radius=.05,color = viz.PURPLE,parent=viz.SCREEN)
menu4.setPosition(0,1,0)

def pickup():	
	if state.intersectedObjects:
		interaction.homerAttach(state.intersectedObjects[0])
		print 'pickup'
						
		#update state variables
		state.obj = state.intersectedObjects
		state.attached = True
					
def drop():
	if state.obj:
		interaction.release(mode,state.obj[0])
		print 'drop'
		
		#update state variables
		state.attached = False
		state.obj = []

def onButtonUp(button):
	if system == MOVE:
		if button == 1:
			if not moveSystem.isCalibrated:
				moveSystem.calibrate()
				print "calibrate"
			else:
				drop()
		if button == 2:
			state.nav_state[0] = False
		if button == 7:
			state.nav_state[2] = False
		if button == 4:
			state.nav_state[1] = False
viz.callback(sensors.BUTTON_UP,onButtonUp)

def onButtonDown(button):
	if system == MOVE:
		if button == 1:
			pickup()
		if button == 2:
			state.nav_state[0] = True
		if button == 7:
			state.nav_state[2] = True
		if button == 4:
			state.nav_state[1] = True
viz.callback(sensors.BUTTON_DOWN,onButtonDown)


def updateScene():
	#update tracker information
	moveSystem.update()
	
	#Highlighting Effect or Homer Move depending on if an object is attached
	if state.attached:
		interaction.homerMove()
	else:
		if state.intersectedObjects:
			[node.object.emissive([0,0,0]) for node in state.lastSelection]
			state.intersectedObjects[0].object.emissive(viz.GREEN)
			state.lastSelection = state.intersectedObjects
			
		elif state.lastSelection:
			[node.object.emissive([0,0,0]) for node in state.lastSelection]	
			
	#Update state variables with currently interstected objects
	state.intersectedObjects = vetools.formatIntersectionResults(viz.intersect(rayModel.getPosition(viz.ABS_GLOBAL), rayEnd.getPosition(viz.ABS_GLOBAL), all=True),[rayModel])
		
	#Navigation Actions
	user.setCenter(head.getPosition())
	if state.nav_state[0]:
		user.setPosition(vizmat.MoveAlongVector(user.getPosition(viz.ABS_GLOBAL),vizmat.VectorToPoint(rayModel.getPosition(viz.ABS_GLOBAL),rayEnd.getPosition(viz.ABS_GLOBAL)),100*viz.elapsed()),viz.ABS_GLOBAL)
	if state.nav_state[1]:
		user.setEuler([60*viz.elapsed(),0,0],viz.RELATIVE)
	if state.nav_state[2]:
		user.setEuler([-60*viz.elapsed(),0,0],viz.RELATIVE)

vizact.ontimer(UPDATE_RATE,updateScene)

def mykeyboard(key):
	#close file when exiting the system
	if key == viz.KEY_ESCAPE:
		print 'Escape Key'
	
	#recalibrate
	if key == 'c':
		if system == MOVE:
			moveSystem.head.setPosition([0,0,0])
			moveSystem.isCalibrated = False
			trialtools.setupCalImage('calibrate.png')
		
	#Viewpoint reset
	if key == 'r':
		user.setPosition(13, 1.8, 11)
		head.setEuler([42.4,5,0],viz.VIEW_ORI)
		
	if key == 'b':
		action1 = vizact.sizeTo([2,2,2],time=2)
		menu1.addAction(action1)
		
	if key == 's':
		action2 = vizact.sizeTo([1,1,1],time=2)
		menu1.addAction(action2)
		
viz.callback(viz.KEYBOARD_EVENT,mykeyboard)

def onExit():
	print 'File Closed'
	
viz.callback(viz.EXIT_EVENT,onExit)

def onCollide(e):
	#Rumble effect
	if (not state.attached) and (system == MOVE):
		viz.director(moveSystem.rumble,75,.25)
viz.callback(viz.COLLIDE_BEGIN_EVENT, onCollide )

