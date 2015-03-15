import viz
import vizmat
import math

#Constants
RAYCASTING = 0
HOMER = 1

class VizardWorldSetup(object):
	def __init__(self,viz):
		self.viz = viz
		
	def setupCalImage(self,path,position=[0,4,0],scale=[5,5],calScene=None):
		if calScene is None:
			calScene = self.viz.Scene2
		calPic = self.viz.add(path,scene=calScene)
		quad = self.viz.add(self.viz.TEXQUAD,scene=calScene)
		quad.translate(position[0],position[1],position[2])
		quad.scale(scale[0],scale[1])
		quad.texture(calPic)
		
	def addModel(self,path,position=[0,0,0],orientation=[0,0,0],scale=[1,1,1],physics=True,parent=None):
		#Add model
		model = self.viz.add(path)
		
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
			model.disable(self.viz.DYNAMICS)
		
		return model
		
	def addOmniLight(self,position=[0,0,0],intensity=2):
		#Add Light
		light = self.viz.addLight(self.viz.WORLD)
		light.enable()
		
		#Set parameters
		light.position(position[0],position[1],position[2])
		light.intensity(intensity)
		
		return light
	
	def reset(self,model,position=[0,0,0],orientation=[0,0,0],scale=[1,1,1]):
		#Set position, orientation & scale
		model.setPosition(position)
		model.setEuler(orientation)
		model.setScale(scale)

class InteractionTools(object):
	def __init__(self,viz,rayObject,handObject,virtualHandGroup,bodyObject,objectParentGroup,positionMarkerGroup,wimObjectParentGroup,worldGroup):
		self.viz = viz
		self.ray = rayObject
		self.hand = handObject
		self.body = bodyObject
		self.virtualHand = virtualHandGroup
		self.objParent = objectParentGroup
		self.posMarker = positionMarkerGroup
		self.miniObjParent = wimObjectParentGroup
		self.world = worldGroup
		
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
		self.hand.visible(self.viz.ON)
		self.hand.setQuat(self.ray.getQuat(self.viz.ABS_GLOBAL),self.viz.ABS_GLOBAL)
		self.ray.visible(self.viz.OFF)
		
		#Calculate scaling Factor
		objDistance = vizmat.Distance(self.body.getPosition(self.viz.ABS_GLOBAL),self.virtualHand.getPosition(self.viz.ABS_GLOBAL))
		handDistance = vizmat.Distance(self.body.getPosition(self.viz.ABS_GLOBAL),self.ray.getPosition(self.viz.ABS_GLOBAL))
		
		if handDistance == 0.0 or handDistance < 0.0:
			handDistance = .001
			
		self.scalingFactor = objDistance/handDistance
		
		#Setup marker to calculate HOMER movements
		self.body.lookat(self.ray.getPosition(self.viz.ABS_GLOBAL),self.viz.ABS_GLOBAL)
		self.posMarker.setPosition(self.virtualHand.getPosition(self.viz.ABS_GLOBAL),self.viz.ABS_GLOBAL)
	
	def homerMove(self):
		#Homer Rotation
		XMoveCurrent = self.objParent.getMatrix(self.viz.ABS_GLOBAL)
		XMoveCurrent.preMult(self.XMoveInit.inverse())
		
		self.virtualHand.setQuat(XMoveCurrent.getQuat(),self.viz.ABS_GLOBAL)
		
		#Homer Position
		objDistance = self.scalingFactor * vizmat.Distance(self.body.getPosition(self.viz.ABS_GLOBAL),self.ray.getPosition(self.viz.ABS_GLOBAL))
		
		self.body.lookat(self.ray.getPosition(self.viz.ABS_GLOBAL),self.viz.ABS_GLOBAL)
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
		
	def wimCheck(self, rayPosition, wimPosition, attachFlag, wimState, rayObject, controllerObject, rayEndPoint):
		moveDist = vizmat.Distance(rayPosition, wimPosition)
		
		if not attachFlag: 
			if moveDist < 1.25:
				controllerObject.visible(viz.ON)
				rayObject.visible(viz.OFF)
				rayEndPoint.setPosition([0,0,.40])
				
				wimState = True
			else:
				controllerObject.visible(viz.OFF)
				rayObject.visible(viz.ON)
				rayEndPoint.setPosition([0,0,43])
				
				wimState = False
		return wimState
	
	def release(self,mode,object):
		self.X1 = object.object.getMatrix(self.viz.ABS_GLOBAL)
			
		#Release
		object.object.parent(self.world)
		object.object.setMatrix(self.X1,self.viz.ABS_GLOBAL)
		
		if mode == HOMER:
			self.hand.visible(self.viz.OFF)
			self.ray.visible(self.viz.ON)

def formatIntersectionResults(rawList,ray,controller,room):
	formatedList = []
	temp = []
	
	#Removes ray, floor and duplicates from list
	for elem in rawList:
		if ((elem.object != ray) and (elem.object != controller) and (elem.object != room) and (not temp.count(elem.object))):
			formatedList.append(elem)
			temp.append(elem.object)
			
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
	