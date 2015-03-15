import viz
import vizmat

viz.setMultiSample(4)
viz.go()

import vizinfo
vizinfo.add('Hold down left mouse button to charge up\nRelease left button to fire ball\nPress \'r\' to reset boxes')

#Declare some constants
GRID_WIDTH      = 6
GRID_HEIGHT     = 6
SPACING         = 1.1
MAX_BALLS       = 20
MIN_POWER       = 1
MAX_POWER       = 50

#We need to enable physics
viz.phys.enable()

#Add a ground with an infinite collision plane
ground = viz.addChild('ground.osgb')
ground.collidePlane()

#List for holding the boxes and balls
boxes = []
balls = []

for i in range(GRID_WIDTH):
    boxes.append([])
    for j in range(GRID_HEIGHT):
        #Add a box model
        box = viz.addChild('crate.osgb',cache=viz.CACHE_CLONE)
        #Use the boxes bounding box for collisions
        box.collideBox()
        #Add the box to the list
        boxes[i].append(box)


for x in range(MAX_BALLS):
    #Add a ball model
    ball = viz.addChild('volleyball.osgb',scale=(3.5,3.5,3.5),cache=viz.CACHE_CLONE)
    #The balls collision will be represented by the bounding sphere of the ball
    ball.collideSphere()
    #Add the body to the list
    balls.append(ball)

#Create a generator this will loop through the balls
nextBall = viz.cycle(balls)

#Add a green marker that will show where we are aiming, disable picking on it
import vizshape
marker = vizshape.addSphere(radius=0.1,color=viz.GREEN)
marker.visible(False)
marker.disable(viz.PICKING)

#Add a progress bar to the screen that will show how much power is charged up
power = viz.addProgressBar('Power',pos=(0.8,0.1,0))
power.disable()
power.set(0)

#Move the head position back and up and look at the origin
viz.MainView.setPosition([0,5,-20])
viz.MainView.lookat([0,0,0])

#Disable mouse navigation
viz.mouse(viz.OFF)

#This function will reset all the boxes and balls
def ResetObjects():

    for i in range(GRID_WIDTH):
        for j in range(GRID_HEIGHT):
            #Reset the physics of the object (This will zero its velocities and forces)
            boxes[i][j].reset()
            #Reset the position of the box
            boxes[i][j].setPosition([(i*SPACING)-(GRID_WIDTH/2.0),j*SPACING+0.5,0])
            #Reset the rotation of the box
            boxes[i][j].setEuler([0,0,0])

    for b in balls:
        #Translate the ball underneath the ground
        b.setPosition([0,-5,0])
        #Disable physics on the ball
        b.disable(viz.PHYSICS)

ResetObjects()

#'r' key resets simulation
vizact.onkeydown('r',ResetObjects)

def ChargePower():
    #Get detailed information about where the mouse is pointed
    info = viz.pick(1)
    #Show and place marker based on intersection result
    marker.visible(info.valid)
    marker.setPosition(info.point)
    #Increment the amount of power charged up
    power.set(power.get()+0.05)

vizact.whilemousedown(viz.MOUSEBUTTON_LEFT,ChargePower)

def ShootBall():
    #Hide marker
    marker.visible(viz.OFF)
    #Convert the current mouse position from screen coordinates to world coordinates
    line = viz.MainWindow.screenToWorld(viz.mouse.getPosition())
    #Create a vector that points along the line the mouse is at
    vector = viz.Vector(line.dir)
    #Set length of vector based on the amount of power charged up
    vector.setLength(vizmat.Interpolate(MIN_POWER,MAX_POWER,power.get()))
    #Move the next ball to be fired to the begin point
    b = nextBall.next()
    b.setPosition(line.begin)
    #Reset the ball, set its velocity vector, and enable it
    b.reset()
    b.setVelocity(vector)
    b.enable(viz.PHYSICS)
    #Reset the power
    power.set(0)

vizact.onmouseup(viz.MOUSEBUTTON_LEFT,ShootBall)

#Set the background color
viz.clearcolor(viz.SKYBLUE)
