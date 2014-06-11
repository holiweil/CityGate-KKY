'''
Soubor sensors.py zahrnuje tridu KinectTrack pro zisk skeletonu a obrazovych dat
z Kinectum tridu Kamera pro praci s webovou kamerou a volne metody pro praci
s obrazovimi daty.

Autor: Jan Holecek
'''
import sys
import StringIO
import numpy
import Image
import cv2
import Queue
from pykinect import nui


# Vytvari ze Stringu JPEG obraz v pameti.#
def makeJpegFromMemory(string):
    imgJpeg = StringIO.StringIO()
    imgJpeg.write(string)
    imgJpeg.seek(0)
    return imgJpeg


# Vytvari ze Stringu OpenCV obraz.#
def makeCvImageFromMemory(string):
    nparr = numpy.fromstring(string, numpy.uint8)
    img_np = cv2.imdecode(nparr, cv2.CV_LOAD_IMAGE_COLOR)
    return img_np


# Uklada obraz jako JPEG do pameti.
# com (input) - mira komprese: 0 - nejvetsi, 100 - nejmensi
# string (input) - 0: vrati odkaz na objekt, 1: vrati jako String   
def saveJpegToMemory(img,com=0,string=0):
        img = Image.fromarray(img)
        imgJpeg = StringIO.StringIO()
        img.save(imgJpeg, "JPEG", quality=com)
        imgJpeg.seek(0)
        if string == 0:
            return imgJpeg
        elif string == 1:
            imgString = imgJpeg.getvalue()
            return imgString


#Ze Stringu vytvari seznam osbsahujici pozice jednotlivych kosti.#
def stringToSkeleton (string):
        skeleton = []
        bone = []
        sIndex = 0
        for index in range(len(string)):
            
            if string[index]=='|':
                end = string.find('/', index+1, len(string))
                skeleton.append(string[index+1:end])
            if string[index]=='/':
                end = string.find('|', index+1, len(string))
                
                numbers = string[index+1:end].split(',')
                numbers = [ int(x) for x in numbers ]
                subStr = numbers
                skeleton.append(subStr)
        return skeleton

'''
Trida poskytuje zakladni praci s webkamerou pomoci OpenCV
'''      
class Kamera():
    source = 0
    kamera = 0

    #Inicializace kamery.
    #source (input) - 0: interni kamera, 1: externi kamera 
    def loadKamera(self,source=0):
        self.kamera = cv2.VideoCapture(source)

      
    #Zisk aktualniho snimku z kamery #
    def getImage(self,fromArray = 0):
        ret, im = self.kamera.read()      
        im = numpy.array(im)
        im = cv2.cvtColor(im, cv2.COLOR_RGB2BGR)
        return im


'''
Trida poskytuje obrazova data z Kinectu pomoci knihovny PyKinect
'''       
class KinectTrack:

    firstPlayer = 0 #ID prvni sledovane kostry
    kinect = 0

    # velikost okna pro skalovani kostry
    width = 640
    height = 420


    # fronty jednotlivych druhu dat (video, hloubkova mapa, kostra)
    videoQ = Queue.Queue()
    depthQ = Queue.Queue()
    skeletonQ = Queue.Queue()

    nameList = ['HipCenter',
                    'Spine',
                    'ShoulderCenter',
                    'Head',
                    'ShoulderLeft',
                    'ElbowLeft',
                    'WristLeft',
                    'HandLeft',
                    'ShoulderRight',
                    'ElbowRight',
                    'WristRight',
                    'HandRight',
                    'HipLeft',
                    'KneeLeft',
                    'AnkleLeft',
                    'FootLeft',
                    'HipRight',
                    'KneeRight',
                    'AnkleRight',
                    'FootRight'
                     ]


    def __init__(self):
        self.kinect = nui.Runtime()
        self.firstPlayer = -1


    #Nastaveni elevace Kinectu#    
    def setElevation(self,elevation):
        self.kinect.camera.elevation_angle = elevation

        
    #
    #Video 
    #
    def startVideo(self,width=640,height=480):
        self.kinect.video_frame_ready += self.video_frame_ready
        if width==1280:
            size = nui.ImageResolution.Resolution1280x1024
        else:
            size = nui.ImageResolution.Resolution640x480
        self.kinect.video_stream.open(nui.ImageStreamType.Video, 2, size, nui.ImageType.Color )
        

    
    def video_frame_ready(self, frame):
        #1024,1280
        #480,640
        video = numpy.empty( ( 480, 640,4 ), numpy.uint8 )
        frame.image.copy_bits( video.ctypes.data )
        im = cv2.cvtColor(video, cv2.COLOR_BGRA2BGR)
        if self.videoQ.empty():        
            self.videoQ.put(im)


    #
    #Hloubkova mapa 
    #
    def startDepth(self):
        self.kinect.depth_frame_ready += self.depth_frame_ready
        self.kinect.depth_stream.open(nui.ImageStreamType.Depth, 2, nui.ImageResolution.Resolution320x240, nui.ImageType.Depth )
        
        
    
    def depth_frame_ready( frame ):
        depth = numpy.empty( ( 240, 320, 1 ), numpy.uint16 )
        frame.image.copy_bits( depth.ctypes.data )
        im = cv2.cvtColor(video, cv2.COLOR_BGRA2BGR)
        if self.depthQ.empty():
            self.depthQ.put(Image.fromarray(im))
            
    #
    #Kostra 
    #
    def startSkeleton(self):
        self.kinect.skeleton_engine.enabled = True
        self.kinect.skeleton_frame_ready += self.post_frame

    def post_frame(self,frame):
        if self.skeletonQ.empty():
            skelet = self.getSkeleton(frame)
            self.skeletonQ.put(skelet)    

    # True pokud je Kinectem sledovana nejaka kostra.#
    def isSkeleton(self):
        if self.firstPlayer == -1: return False
        else: return True

    # Nalezeni prvni sledovane kostry.#    
    def findPlayer (self):
        frame = self.kinect.skeleton_engine.get_next_frame()
        for index in range(6):
            
            if frame.SkeletonData[index].eTrackingState == 2 and self.firstPlayer == -1:
                self.firstPlayer = index
            if  frame.SkeletonData[self.firstPlayer].eTrackingState == 0 and not self.firstPlayer == -1:
                self.firstPlayer = -1

        return self.firstPlayer

    # Seznam kosti prepise na String.#
    def skeletonToString (self,skeleton):
        skeletonString = ''
        for index in range(len(skeleton)):
            if index%2 == 0:
                skeletonString =skeletonString + '|' + str(skeleton[index])+'/'
            elif index%2 == 1:
                skeletonString =skeletonString  + str(int(skeleton[index][0])) + ',' + str(int(skeleton[index][1])) + ',' + str(int(skeleton[index][1]))
        return skeletonString +'|'


    
               
    # Vrati pozici konkretni kosti.
    # jointId (input) - jmeno hledane kosti (se seznamu nameList)
    # scale (input) - True: skalovane vuci velikosti okna, False: neskalovane
    def findJoint (self,jointId,scaled=True):
        frame = self.kinect.skeleton_engine.get_next_frame()       
        idPlayer = self.findPlayer()
        if not idPlayer==-1:
            position = frame.SkeletonData[idPlayer].SkeletonPositions[self.nameList.index(jointId)]
            if scaled == False:                       
                    joint = [position.x,position.y,position.z]
            else:
                scaled = nui.SkeletonEngine.skeleton_to_depth_image(position, self.width, self.height)
                joint = [scaled[0],scaled[1],position.z]
        else:
            joint = [1.0,1.0,1.0]

        bone = [jointId,joint]
        return bone
        
    
    # Vrati celou kostru v seznamu.
    # scale (input) - True: skalovane vuci velikosti okna, False: neskalovane
    def getSkeleton (self,frame,scaled=True):
        skeletList = range(len(self.nameList)*2)
        idPlayer = self.findPlayer()

        
        for index in range(len(self.nameList)*2):  
            if index%2 == 0:
                  skeletList[index] = self.nameList[index/2]
            if index%2 == 1 and not idPlayer==-1:
                position = frame.SkeletonData[idPlayer].SkeletonPositions[int(round(index/2))]
                if scaled == False:                       
                       skeletList[index] = [position.x,position.y,position.z]
                else:
                    scaled = nui.SkeletonEngine.skeleton_to_depth_image(position, self.width, self.height)
                    skeletList[index] = [scaled[0],scaled[1],position.z]
            if index%2 == 1 and idPlayer==-1:
                skeletList[index] = [1.0,1.0,1.0]
            
        return skeletList

    # Ukonci spojeni s Kinectem #
    def destroy(self):
        self.kinect.close()
