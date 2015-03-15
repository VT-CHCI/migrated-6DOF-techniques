import viz
import vizact



viz.go()
viz.phys.enable()
viz.clearcolor(viz.SKYBLUE)

box = viz.add( 'box.wrl' )
box.alpha( .2 )
box.color( viz.RED )

def drawborder(obj):
	savedEuler = obj.getEuler()
	obj.setEuler([0, 0, 0])
	bb = obj.getBoundingBox()
	obj.setEuler(savedEuler)
	box.setPosition( bb[3:7] )
	box.setEuler(obj.getEuler())
	box.scale( bb[0:3] )

logo = viz.add( 'logo.wrl' )

logo.add( vizact.goto( 0, 0, 10, 10 ) )
logo.add( vizact.spin( 0, 1, 0, 45, viz.FOREVER ), 1 )

viz.phys.setGravity(0,-9.8/6,0) #Half Gravity
ground = viz.add('tut_ground.wrl')  # Add ground
ground.collidePlane()   # Make collideable plane

temp = viz.add('logo.wrl',pos=[0,1,6]) # Add logo
temp.collideMesh(bounce=1.5) # Collide and make it bounce a bit

for x in range(10):
    for z in range(10):
        ball = viz.add('white_ball.wrl',pos=[-.5+.1*x,2.5+.1*z,6],scale=[.5,.5,.5])
        ball.collideSphere()

def onTimer(num):
	drawborder( logo )

viz.callback(viz.TIMER_EVENT,onTimer)
viz.starttimer( 0, 0, viz.FOREVER )