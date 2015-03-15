import viz
import time

viz.go()

raySensor = viz.add('MoveSensor.dls')
count = 0

def update():
	global count
	
	first = 255-count
	second = count
	
	print count
	
	raySensor.command(2,str(first),second)
	
	count = count + 1
vizact.ontimer(2,update)
