import vizmat
import math

class skeleton(object):
	def __init__(self,data):
		self.ID = data[0]
	
		self.HIP_CENTER = data[1:6]
		self.SPINE = data[6:11]
		self.SHOULDER_CENTER = data[11:16]
		self.HEAD = data[16:21 ]
		self.SHOULDER_LEFT = data[21:26]
		self.ELBOW_LEFT = data[26:31]
		self.WRIST_LEFT = data[31:36]
		self.HAND_LEFT = data[36:41]
		self.SHOULDER_RIGHT = data[41:46]
		self.ELBOW_RIGHT = data[46:51]
		self.WRIST_RIGHT = data[51:56]
		self.HAND_RIGHT = data[56:61]
		self.HIP_LEFT = data[61:66]
		self.KNEE_LEFT = data[66:71]
		self.ANKLE_LEFT = data[71:76]
		self.FOOT_LEFT = data[76:81]
		self.HIP_RIGHT = data[81:86]
		self.KNEE_RIGHT = data[86:91]
		self.ANKLE_RIGHT = data[91:96]
		self.FOOT_RIGHT = data[96:101]
		self.COUNT = data[101:106]
		
	def update(self,data):
		self.ID = data[0]
	
		self.HIP_CENTER = data[1:6]
		self.SPINE = data[6:11]
		self.SHOULDER_CENTER = data[11:16]
		self.HEAD = data[16:21 ]
		self.SHOULDER_LEFT = data[21:26]
		self.ELBOW_LEFT = data[26:31]
		self.WRIST_LEFT = data[31:36]
		self.HAND_LEFT = data[36:41]
		self.SHOULDER_RIGHT = data[41:46]
		self.ELBOW_RIGHT = data[46:51]
		self.WRIST_RIGHT = data[51:56]
		self.HAND_RIGHT = data[56:61]
		self.HIP_LEFT = data[61:66]
		self.KNEE_LEFT = data[66:71]
		self.ANKLE_LEFT = data[71:76]
		self.FOOT_LEFT = data[76:81]
		self.HIP_RIGHT = data[81:86]
		self.KNEE_RIGHT = data[86:91]
		self.ANKLE_RIGHT = data[91:96]
		self.FOOT_RIGHT = data[96:101]
		self.COUNT = data[101:106]
		
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