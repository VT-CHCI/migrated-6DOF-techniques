import viz
import vizmat
import vizshape
import math

#Constants
RAYCASTING = 0
HOMER = 1

class InteractionTools(object):
	def __init__(self,viz,rayObject,handObject,head,handRay,handWIM,miniWorld,workspace):
		self.viz = viz
		self.rayObject = rayObject
		self.handObject = handObject
		self.handRay = handRay
		self.miniWorld = miniWorld
		self.workspace = workspace
		
		#HOMER Specific
		self.body = self.viz.addGroup(parent=head)
		self.virtualHand = self.viz.addGroup(parent=workspace)
		self.posMarker = self.viz.addGroup(parent=self.body)
		self.handInBodySpace = viz.addGroup(parent=head)

		self.handObject.parent(self.virtualHand)
		self.body.setPosition([0,-3.5,1])
		self.body.setEuler([0,0,0],viz.ABS_GLOBAL)
		
		self.objParent = self.viz.addGroup(parent=handRay)
		
		#Wim Specific
		self.miniObjParent = viz.addGroup(parent=miniWorld)
		self.wimHolder = self.viz.addGroup(parent=head)
		
		#Matrices
		self.X1 = vizmat.Transform()
		self.XOffset = vizmat.Transform()
		self.XMoveInit = vizmat.Transform()
		self.XMoveCurrent = vizmat.Transform()
		
		#HOMER Scaling Factor
		self.scalingFactor = 0.0
	
	def raycastingAttach(self,intersectedObject):
		#Set Matrix
		self.X1 = intersectedObject.object.getMatrix(self.viz.ABS_GLOBAL)
				
		#Attach
		intersectedObject.object.parent(self.objParent)
		intersectedObject.object.setMatrix(self.X1,self.viz.ABS_GLOBAL)
		
	def homerAttach(self,intersectedObject):
		#Set Matrices
		self.XMoveInit = self.objParent.getMatrix(self.viz.ABS_GLOBAL)
		self.X1 = intersectedObject.object.getMatrix(self.viz.ABS_GLOBAL)
		
		#Add object to virtual hand
		self.virtualHand.setPosition(intersectedObject.point)
		self.virtualHand.setQuat([0,0,0,1],self.viz.ABS_GLOBAL)
		intersectedObject.object.parent(self.virtualHand)
		intersectedObject.object.setMatrix(self.X1,self.viz.ABS_GLOBAL)
		
		#Replace move controller with virtual hand at intersection point with proper rotation
		self.handObject.visible(self.viz.ON)
		self.handObject.setQuat(self.handRay.getQuat(self.viz.ABS_GLOBAL),self.viz.ABS_GLOBAL)
		self.rayObject.visible(self.viz.OFF)
		
		#Calculate scaling Factor
		objDistance = vizmat.Distance(self.body.getPosition(self.viz.ABS_GLOBAL),self.virtualHand.getPosition(self.viz.ABS_GLOBAL))
		handDistance = vizmat.Distance(self.body.getPosition(self.viz.ABS_GLOBAL),self.handRay.getPosition(self.viz.ABS_GLOBAL))
		
		if handDistance == 0.0 or handDistance < 0.0:
			handDistance = .001
			
		self.scalingFactor = objDistance/handDistance
		
		#Setup marker to calculate HOMER movements
		
		self.handInBodySpace.setMatrix(self.handRay.getMatrix(viz.ABS_GLOBAL),viz.ABS_GLOBAL)
		self.body.lookat(self.handInBodySpace.getPosition())
		#self.body.lookat(self.handRay.getPosition(self.viz.ABS_GLOBAL),self.viz.ABS_GLOBAL)
		
		
		self.posMarker.setPosition(self.virtualHand.getPosition(self.viz.ABS_GLOBAL),self.viz.ABS_GLOBAL)
		
	def homerMove(self):
		#Homer Rotation
		XMoveCurrent = self.objParent.getMatrix(self.viz.ABS_GLOBAL)
		XMoveCurrent.preMult(self.XMoveInit.inverse())
		
		self.virtualHand.setQuat(XMoveCurrent.getQuat(),self.viz.ABS_GLOBAL)
		
		#Homer Position
		objDistance = self.scalingFactor * vizmat.Distance(self.body.getPosition(self.viz.ABS_GLOBAL),self.handRay.getPosition(self.viz.ABS_GLOBAL))
		
		#self.body.lookat(self.handRay.getPosition(self.viz.ABS_GLOBAL),self.viz.ABS_GLOBAL)
		self.handInBodySpace.setMatrix(self.handRay.getMatrix(viz.ABS_GLOBAL),viz.ABS_GLOBAL)
		self.body.lookat(self.handInBodySpace.getPosition())
		
		tempVector = vizmat.VectorToPoint(self.body.getPosition(self.viz.ABS_GLOBAL),self.posMarker.getPosition(self.viz.ABS_GLOBAL))
		virtualHandPos = vizmat.MoveAlongVector(self.body.getPosition(self.viz.ABS_GLOBAL),tempVector,objDistance)
		
		self.virtualHand.setPosition(virtualHandPos,self.viz.ABS_GLOBAL)

	def wimAttach(self,intersectedObject):		
		self.miniObjParent.setMatrix(self.objParent.getMatrix(self.viz.ABS_GLOBAL),self.viz.ABS_GLOBAL)
					
		self.XMoveInit = self.miniObjParent.getMatrix()
		
		self.XMoveCurrent = self.miniObjParent.getMatrix()
		self.XMoveCurrent.preMult(self.XMoveInit.inverse())
		
		self.XOffset = intersectedObject.object.getMatrix()
		self.XOffset.preMult(self.XMoveCurrent.inverse())
	
	def wimMove(self,attachedObject):
		self.miniObjParent.setMatrix(self.objParent.getMatrix(self.viz.ABS_GLOBAL),self.viz.ABS_GLOBAL)
		
		self.XMoveCurrent = self.miniObjParent.getMatrix()
		self.XMoveCurrent.preMult(self.XMoveInit.inverse())
		self.XMoveCurrent.preMult(self.XOffset)
		
		attachedObject.object.setMatrix(self.XMoveCurrent.get())
	
	def release(self,mode,object):
		self.X1 = object.object.getMatrix(self.viz.ABS_GLOBAL)
			
		#Release
		object.object.parent(self.workspace)
		object.object.setMatrix(self.X1,self.viz.ABS_GLOBAL)
		
		if mode == HOMER:
			self.handObject.visible(self.viz.OFF)
			self.rayObject.visible(self.viz.ON)
	
	def wimPickup(self):
		#Set Matrices
		self.XMoveInit = self.objParent.getMatrix(self.viz.ABS_GLOBAL)
		self.X1 = self.miniWorld.getMatrix(self.viz.ABS_GLOBAL)
		
		#Add object to virtual hand
		self.wimHolder.setPosition(self.miniWorld.getPosition())
		self.wimHolder.setQuat([0,0,0,1],self.viz.ABS_GLOBAL)
		self.miniWorld.setParent(self.wimHolder)
		self.miniWorld.setMatrix(self.X1,self.viz.ABS_GLOBAL)
	
	def wimUpdate(self):
		XMoveCurrent = self.objParent.getMatrix(self.viz.ABS_GLOBAL)
		XMoveCurrent.preMult(self.XMoveInit.inverse())
		
		self.wimHolder.setQuat(XMoveCurrent.getQuat(),self.viz.ABS_GLOBAL)
		
	def wimRelease(self,group):
		self.X1 = self.miniWorld.getMatrix(self.viz.ABS_GLOBAL)
			
		#Release
		self.miniWorld.setParent(group)
		self.miniWorld.setMatrix(self.X1,self.viz.ABS_GLOBAL)
						
class states(object):
	def __init__(self):
		#Global Variables
		self.nav_state = [0,0,0]
		self.lastSelection = []
		self.intersectedObjects = []
		self.obj = []

		#States
		self.wimSelect = False
		self.attached = False
		self.wimEnabled = False
		
		self.start = False
		self.finalStart = False
		
		self.wimAttached = False
		
		self.goodDrop = False
	
def formatIntersectionResults(rawList,exemptList):
	formatedList = []
	temp = []
	exempt = False
	
	#Removes ray, floor and duplicates from list
	for elem in rawList:
		for exemption in exemptList:
			if (elem.object == exemption):
				exempt = True
				
		if ((not temp.count(elem.object)) and (not exempt)):
			formatedList.append(elem)
			temp.append(elem.object)
		
		exempt = False
			
	return formatedList
	
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
	