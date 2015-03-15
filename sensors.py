import vizmat
import vizact
import math
import viz
import vetools

from LowPassDynamicFilter import LowPassDynamicFilter
from Vector3 import Vector3

BUTTON_DOWN = viz.getEventID('MOVE_BUTTON_DOWN')
BUTTON_UP = viz.getEventID('MOVE_BUTTON_UP')

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

IS900 = 0
MOVE = 1
KINECT = 2

class intersense(object):
	def __init__(self,portNumber,viz,scalingFactor,head,handRay,handWim):
		self.viz = viz
		self.scalingFactor = scalingFactor
		
		#Transformation Groups
		self.rayGroup = self.viz.addGroup()
		self.wimGroup = self.viz.addGroup()
		self.headGroup = self.viz.addGroup()
		
		self.oldButtonStateRay = int2bits(0)
		
		#Add Sensors and Tracker
		'''
		self.isense = self.viz.add('intersense.dle')
		
		self.headSensor = self.isense.addTracker(port=portNumber,station=1)
		self.headSensor.setSensitivity(0)
		self.headSensor.setEnhancement(2)
		
		self.raySensor = self.isense.addTracker(port=portNumber,station=2)
		self.raySensor.setSensitivity(0)
		self.raySensor.setEnhancement(2)
		
		self.wimSensor = self.isense.addTracker(port=portNumber,station=4)
		self.wimSensor.setSensitivity(0)
		self.wimSensor.setEnhancement(2)
		'''
		
		self.headSensor = self.viz.add('intersense.dls');
		self.raySensor = self.viz.add('intersense.dls');
		self.wimSensor = self.viz.add('intersense.dls');
		
		#Links
		#self.headTracker = self.viz.link(self.headGroup,head,priority=1,mask=self.viz.LINK_POS)
		headTracker = self.viz.link(self.headSensor,head,priority=1,mask=self.viz.LINK_POS)
		headTracker.postScale([scalingFactor,scalingFactor,scalingFactor],target=self.viz.LINK_POS_OP)

		#self.rayTracker = self.viz.link(self.rayGroup,handRay)
		rayTracker = self.viz.link(self.raySensor,handRay)
		rayTracker.postTrans([0,.5,0],target=self.viz.LINK_POS_OP)
		rayTracker.postScale([scalingFactor,scalingFactor,scalingFactor],target=self.viz.LINK_POS_OP)
		
		#self.wimTracker = self.viz.link(self.wimGroup,handWim)
		wimTracker = self.viz.link(self.wimSensor,handWim)
		wimTracker.postScale([scalingFactor,scalingFactor,scalingFactor],target=self.viz.LINK_POS_OP)
		wimTracker.postTrans([0,12,0],target=self.viz.LINK_POS_OP)
		wimTracker.preEuler([25,-60,10],target=self.viz.LINK_ORI_OP)
		
	def isValid(self):
		#return self.isense.valid()
		return self.headSensor.valid()
		
	def update(self):
		#self.rayJoystick = self.raySensor.getJoystickPosition()
		self.rayJoystick = self.raySensor.getData();
		
		#Update Button Events
		rayButtons = int2bits(int(self.rayJoystick[7]))
		if rayButtons != self.oldButtonStateRay:
			for i in range(0,len(rayButtons),1):
				if rayButtons[i] != self.oldButtonStateRay[i] and rayButtons[i] == 1:
					viz.sendEvent(BUTTON_DOWN,i)
				elif rayButtons[i] != self.oldButtonStateRay[i] and rayButtons[i] == 0:
					viz.sendEvent(BUTTON_UP,i)
		self.oldButtonStateRay = rayButtons
		
class move(object):
	def __init__(self,viz,scalingFactor,head,handRay,handWim):
		self.viz = viz
		self.scalingFactor = scalingFactor
		
		self.isCalibrated = False
		
		self.calibrationPos = handRay
		self.oldButtonStateRay = int2bits(0)
		self.oldButtonStateWim = int2bits(0)
		
		self.head = self.viz.addGroup()
		self.ray = self.viz.addGroup()
		self.wim = self.viz.addGroup()
		
		#Move Plugin
		self.raySensor = self.viz.add('MoveSensor.dls')
		self.wimSensor = self.viz.add('MoveSensor.dls')
		
		self.head.setPosition([0,0,0])
		
		self.rayData = self.raySensor.get()
		self.ray.setPosition(self.rayData[0:3])
		self.ray.setQuat(self.rayData[3:7])
		
		self.wimData = self.wimSensor.get()
		self.wim.setPosition(self.wimData[0:3])
		self.wim.setQuat(self.wimData[3:7])
		
		headTracker = self.viz.link(self.head,head,priority=1)

		rayTracker = self.viz.link(self.ray,handRay)
		rayTracker.postScale([scalingFactor,scalingFactor,scalingFactor],target=self.viz.LINK_POS_OP)
		#rayTracker.postTrans([0,3,0],target=self.viz.LINK_POS_OP)
		rayTracker.swapQuat([-1,-2,3,4])
		rayTracker.swapPos([1,2,-3])
		
		wimTracker = self.viz.link(self.wim,handWim)
		wimTracker.postScale([scalingFactor,scalingFactor,scalingFactor],target=self.viz.LINK_POS_OP)
		wimTracker.postTrans([0,2,0],target=self.viz.LINK_POS_OP)
		wimTracker.swapQuat([-1,-2,3,4])
		wimTracker.swapPos([1,2,-3])

	def isValid(self):
		if self.raySensor.valid() and self.wimSensor.valid():
			return True
		else:
			return False
			
	def update(self):
		#Update Tracking Data
		self.rayData = self.raySensor.get()
		self.ray.setPosition(self.rayData[0:3])
		self.ray.setQuat(self.rayData[3:7])
		
		self.wimData = self.wimSensor.get()
		self.wim.setPosition(self.wimData[0:3])
		self.wim.setQuat(self.wimData[3:7])
			
		#Update Button Events
		rayButtons = self.getButtons(0)
		if rayButtons != self.oldButtonStateRay:
			for i in range(0,len(rayButtons),1):
				if rayButtons[i] != self.oldButtonStateRay[i] and rayButtons[i] == 1:
					viz.sendEvent(BUTTON_DOWN,i)
				elif rayButtons[i] != self.oldButtonStateRay[i] and rayButtons[i] == 0:
					viz.sendEvent(BUTTON_UP,i)
		self.oldButtonStateRay = rayButtons
		
	def calibrate(self):
		self.head.setPosition(self.calibrationPos.getPosition())
		self.isCalibrated = True
		
		viz.MainView.setScene(viz.Scene1)
		
	def getButtons(self,controller=0):
		if controller == 0:
			return int2bits(int(self.rayData[10]))
		elif controller == 1:
			return int2bits(int(self.wimData[10]))
		else:
			return 0
			
	def rumble(self,strength,time,controller=0):
		if controller == 0:
			self.raySensor.command(1,'',strength)
			self.viz.waittime(time)
			self.raySensor.command(1,'',0)
		elif controller == 1:
			self.wimSensor.command(1,'',strength)
			self.viz.waittime(time)
			self.wimSensor.command(1,'',0)
			
class kinect(object):
	def __init__(self,viz,scalingFactor,head,handRay,handWim):
		self.viz = viz
		self.scalingFactor = scalingFactor
		
		self.head = self.viz.addGroup()
		self.handR = self.viz.addGroup()
		self.handL = self.viz.addGroup()
		
		self.rayMatrix = self.viz.Matrix()
		
		#Add Kinect Plugin
		self.kinectSensor = self.viz.add('KinectSensor.dls')
		
		data = self.kinectSensor.get()

		# low pass filter initialization, converted to degrees, which is how the filter is now being applied
		#self.filter = LowPassDynamicFilter(.25, 5, 0.33745, 6.7492)

		# if you want to use the filter for position, use this instead
		self.filterHead = LowPassDynamicFilter(0.25, 5, 0.01, 2.0)
		self.filterHandR = LowPassDynamicFilter(0.25, 5, 0.01, 2.0)
		self.filterHandL = LowPassDynamicFilter(0.25, 5, 0.01, 2.0)
		self.filterElbowR = LowPassDynamicFilter(0.25, 5, 0.01, 2.0)
		self.filterElbowL = LowPassDynamicFilter(0.25, 5, 0.01, 2.0)
		
		# used to determine the number of frames used in the animation and also the low pass filter
		self.previousFrameTick = self.viz.tick()
		self.fps = 0.0
		
		#Kinect Joints
		self.HEAD = data[16:21]
		self.ELBOW_LEFT = data[26:31]
		self.HAND_LEFT = data[36:41]
		self.ELBOW_RIGHT = data[46:51]
		self.HAND_RIGHT = data[56:61]

		self.head.setPosition(self.HEAD[0:3])
		self.handR.setPosition(self.HAND_RIGHT[0:3])
		self.handL.setPosition(self.HAND_LEFT[0:3])
		
		headTracker = self.viz.link(self.head,head,priority=1)
		headTracker.postScale([scalingFactor,scalingFactor,scalingFactor],target=self.viz.LINK_POS_OP)
		headTracker.swapPos([1,2,-3])
		
		rayTracker = self.viz.link(self.handR,handRay,priority=1)
		rayTracker.postScale([scalingFactor,scalingFactor,scalingFactor],target=self.viz.LINK_POS_OP)
		rayTracker.postTrans([0,9,0],target=self.viz.LINK_POS_OP)
		rayTracker.swapEuler([1,-2,-3])
		rayTracker.swapPos([1,2,-3])
		
	def isValid(self):
		return self.kinectSensor.valid()
		
	def update(self):
		currentFrameTick = self.viz.tick()
		self.fps = 1/(currentFrameTick-self.previousFrameTick)
		self.previousFrameTick = currentFrameTick
		
		data = self.kinectSensor.get()
		
		self.HEAD = data[16:21]
		self.ELBOW_LEFT = data[26:31]
		self.HAND_LEFT = data[36:41]
		self.ELBOW_RIGHT = data[46:51]
		self.HAND_RIGHT = data[56:61]
		
		tempRightHand = self.filterPosition(self.HAND_RIGHT[0:3],self.filterHandR)
		tempLeftHand = self.filterPosition(self.HAND_LEFT[0:3],self.filterHandL)
		
		self.head.setPosition(self.filterPosition(self.HEAD[0:3],self.filterHead))
		
		horizontalVector = vizmat.VectorToPoint([-1,0,0],[1,0,0])
		
		hands = midpoint(tempLeftHand,tempRightHand)
		elbows = midpoint(self.filterPosition(self.ELBOW_LEFT[0:3],self.filterElbowL),self.filterPosition(self.ELBOW_RIGHT[0:3],self.filterElbowR))
	
		rayVector = vizmat.VectorToPoint(hands,elbows)
		rotVector = vizmat.VectorToPoint(tempLeftHand,tempRightHand)
	
		self.rayMatrix.makeVecRotVec(rotVector,horizontalVector)
		self.rayMatrix.postQuat(vizmat.LookToQuat(rayVector))
		self.rayMatrix.setPosition(hands)
		
		self.handR.setPosition(self.rayMatrix.getPosition())
		self.handR.setQuat(self.rayMatrix.getQuat())

	def filterPosition(self,position,filter):
		#Apply Filter
		newPos = filter.Apply(Vector3(position[0],position[1],position[2]),self.fps)
		position[0] = newPos.x
		position[1] = newPos.y
		position[2] = newPos.z
		
		return position
		
#Helpful Functions
def int2bits(num):
	bits=[]
	
	while (num > 0):
		bits.append(num % 2)
		num = num >> 1
		
	bits.extend([0]*(8-len(bits)))
	return bits

def subtract(a,b):
	difference = [a - b for a, b in zip(a,b)]
	
	return difference
	
def add(a,b):
	sum = [a + b for a, b in zip(a,b)]
	
	return sum
	
def configQuat(dataQuat,offset=[0,0,0]):
	quat = [-dataQuat[0],-dataQuat[1],dataQuat[2],dataQuat[3]] #use if model is facing forward in blender
	
	X1 = vizmat.Transform()
	X1.setQuat(quat)
	X1.preEuler(offset)
	
	quat = X1.getQuat()
	
	return quat
	
def configPos(calibrated,dataPos,scalingFactor=0,calPos=[0,0,0],offset=[0,0,0]):
	pos = [point*scalingFactor for point in dataPos] #scaling factor
	
	if calibrated:
		pos = [pos - calPos for pos,calPos in zip(pos,calPos)]
		pos[2] = -pos[2]
		pos = [pos + offset for pos,offset in zip(pos,offset)]
		
	return pos
	
def scaleData(pos):
	pos[0] = pos[0]*1.0
	pos[1] = pos[1]*1.0
	pos[2] = -pos[2]*1.0
	
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
	
def addOffset(pos,offset):
	pos = [pos + offset for pos,offset in zip(pos,offset)]
	
	return pos