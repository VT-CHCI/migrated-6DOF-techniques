import math
import random
import string
import sys
import os

f = open('Trial_3.txt', 'w')

def Positions(model):
	
	x = '%.2f' % (random.random()*2)
	y = '%.2f' % (random.random()*10)
	z = '%.2f' % (random.random()*5)
	
	u = '%.2f' % (random.random()*360)
	v = '%.2f' % (random.random()*360)
	w = '%.2f' % (random.random()*360)
	
	f.write("setup.addModel('"+model+"',"+"["+ str(x)+","+str(y)+","+str(z)+"]"+",["+ str(u)+","+str(v)+","+str(w)+"],"+"[1.001,1.001,1.001],parent=world)"+"\n")

Positions("Room/Design/Bed.obj")
Positions("Room/Design/Bed.obj")
Positions("Room/Design/Bed.obj")
Positions("Room/Design/Bed.obj")

Positions("Room/Design/Chair.obj")
Positions("Room/Design/Chair.obj")
Positions("Room/Design/Chair.obj")
Positions("Room/Design/Chair.obj")
	
Positions("Room/Design/Flowers.obj")
Positions("Room/Design/Flowers.obj")