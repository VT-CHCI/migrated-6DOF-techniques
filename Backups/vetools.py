import viz
import vizmat
import math

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
		
	def addModel(self,path,position=[0,0,0],orientation=[0,0,0],scale=[1,1,1],parent=None):
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
		model.collideMesh()
		model.disable(self.viz.DYNAMICS)
		
		return model
		
	def addOmniLight(self,position=[0,0,0],intensity=2,linearatt=0.2):
		#Add Light
		light = self.viz.add(self.viz.LIGHT)
		
		#Set parameters
		light.position(position[0],position[1],position[2])
		light.linearattenuation(linearatt)
		light.intensity(intensity)
		
		return light
		
def formatIntersectionResults(rawList,ray,room):
	formatedList = []
	temp = []
	
	#Removes ray, floor and duplicates from list
	for elem in rawList:
		if ((elem.object != ray) and (elem.object != room) and (not temp.count(elem.object))):
			formatedList.append(elem)
			temp.append(elem.object)
			
	return formatedList

class HomerTools(object):
	def __init__(self,viz,calibrationPos,worldGroup,virtualHandGroup,rayChildGroup):
		self.body = [calibrationPos[0],calibrationPos[1]-2,calibrationPos[2]]
		self.viz = viz
		self.world = worldGroup
		self.virtualHand = virtualHandGroup
		self.rayChild = rayChildGroup
	
	def changeCenterPoint(self,intersectObject):
		X1 = self.virtualHand.getMatrix(self.viz.ABS_GLOBAL)
		
		self.virtualHand.setPosition(intersectObject.point)
		self.virtualHand.parent(intersectObject.object)
		self.virtualHand.setMatrix(X1,self.viz.ABS_GLOBAL)
		
		basePos = intersectObject.object.getPosition(viz.ABS_GLOBAL)
		
		intersectObject.object.center(virtualHand.getPosition())		
		intersectObject.object.setPosition(subtractLists(basePos,intersectObject.object.getPosition(self.viz.ABS_GLOBAL)),self.viz.REL_GLOBAL)
		
	def attachVirtualHand(self,intersectedObject):
		X1 = intersectedObject.object.getMatrix(self.viz.ABS_GLOBAL)
		
		self.virtualHand.setPosition(intersectObject.point)
		
		#Can I set this to an inverse Quat and then set the object to the real quat so that it would negate the initial orienation?
		self.virtualHand.setQuat(self.rayChild.getQuat())
		
		intersectedObject.object.parent(self.virtualHand)
		intersectedObject.object.setMatrix(X1,self.viz.ABS_GLOBAL)
		
	def setOrientation(self,object):
		object.parent(self.rayChild)
		
		X1 = object.getMatrix(self.viz.ABS_GLOBAL)
		dummyGroup = self.viz.addGroup(parent=self.world)
		dummyGroup.setMatrix(X1,self.viz.ABS_GLOBAL)
		
		object.parent(self.world)
		
		return dummyGroup.getQuat()
		
	def setPosition(self,hand,object):
		pass
	
	def scalingFactor(self,hand,object):
		hand2objectDist = vizmat.Distance(hand,object)
		body2handDist = vizmat.Distance(self.body,hand)
		
		scalingFactor = hand2objectDist/body2handDist
		
		return scalingFactor

def int2bits(num):
	bits=[]
	
	while (num > 0):
		bits.append(num % 2)
		num = num >> 1
		
	bits.extend([0]*(8-len(bits)))
	return bits
	
def subtractLists(a,b):
	difference = [a - b for a, b in zip(a,b)]
	
	return difference

def inverseQuat(q):
	denominator = sum([pow(elem,2) for elem in q])
	invQuat = [q[0],-q[1],-q[2],-q[3]]
	invQuat = [elem/denominator for elem in invQuat]
	
	return invQuat
	
def multiplyQuats(q,r):
	t0 = (r[0]*q[0])-(r[1]*q[1])-(r[2]*q[2])-(r[3]*q[3])
	t1 = (r[0]*q[1])+(r[1]*q[0])-(r[2]*q[3])+(r[3]*q[2])
	t2 = (r[0]*q[2])+(r[1]*q[3])+(r[2]*q[0])-(r[3]*q[1])
	t3 = (r[0]*q[3])-(r[1]*q[2])+(r[2]*q[1])+(r[3]*q[0])
	t = [t0,t1,t2,t3]
	
	return t
	
def subtractQuats(q,r):
	t = multiplyQuats(q,inverseQuat(r))
	
	return t
	
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
	