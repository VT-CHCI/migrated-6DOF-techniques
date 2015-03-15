import viz
import math
from math import sqrt

#-------------------------------------------------------------------------------
# Vector 3D class in support of low pass filter
#-------------------------------------------------------------------------------
class Vector3:
	def __init__(self, xx = None, yy = None, zz = None):
		if xx != None and yy == None and zz == None:
			#xx is a vector, we create a new vector passing
			#xx values as arguments
			self.x = xx.x
			self.y = xx.y
			self.z = xx.z
		elif xx != None and yy != None and zz == None:
			#two points to create a vector from xx to yy
			self.x = yy.x-xx.x
			self.y = yy.y-xx.y
			self.z = yy.z-xx.z
		elif xx != None and yy != None and zz != None:
			self.x = xx
			self.y = yy
			self.z = zz
		else:
			print "Vector Creation Error!"
			viz.quit()
	
	def __str__(self):
		return str(self.x)+", "+str(self.y)+", "+str(self.z)
	
	def __add__(self, vec):
		return Vector3(self.x + vec.x, self.y + vec.y, self.z + vec.z)
		
	def __sub__(self, vec):
		return Vector3(self.x - vec.x, self.y - vec.y, self.z - vec.z)
		
	def __mul__(self, val):
		return Vector3(self.x * val, self.y * val, self.z * val)
		
	def __div__(self, val):
		return Vector3(self.x / val, self.y / val, self.z / val)
		
	def abs (self):
		return Vector3(math.fabs(self.x),math.fabs(self.y), math.fabs(self.z))
		
	def dot(self,v):
		return (self.x * v.x + self.y * v.y + self.z * v.z)
		
	def norm(self):
		return sqrt(dot(self))
		
	def distance(self,v):
		return norm([self.x-v.x,self.y-v.y,self.z-v.z])
		
	def distanceSquared(self,v):
		return (self.x-v.x)**2+(self.y-v.y)**2+(self.z-v.z)**2
	
	def magnitude(self):
		return (self.x**2+self.y**2+self.z**2)**0.5
	
	def magnitudeSquared(self):
		return self.x**2+self.y**2+self.z**2
		
	def normalize(self):
		mag = self.magnitude()
		if mag != 0:
			self.x /= mag
			self.y /= mag
			self.z /= mag
	
	def Dot(v1,v2):
		return (v1.x * v2.x + v1.y * v2.y + v1.z * v2.z)
	
	def Cross(v1, v2):
		return Vector3(v1.y*v2.z-v1.z*v2.y,v1.z*v2.x-v1.x*v2.z,v1.x*v2.y-v1.y*v2.x)

	def DistanceToLine(origin, direction, point):
		return Vector3.Cross(direction, point - origin).magnitude()

	def DistanceToLineSquared(origin, direction, point):
		return Vector3.Cross(direction, point - origin).magnitudeSquared()
		
	def PositionInRay(origin, direction, point):
		return Vector3.Dot(direction, point - origin)

	def IntersectionPoint(origin, direction, point):
		#t = Vector3.Dot(direction, point - origin)
		#print t
		return origin + (direction * Vector3.Dot(direction, point - origin))
	
	def Adjust(xyz, z):
		out = Vector3(xyz)
		out.normalize()
		factor = z/out.z
		return Vector3(out.x*factor, out.y*factor, out.z*factor)
		
	def Transform(self,quat):
		return Vector3(quat[3]*quat[3]*self.x + 2*quat[1]*quat[3]*self.z - 2*quat[2]*quat[3]*self.y + quat[0]*quat[0]*self.x + 2*quat[1]*quat[0]*self.y + 2*quat[2]*quat[0]*self.z - quat[2]*quat[2]*self.x - quat[1]*quat[1]*self.x,
					   2*quat[0]*quat[1]*self.x + quat[1]*quat[1]*self.y + 2*quat[2]*quat[1]*self.z + 2*quat[3]*quat[2]*self.x - quat[2]*quat[2]*self.y + quat[3]*quat[3]*self.y - 2*quat[0]*quat[3]*self.z - quat[0]*quat[0]*self.y,
					   2*quat[0]*quat[2]*self.x + 2*quat[1]*quat[2]*self.y + quat[2]*quat[2]*self.z - 2*quat[3]*quat[1]*self.x - quat[1]*quat[1]*self.z + 2*quat[3]*quat[0]*self.y - quat[0]*quat[0]*self.z + quat[3]*quat[3]*self.z)
		
	def max (self, f):
		vec = Vector3(0,0,0)
		if self.x > f:
			vec.x = self.x
		else:
			vec.x = f

		if self.y > f:
			vec.y = self.y
		else:
			vec.y = f

		if self.z > f:
			vec.z = self.z
		else:
			vec.z = f
		
		return vec
		
	def min (self, f):
		vec = Vector3(0,0,0)
		
		if self.x < f:
			vec.x = self.x
		else:
			vec.x = f

		if self.y < f:
			vec.y = self.y
		else:
			vec.y = f

		if self.z < f:
			vec.z = self.z
		else:
			vec.z = f
		
		return vec
	
# pbase_Plane(): get base of perpendicular from point to a plane
#    Input:  P = a 3D point
#            PL = a plane with point V0 and normal n
#    Output: *B = base point on PL of perpendicular from P
#    Return: the distance from P to the plane PL
def distancePointPlane( P, PL, B ):
	sn = -dot( PL, P)
	sd = dot(PL, PL)
	sb = sn / sd
	
	B = [P[0] + sb * PL[0],P[1] + sb * PL[1],P[2] + sb * PL[2]]
	return distance(P, B)
