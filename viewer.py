import viz
import vizact
import vizshape
import vizconnect
import vizcam
from PIL import Image
import PIL

from enum import Enum
from collections import namedtuple

Dims = namedtuple("Dims", ['width', 'height']) #width, height

class Resolution(Enum):
    FULL = 1
    QUARTER = 2

class ImageStack:

    def __init__(self, resolution=Resolution.FULL):
        self.num_images = None
        self.image_size_bytes = None
        self.image_dims = Dims(0,0)
        self.res = resolution
        self.blob = None #The large binary
        self.image_array = None #Array of buffers with image data

        self._loadBlob(self.res)
        self._makeImageArray()  

    def _loadBlob(self, res):
        filename = None
        self.num_images = 998

        if res == Resolution.FULL:
            filename = "D:/image_700x516_L_361200bytes.rawblob"
            self.image_dims = Dims(700, 516)
            
        elif res == Resolution.QUARTER:
            filename = "D:/image_352x259_L_91168bytes_998images.rawblob"
            self.image_dims = Dims(352, 259)
            
        self.image_size_bytes = self.image_dims[0] * self.image_dims[1]

        with open(filename, "rb") as f:
            self.blob = f.read()

    #slice the blob up into an array of buffers
    def _makeImageArray(self):
        self.image_array = [None] * self.num_images
        
        for i in range(0, self.num_images):
            start = i * self.image_size_bytes
            end = start + self.image_size_bytes

            # print("Image{}".format(i))

            image = self.blob[start:end]
            self.image_array[i] = image

    #(x,y) -> (col, row)  
    def getPixel(self, image_index, row, col):
        #assume 8-bit grayscale byte position
        byte_pos = (row * self.image_dims.width) + col  
        return self.image_array[image_index][byte_pos]


viz.setMultiSample(4)
viz.fov(60)
window = viz.MainWindow
view = viz.MainView
window.clearcolor(1,1,1)
cam = vizcam.PivotNavigate(center=[0,0,250],distance=1450,sensitivity=[1.0,1.0])
def IsThisVillanovaCAVE():
    cave_host_names = ["exx-PC","render-PC"]
    import socket
    if socket.gethostname() in cave_host_names:
        return True
    else:
        return False

if IsThisVillanovaCAVE():
    CONFIG_FILE = "vizconnect_config_CaveFloor+ART_headnode.py"
    vizconnect.go(CONFIG_FILE)
    rawInput = vizconnect.getConfiguration().getRawDict("input")
    vizconnect.getAvatar().getAttachmentPoint("l_hand").getNode3d().remove()
    vizconnect.getAvatar().getAttachmentPoint("r_hand").getNode3d().remove()
    BUTTON_LEFT = 4
    BUTTON_LEFTMID = 3
    BUTTON_RIGHTMID = 2
    BUTTON_RIGHT = 1
    BUTTON_TRIGGER = 0
    
    vizconnect.getTransport('wandmagiccarpet').getNode3d().setMatrx(viewMatrix)
else:
    viz.go()
    view.setPosition([500,1.82,-1200])
    vizact.onkeydown('w', view.move,0,1,0)
    vizact.onkeydown('s', view.move,0,-1,0)
    

slider = viz.addSlider()
slider.setTickSize(0.1,2)
slider.setPosition(0.5,0.1)

#350/258 [2.8,2.06,0.4]
#images into memory, save images, line them up, load from single file bc one file is faster and can slice up one file from RAM 
#Overall tree hierarchy, addGroup for all nodes 
#Vizard 5 2.9.0, vizard 7 8.1.0

imageStack = ImageStack(resolution=Resolution.FULL)
colorMap = {}
clones = []
downsample_factor = 4
boxSize = 8

for k in range(0,100):
    print(k)
    for j in range(0,imageStack.image_dims[1],downsample_factor):
        for i in range(0,imageStack.image_dims[0],downsample_factor):
            col = imageStack.getPixel(k,i,j) / 255
            #0.06737980074756128
            if col > 0.06737980074756128:
                if colorMap.get(col) == None:
                    colorMap.update({col : vizshape.addBox(size=(boxSize*downsample_factor,boxSize*downsample_factor,boxSize),pos=(i*boxSize,-j*boxSize,k*boxSize),color=(col,col,col),cullFace=False)})
                else:
                    parentPos = colorMap.get(col).getPosition()
                    clones.append(colorMap.get(col).clone(parent=colorMap.get(col),pos=(-parentPos[0]+i*boxSize,-parentPos[1]-j*boxSize,-parentPos[2]+k*boxSize)))
            

colorKeys = list(colorMap.keys())
print(len(clones))
def updateVoxels(threshold):
    for i in colorKeys:
        if i < threshold:
            colorMap.get(i).visible(viz.OFF)
        elif i >= threshold and not colorMap.get(i).getVisible():
            colorMap.get(i).visible(viz.ON)
if not IsThisVillanovaCAVE():
    vizact.onslider(slider,updateVoxels)


def onButtonDown(e):
    if IsThisVillanovaCAVE():
        if rawinput['flystick'].isButtonDown(BUTTON_LEFTMID):
            view.move([0,0.5,0])
        elif rawinput['flystick'].isButtonDown(BUTTON_RIGHTMID):
            view.move([0,-0.5,0])
        elif rawinput['flystick'].isButtonDown(BUTTON_LEFT):
            if slider.get() - 0.05 >= 0:
                updateVoxels(slider.get() - 0.05)
                slider.set(slider.get() - 0.05)
        elif rawinput['flystick'].isButtonDown(BUTTON_RIGHT):
            if slider.get() + 0.05 <= 1:
                updateVoxels(slider.get() + 0.05)
                slider.set(slider.get() + 0.05)
        
if IsThisVillanovaCAVE():
    viz.callback(viz.SENSOR_DOWN_EVENT, onButtonDown)
    
    