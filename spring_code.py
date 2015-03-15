import viz
import vetools

viz.go()

view = viz.MainView

view.setPosition(0,75,0)
view.setEuler(0,90,0)

world = viz.addGroup()
setup = vetools.VizardWorldSetup(viz)

setup.addOmniLight([0,150,0],1.5)

#Populate World
room = setup.addModel('Room/Design/Room.obj',scale=[.1,.1,.1],physics=False,parent=world)
bed = setup.addModel('Room/Design/Bed.obj',[21,0,15],[90,0,0],scale=[.1,.1,.1],parent=world)
books = setup.addModel('Room/Design/Books.obj',[-18.5,4.97,5],[-90,0,0],scale=[.1,.1,.1],parent=world)
bookshelf = setup.addModel('Room/Design/Bookshelf.obj',[12,0,15],[90,0,0],scale=[.1,.1,.1],parent=world)
chair = setup.addModel('Room/Design/Chair.obj',[3,0,-8],[90,0,0],scale=[.1,.1,.1],parent=world)
clock = setup.addModel('Room/Design/Clock.obj',[29.9,12,15],[-90,0,0],scale=[.1,.1,.1],parent=world)
console = setup.addModel('Room/Design/Console.obj',[-18.5,0,7],[90,0,0],scale=[.1,.1,.1],parent=world)
floorLamp = setup.addModel('Room/Design/Floor_Lamp.obj',[8,0,-5],scale=[.1,.1,.1],parent=world)
flowers = setup.addModel('Room/Design/Flowers.obj',[-18.5,4.97,9],scale=[.1,.1,.1],parent=world)
footStool = setup.addModel('Room/Design/Foot_Stool.obj',[0,0,-5],[90,0,0],scale=[.1,.1,.1],parent=world)
glass = setup.addModel('Room/Design/Glass.obj',[13,2.6,12.75],scale=[.1,.1,.1],parent=world)
pictureFrame = setup.addModel('Room/Design/Picture_Frame.obj',[-18.5,4.97,7],[-90,0,0],scale=[.1,.1,.1],parent=world)
radio = setup.addModel('Room/Design/Radio.obj',[12,2.6,12],scale=[.1,.1,.1],parent=world)
sideLamp = setup.addModel('Room/Design/Small_Lamp.obj',[12,2.6,18],scale=[.1,.1,.1],parent=world)
speakerLeft = setup.addModel('Room/Design/Speaker_L.obj',[-19,0,-3],[-90,0,0],scale=[.1,.1,.1],parent=world)
speakerRight = setup.addModel('Room/Design/Speaker_R.obj',[-19,0,17],[-90,0,0],scale=[.1,.1,.1],parent=world)
tv = setup.addModel('Room/Design/Tv.obj',[-22,12,7],[90,0,0],scale=[.1,.1,.1],parent=world)
vase = setup.addModel('Room/Design/Vase.obj',[25,0,5],scale=[.1,.1,.1],parent=world)

vizact.onkeydown( 's', viz.window.screenCapture, 'image.jpg' )