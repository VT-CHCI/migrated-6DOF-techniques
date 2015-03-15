import string
import math
import time
import sys
import os

import viz

#Constants
RAYCASTING = 0
HOMER = 1
WIM = 2

PRACTICE = 1
DOCKING = 2
CAPSTONE = 3

MAX_TRIALS = 10

IS900 = 0
MOVE = 1
KINECT = 2

def systemOrder(idNumber):
	idNumber = idNumber % 9
	
	if idNumber == 0:
		idNumber = 9-1
	else:
		idNumber = idNumber - 1
		
	order = [[IS900,MOVE,KINECT]
			,[IS900,MOVE,KINECT]
			,[IS900,MOVE,KINECT]
			,[KINECT,IS900,MOVE]
			,[KINECT,IS900,MOVE]
			,[KINECT,IS900,MOVE]
			,[MOVE,KINECT,IS900]
			,[MOVE,KINECT,IS900]
			,[MOVE,KINECT,IS900]]
			
	technique = [RAYCASTING
				,HOMER
				,WIM
				,RAYCASTING
				,HOMER
				,WIM
				,RAYCASTING
				,HOMER
				,WIM]
	
	return technique[idNumber],order[idNumber]
	
def tupleInBounds (selection, match, offset):
	matches = False
	
	if (selection[0] < match[0] + offset) and (selection[0] > match[0] - offset) and (selection[1] < match[1] + offset) and (selection[1] > match[1] - offset) and (selection[2] < match[2] + offset) and (selection[2] > match[2] - offset):
		matches = True
		
	return matches
	
class experiment(object):
	def __init__(self,viz,world,head):
		self.viz = viz
		self.world = world
		self.head = head
		
		self.state = PRACTICE
		self.system = MOVE

	def calibrate(self):
		setupCalImage('calibrate.png')
		
		self.head.setPosition(0,4,-8)
		self.head.setEuler([0,0,0],self.viz.ABS_GLOBAL)
	
class generateRoom(object):
	def __init__(self,viz,world,head):
		self.viz = viz
		self.world = world
		self.head = head
		
		self.addLights()
	
	def remove(self):
		self.walls.remove()
		self.bed.remove()
		self.books.remove()
		self.bookshelf.remove()
		self.chair.remove()
		self.clock.remove()
		self.console.remove()
		self.floorLamp.remove()
		self.flowers.remove()
		self.footStool.remove()
		self.glass.remove()
		self.pictureFrame.remove()
		self.radio.remove()
		self.sideLamp.remove()
		self.speakerLeft.remove()
		self.speakerRight.remove()
		self.tv.remove()	
		self.vase.remove()
		
	def load(self):
		#Setup view and background color
		self.head.setEuler([42.4,5,0],self.viz.REL_PARENT)
		
		self.viz.clearcolor(self.viz.BLACK)
		
		self.walls = addModel('Room/Design/room-single-walls.obj',scale=[1,1,1],physics=False,parent=self.world)
		self.walls.cullFace(self.viz.GL_BACK)
		
		self.bed = addModel('Room/Design/Bed.obj',[50,0,150],scale=[1,1,1],parent=self.world)
		self.books = addModel('Room/Design/Books.obj',[230,26.0,200],scale=[1,1,1],parent=self.world)
		self.bookshelf = addModel('Room/Design/Bookshelf.obj',[200,0,200],scale=[1,1,1],parent=self.world)
		self.chair = addModel('Room/Design/Chair.obj',[200,0,0],scale=[1,1,1],parent=self.world)
		self.clock = addModel('Room/Design/Clock.obj',[200,120,-234.5],scale=[1,1,1],parent=self.world)
		self.console = addModel('Room/Design/Console.obj',[50,0,-200],scale=[1,1,1],parent=self.world)
		self.floorLamp = addModel('Room/Design/Floor_Lamp.obj',[-150,0,170],scale=[1,1,1],parent=self.world)
		self.flowers = addModel('Room/Design/Flowers.obj',[210,26,200],scale=[1,1,1],parent=self.world)
		self.footStool = addModel('Room/Design/Foot_Stool.obj',[170,0,-30],scale=[1,1,1],parent=self.world)
		self.glass = addModel('Room/Design/Glass.obj',[175,31.7,2.5],scale=[1,1,1],parent=self.world)
		self.pictureFrame = addModel('Room/Design/Picture_Frame.obj',[195,26,190],scale=[1,1,1],parent=self.world)
		self.radio = addModel('Room/Design/Radio.obj',[168.5,26,192.5],scale=[1,1,1],parent=self.world)
		self.sideLamp = addModel('Room/Design/Small_Lamp.obj',[180,26,202.5],scale=[1,1,1],parent=self.world)
		self.speakerLeft = addModel('Room/Design/Speaker_L.obj',[150,0,-200],[180,0,0],scale=[1,1,1],parent=self.world)
		self.speakerRight = addModel('Room/Design/Speaker_R.obj',[-50,0,-200],[180,0,0],scale=[1,1,1],parent=self.world)
		self.tv = addModel('Room/Design/Tv.obj',[50,120,-234.5],scale=[1,1,1],parent=self.world)
		self.vase = addModel('Room/Design/Vase.obj',[250,0,-200],scale=[1,1,1],parent=self.world)
		
	def addLights(self):
		addOmniLight([-100,1000,0],1.0)
		addOmniLight([200,1000,0],1.0)
		addOmniLight([-290,155,-185],.5)

		addOmniLight([180,55,200],.2)
		addOmniLight([-150,90,170],.8)
		
	def startingPosition(self):
		self.viz.clearcolor(self.viz.BLACK)
		
class generateTrials(object):
	def __init__(self,viz,world,head,maxTrials):
		self.viz = viz
		self.world = world
		self.head = head
		self.maxTrials = maxTrials
		
		self.start = False
		
		self.trialText = viz.addText(' ',parent=viz.SCREEN)
		self.trialText.setBackdrop(viz.BACKDROP_RIGHT_BOTTOM)
		self.trialText.setBackdropColor([0.5,0.25,0])
		self.trialText.setPosition(0.05,0.1)
		self.trialText.fontSize(36)
		
	def chooseMatchSet(self,system,order):
		#Determine the proper list based on system
		chooseMatchList = [i for i,x in enumerate(order) if x == system]

		if chooseMatchList[0] == 0:
			self.matchList = 	["addModel('Room/Design/Chair.obj',[16.9,55.8,15.7],[349.59,8.38,265.29],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Chair.obj',[04.9,74.5,25.0],[117.31,23.02,199.69],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Chair.obj',[01.1,03.1,34.3],[293.18,31.96,299.46],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Chair.obj',[02.7,68.1,08.7],[18.84,151.78,338.76],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Chair.obj',[14.3,48.7,42.6],[302.25,113.06,159.33],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"saddModel('Room/Design/Radio.obj',[08.2,67.3,-28.8],[110.25,124.81,161.33],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Radio.obj',[06.2,33.8,-30.8],[277.80,153.58,169.57],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Radio.obj',[12.9,50.9,-11.2],[292.89,206.74,272.52],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Radio.obj',[12.5,48.1,-34.6],[113.11,109.08,239.90],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Radio.obj',[18.3,77.0,00.1],[26.88,26.88,247.66],[1.01,1.01,1.01],physics=False,parent=self.world)"]
			self.selectList = 	["addModel('Room/Design/Chair.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Chair.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Chair.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Chair.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Chair.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Radio.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Radio.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Radio.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Radio.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Radio.obj',scale=[1,1,1],parent=self.world)"]	
		elif chooseMatchList[0] == 1:
			self.matchList = 	["addModel('Room/Design/Chair.obj',[00.9,50.6,04.1],[280.11,225.82,91.78],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Chair.obj',[14.2,65.1,09.4],[352.38,71.72,80.99],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Chair.obj',[16.8,61.6,22.7],[314.07,68.52,46.24],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Chair.obj',[13.7,86.9,49.0],[87.49,99.22,326.77],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Chair.obj',[08.3,61.3,03.8],[296.46,78.17,16.97],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Radio.obj',[17.1,27.7,-40.5],[205.76,191.37,51.91],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Radio.obj',[12.8,30.9,-45.5],[314.16,94.62,77.49],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Radio.obj',[14.7,14.2,-15.7],[291.84,132.94,11.38],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Radio.obj',[17.7,63.3,-33.2],[30.88,63.59,65.99],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Radio.obj',[08.5,32.8,-32.3],[308.04,239.29,171.74],[1.01,1.01,1.01],physics=False,parent=self.world)"]
			self.selectList = 	["addModel('Room/Design/Chair.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Chair.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Chair.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Chair.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Chair.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Radio.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Radio.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Radio.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Radio.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Radio.obj',scale=[1,1,1],parent=self.world)"]	
		elif chooseMatchList[0] == 2:
			self.matchList = 	["addModel('Room/Design/Chair.obj',[03.4,50.5,16.9],[194.44,357.75,271.39],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Chair.obj',[18.3,62.1,19.3],[62.94,11.40,77.09],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Chair.obj',[15.8,53.2,10.1],[216.87,102.00,90.81],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Chair.obj',[10.1,47.6,45.1],[117.50,336.47,177.32],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Chair.obj',[03.3,75.0,23.5],[203.37,141.91,70.48],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Radio.obj',[13.2,08.7,-24.9],[116.88,234.28,70.45],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Radio.obj',[15.1,30.8,-40.1],[250.26,4.01,117.63],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Radio.obj',[19.0,19.1,-30.2],[68.17,304.55,271.49],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Radio.obj',[13.4,58.9,-30.6],[163.68,190.55,248.66],[1.01,1.01,1.01],physics=False,parent=self.world)"
								,"addModel('Room/Design/Radio.obj',[04.1,02.9,-02.1],[179.40,208.91,179.38],[1.01,1.01,1.01],physics=False,parent=self.world)"]
			self.selectList = 	["addModel('Room/Design/Chair.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Chair.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Chair.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Chair.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Chair.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Radio.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Radio.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Radio.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Radio.obj',scale=[1,1,1],parent=self.world)","addModel('Room/Design/Radio.obj',scale=[1,1,1],parent=self.world)"]		

	def setup(self):
		self.listIndex = 0
		self.trialText.message('Trial: ' + str(self.listIndex + 1))
		
		self.backdrop = addModel('Room/Design/Backdrop.obj',[0,0,25],scale=[50,50,50],parent=self.world)
		
		self.match = eval(self.matchList[self.listIndex])
		self.select = eval(self.selectList[self.listIndex])
		
		self.match.alpha(0.25)
		
		self.startingPosition()
		
	def startingPosition(self):
		#Setup view and background color
		self.head.setPosition(0,30,-75)
		self.head.setEuler([0,0,0],self.viz.ABS_GLOBAL)
		
		self.viz.clearcolor(.25,.25,.25)
		
	def nextTrial(self):
		self.match.remove()
		self.select.remove()
		
		self.listIndex = self.listIndex + 1
		self.trialText.message('Trial: ' + str(self.listIndex + 1))
		
		if self.listIndex < self.maxTrials:
			self.match = eval(self.matchList[self.listIndex])
			self.select = eval(self.selectList[self.listIndex])

			self.match.alpha(0.5)
			return True
		else:
			return False
			
	def getTrial(self):
		return self.listIndex
		
	def getMatchInfo(self):
		return self.match.getPosition(), self.match.getEuler()
	
	def getSelectInfo(self):
		return self.select.getPosition(), self.select.getEuler()
	
	def inBounds(self,posOffset,rotOffset):
		if tupleInBounds(self.select.getPosition(self.viz.ABS_GLOBAL),self.match.getPosition(self.viz.ABS_GLOBAL),posOffset) and tupleInBounds(self.select.getEuler(self.viz.ABS_GLOBAL),self.match.getEuler(self.viz.ABS_GLOBAL),rotOffset):
			self.select.emissive(self.viz.RED)
			return True
		else:
			self.select.emissive([0,0,0])
			return False
			
	def clear(self):
		self.match.remove()
		self.select.remove()
		self.trialText.remove()
		self.backdrop.remove()

class recorder(object):
	def __init__(self,participant_id,trialsClass):
		self.participant_id = participant_id
		self.dockingTrials = trialsClass
		self.timer = time.time()
		
		localtime = time.localtime(time.time())
		self.data = open('Trials/'+'ID '+str(participant_id)+' '+str(localtime[1])+'.'+str(localtime[2])+'.'+str(localtime[0])+' '+str(localtime[3])+str(localtime[4])+str(localtime[5])+'.txt', 'w')
		
	def trialStart(self):
		matchPos, matchEuler = self.dockingTrials.getMatchInfo()
		self.timer = time.time()
		
		self.data.write('Start Trial '+str(self.dockingTrials.getTrial()+1)+' MatchInfo: '+str(matchPos)+str(matchEuler)+'\n')
		self.data.write('--------------------------------------------------------------------------------------------------------'+ '\n')
		
	def writeDrop(self,mode):
		selectPos, selectEuler = self.dockingTrials.getSelectInfo()
		
		if mode == RAYCASTING:
			header = 'Raycasting Drop - '
		elif mode == HOMER:
			header = 'HOMER Drop - '
		elif mode == WIM:
			header = 'WIM Drop - '
			
		self.data.write(header+time.asctime(time.localtime(time.time()))+' SelectInfo: '+str(selectPos)+str(selectEuler)+'\n')
			
	def trialEnd(self,dropStatus):
		if dropStatus:
			self.data.write('End Trial '+str(self.dockingTrials.getTrial()+1)+' Time: '+ str((time.time() - self.timer))+'\n'+'\n')
		else:
			self.data.write('Skipped Trial '+str(self.dockingTrials.getTrial()+1)+' Time: '+ str((time.time() - self.timer))+'\n'+'\n')
			
	def startCapstone(self):
		self.data.write('Capstone Start Time: '+time.asctime(time.localtime(time.time()))+'\n')

		self.timer = time.time()
		
	def endCapstone(self, room):
		self.data.write('Capstone Time: '+ str((time.time() - self.timer))+'\n'+'\n')
		self.data.write('Bed: [' + "][".join(str(x) for x in room.bed.getPosition()) + '],[' + "][".join(str(x) for x in room.bed.getEuler())+']\n')
		self.data.write('books: [' + "][".join(str(x) for x in room.books.getPosition()) + '],[' + "][".join(str(x) for x in room.books.getEuler())+']\n')
		self.data.write('bookshelf: [' + "][".join(str(x) for x in room.bookshelf.getPosition()) + '],[' + "][".join(str(x) for x in room.bookshelf.getEuler())+']\n')
		self.data.write('chair: [' + "][".join(str(x) for x in room.chair.getPosition()) + '],[' + "][".join(str(x) for x in room.chair.getEuler())+']\n')
		self.data.write('clock: [' + "][".join(str(x) for x in room.clock.getPosition()) + '],[' + "][".join(str(x) for x in room.clock.getEuler())+']\n')
		self.data.write('console: [' + "][".join(str(x) for x in room.console.getPosition()) + '],[' + "][".join(str(x) for x in room.console.getEuler())+']\n')
		self.data.write('floorLamp: [' + "][".join(str(x) for x in room.floorLamp.getPosition()) + '],[' + "][".join(str(x) for x in room.floorLamp.getEuler())+']\n')
		self.data.write('flowers: [' + "][".join(str(x) for x in room.flowers.getPosition()) + '],[' + "][".join(str(x) for x in room.flowers.getEuler())+']\n')
		self.data.write('footStool: [' + "][".join(str(x) for x in room.footStool.getPosition()) + '],[' + "][".join(str(x) for x in room.footStool.getEuler())+']\n')
		self.data.write('glass: [' + "][".join(str(x) for x in room.glass.getPosition()) + '],[' + "][".join(str(x) for x in room.glass.getEuler())+']\n')
		self.data.write('pictureFrame: [' + "][".join(str(x) for x in room.pictureFrame.getPosition()) + '],[' + "][".join(str(x) for x in room.pictureFrame.getEuler())+']\n')
		self.data.write('radio: [' + "][".join(str(x) for x in room.radio.getPosition()) + '],[' + "][".join(str(x) for x in room.radio.getEuler())+']\n')
		self.data.write('sideLamp: [' + "][".join(str(x) for x in room.sideLamp.getPosition()) + '],[' + "][".join(str(x) for x in room.sideLamp.getEuler())+']\n')
		self.data.write('speakerLeft: [' + "][".join(str(x) for x in room.speakerLeft.getPosition()) + '],[' + "][".join(str(x) for x in room.speakerLeft.getEuler())+']\n')
		self.data.write('speakerRight: [' + "][".join(str(x) for x in room.speakerRight.getPosition()) + '],[' + "][".join(str(x) for x in room.speakerRight.getEuler())+']\n')
		self.data.write('tv: [' + "][".join(str(x) for x in room.tv.getPosition()) + '],[' + "][".join(str(x) for x in room.tv.getEuler())+']\n')
		self.data.write('vase: [' + "][".join(str(x) for x in room.vase.getPosition()) + '],[' + "][".join(str(x) for x in room.vase.getEuler())+']\n')
		
	def close(self):
		self.data.close()
		
def setupCalImage(path,scale=[5,5],calScene=None):
	if calScene is None:
		calScene = viz.Scene2
	calPic = viz.add(path,scene=calScene)
	quad = viz.add(viz.TEXQUAD,scene=calScene,parent=viz.SCREEN)
	quad.translate(.5,.5)
	quad.scale(scale[0],scale[1])
	quad.texture(calPic)
	
	viz.MainView.setScene(viz.Scene2)
	headlight = viz.MainView.getHeadLight()
	headlight.enable()
	
def addModel(path,position=[0,0,0],orientation=[0,0,0],scale=[1,1,1],physics=True,parent=None):
	#Add model
	model = viz.add(path)
	
	#Set position, orientation & scale
	model.setPosition(position)
	model.setEuler(orientation)
	model.setScale(scale)
	
	#Set parent
	if parent is not None:
		model.parent(parent)
	
	#Set up physics
	if physics:
		model.collideMesh()
		model.disable(viz.DYNAMICS)
	
	return model
	
def addOmniLight(position=[0,0,0],intensity=2):
	#Add Light
	light = viz.addLight(viz.WORLD)
	light.enable()
	
	#Set parameters
	light.position(position[0],position[1],position[2])
	light.intensity(intensity)
	
	return light