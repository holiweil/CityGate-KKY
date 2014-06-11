'''
Hra Dots pro dva hrace vyuzivajici rozhrani citygate.

Autor: Jan Holecek
'''
import os, sys, time, getopt, msvcrt, math, random
import pickle
import StringIO 

import pygame
from pygame.locals import *

import Image
import cv2
import numpy

import citygate
from sensors import *
from parameters import *



class TestGame(object):
        
        def __init__(self):
                self.isKinect = 1
               
	def name(self):
		return "Dot Game"
	def author(self):
		return "Jan Holecek + Jakub Vit"
	def version(self):
		return "0.5 beta"
	def serverIni(self):
            self.dots = []
            self.nextDot = True
            self.oldLeftHand0 = [0,0]
            self.oldRightHand0 = [0,0]
            self.maxDots = 7
            self.roundTime = 30
            self.oldTime=time.time()           
            self.oldId = 0
            
	''' Vytvoreni servovych stavovych promennych'''
	def createGameState(self, mode):		
		state = citygate.State(mode)
                state.addParam('timeS', 'float')#Hlavni cas hry.
                state.addParam('dotsS', 'list')#Pozice a zbyvajici cas kolecek.
                state.addParam('attackerS', 'int')#ID hrace, ktery utoci.

		return state

        '''Zjisti, zda byl proveden dotyk v okoli kolecka'''
	def isDot(self,dot,dotList):
                border = 40 
                find = -1
                for index in range(len(dotList)):
                        if not dot==0:
                                if dot[0]>dotList[index][0][0]-border and dot[0]<dotList[index][0][0]+border and dot[1]>dotList[index][0][1]-border and dot[1]<dotList[index][0][1]+border:
                                        find = index
                                        break
                return find
                                        
                
	def updateGameState(self, state, playerState, client, delta):                    
                #Pouze server
                if client.isServer==True:
                        
                        self.dotsOut = []#Vystupni seznam kolecek

                        #Ochrana pri vymene roli
                        if self.roundTime<(time.time() - self.oldTime + 1):
                                for i,p in client.players.iteritems():
                                        if state['attackerS'] == i:
                                                self.oldLeftHand0 = p['handleftC']
                                                self.oldRightHand0 = p['handrightC']
                                self.oldId = state['attackerS']

                        
                        
                        #Ulozeni novych pozic dlani, ktere jsou priblizeny ke Kinectu
                        for i,p in client.players.iteritems():
                                if state['attackerS'] == i:     
                                        if len(self.dots)< self.maxDots and not p['handleftC'] == 0 and not p['handleftC'] == [0,0] and not p['handleftC'] == self.oldLeftHand0:
                                                self.dots.append([p['handleftC'],time.time()])
                                                self.oldLeftHand0 = p['handleftC']
                                                print 'pridavam levou'

                                        if len(self.dots)< self.maxDots and not p['handrightC'] == 0 and not p['handrightC'] == [0,0] and not p['handrightC'] == self.oldRightHand0:
                                                self.dots.append([p['handrightC'],time.time()])
                                                self.oldRightHand0 = p['handrightC']
                                                print 'pridavam pravou'                                        
                                pass
                        


                        #Vytvoreni seznamu kolecek pro klienty
                        for index in range(len(self.dots)):
                                pos = self.dots[index][0]
                                timeStamp = 3

                                #Nove casove znamky
                                timeDif = time.time() - self.dots[index][1]
                                if timeDif >0 and timeDif < 2 :
                                        timeStamp = 0
                                if timeDif > 2 and timeDif < 3 :
                                        timeStamp = 1
                                if timeDif >3 :
                                        timeStamp = 2
                                self.dotsOut.append([pos,timeStamp]) 




                        #Smazani odchycenych kolecek
                        for i,p in client.players.iteritems():
                                if not state['attackerS'] == i:
                                        if not p['handleftC'] == 0:
                                                if not self.isDot(p['handleftC'],self.dotsOut)==-1:
                                                        self.dots.remove(self.dots[self.isDot(p['handleftC'],self.dotsOut)])
                                                        p['scoreCS']+=1
                                        if not p['handrightC'] == 0:
                                                if not self.isDot(p['handrightC'],self.dotsOut)==-1:
                                                        self.dots.remove(self.dots[self.isDot(p['handrightC'],self.dotsOut)])
                                                        p['scoreCS']+=1
                                                        
                        #Rozhodnuti o roli jednotlivych klientu
                        state['timeS'] = round(self.roundTime-(time.time() - self.oldTime))
                        if self.oldTime + self.roundTime  < time.time():
                                if state['attackerS'] == 0:
                                        state['attackerS'] = 1
                                        self.oldTime = time.time()
                                        
                                else:
                                        state['attackerS'] = 0
                                        self.oldTime = time.time()
                                        
                        #Smazani starych kolecek
                        for index in range(len(self.dots)): 
                                if time.time() - self.dots[index][1] >4:
                                        for i,p in client.players.iteritems():
                                                if state['attackerS'] == i:
                                                        p['scoreCS']+=1
                                        self.dots.remove(self.dots[index])
                                        index = 0
                                        break
                                
                        state['dotsS'] = self.dotsOut

                
                
                
	def createPlayerState(self, mode):
		state = citygate.State(mode)
		state.addParam('handleftC', 'list',False)#Leva dlan hrace
		state.addParam('handrightC', 'list',False)#Prava dlan hrace
		state.addParam('scoreCS', 'int',True)#Skore gracu

		return state
	
	def updatePlayerState(self, state, playerId, gameState, delta):


                #Pouze klienti
                if not playerId == None:
                        
                        if not self.changingId == gameState['attackerS']:
                                        self.handLeft== [0,0]
                                        self.handRight== [0,0]                                     
                                        self.changingId = gameState['attackerS']
                                        
                        #Utocnik
                        if playerId == gameState['attackerS']:                            
                                #Ovladani Kinectem
                                if self.isKinect == 1:
                                        if gameState['timeS']>0:

                                                #Leva dlan
                                                if self.hlava[2]-self.leva[2]>400 and self.nextDotLC:
                                                        self.timeNextPut = time.time()
                                                        self.handLeft = [self.leva[0],self.leva[1]]                                                  
                                                        self.nextDotLC = False
                                                        
                                                if not self.hlava[2]-self.leva[2]>400 and not self.nextDotLC and (time.time() - self.timeNextPut) > 0.5:
                                                        self.nextDotLC = True

                                                if not self.handLeft==0:
                                                        state['handleftC'] = self.handLeft
                                                
                                                #Prava dlan
                                                if self.hlava[2]-self.prava[2]>400 and self.nextDotRC:
                                                        self.timeNextPut = time.time()
                                                        self.handRight = [self.prava[0],self.prava[1]]
                                                        self.nextDotRC = False
                                                        
                                                if not self.hlava[2]-self.prava[2]>400 and not self.nextDotRC and (time.time() - self.timeNextPut) > 0.5:
                                                        self.nextDotRC = True
                                                state['handrightC'] = self.handRight

                                                
                                        else:#Pojistka pri vymene roli
                                                state['handleftC'] = [0,0]                                              
                                                state['handrightC'] = [0,0]
                                                

                                # Ovladani mysi
                                elif self.isKinect == 0:
                                        state['handleftC'] = self.mouseDot                                     
                                        if pygame.mouse.get_pressed()[0] ==1 and self.nextDotC:
                                                self.mouseDot = [self.mouse[0],self.mouse[1]]
                                                self.nextDotC = False
                                        if not pygame.mouse.get_pressed()[0] ==1 and not self.nextDotC and (time.time() - self.timeNextPut) > 0.5:
                                                self.nextDotC = True
                                

                        #Obrance
                        else:                     
                                #Ovladani Kinectem
                                if self.isKinect == 1:
                                        if gameState['timeS']>0:        
                                                state['handleftC'] = [self.leva[0],self.leva[1]]                                         
                                                state['handrightC'] = [self.prava[0],self.prava[1]]
                                        else:
                                                state['handleftC'] = [0,0]                                               
                                                state['handrightC'] = [0,0]
                                        


                                #Ovladani mysi
                                if self.isKinect == 0:
                                        state['handleftC'] = self.mouseDot                                    
                                        if pygame.mouse.get_pressed()[0] ==1 and self.nextDotC:
                                                self.mouseDot = [self.mouse[0],self.mouse[1]]
                                                self.nextDotC = False
                                        if not pygame.mouse.get_pressed()[0] ==1 and not self.nextDotC and (time.time() - self.timeNextPut) > 0.5:
                                                self.nextDotC = True
                                
                

                      
                  
        ''' Vytvoreni herniho GUI a potrebnych promennych.'''
	def createGUI(self):

                #Inicializtece PyGame
                self.WINSIZE = 1280, 720
                self.VIDEOSIZE = 640, 480
        
                pygame.init()
                self.fpsClock = pygame.time.Clock()
                self.screen = pygame.display.set_mode(self.WINSIZE,0,32)    
                pygame.display.set_caption('Test game')

                # Mys 
                pygame.mouse.set_visible(False)
                

                # Casove promenne
                self.timeNextPut = 0.0

                # Herni promenne
                self.nextDotC = True #mouse
                self.nextDotLC = True #left hand kinect
                self.nextDotRC = True #right hand kinect
                self.mouseDot = [0,0]
                self.handLeft = [0,0]
                self.handRight = [0,0]
                self.changingId = 0

                # Zakladni grafika 
                self.mask = pygame.image.load('img/mask.png')
                self.handblue = pygame.image.load('img/handblue.png')
                self.handred = pygame.image.load('img/handred.png')
                
                self.dotgreen = pygame.image.load('img/dotgreen.png')
                self.dotorange = pygame.image.load('img/dotorange.png')
                self.dotpurple = pygame.image.load('img/dotpurple.png')
                

                self.nocamImg = pygame.image.load('img/novideo.png')
                self.videoImage = self.nocamImg
                self.isVideo = False

                # Grafika hracova skore
                self.scoreFont = pygame.font.SysFont("04b03", 50)
                self.scoreText = self.scoreFont.render(" ", 0, (0, 150, 255))
                self.scoreTextpos = self.scoreText.get_rect()
                self.scoreTextpos.centerx = self.screen.get_rect().centerx

                # Grafika protihracovo skore 
                self.oscoreFont = pygame.font.SysFont("04b03", 50)
                self.oscoreText = self.oscoreFont.render(" ", 0, (0, 150, 255))
                self.oscoreTextpos = self.oscoreText.get_rect()
                self.oscoreTextpos.centerx = self.screen.get_rect().centerx

                # Grafika textoveho pole 
                self.infoFont = pygame.font.SysFont("04b03", 70)
                self.infoText = self.infoFont.render(" ", 0, (0, 150, 255))
                self.infoTextpos = self.infoText.get_rect()
                self.infoTextpos.centerx = self.screen.get_rect().centerx

                # Grafika casoveho udaje 
                self.timeFont = pygame.font.SysFont("04b03", 100)
                self.timeText = self.timeFont.render(" ", 0, (0, 150, 255))
                self.timeTextpos = self.timeText.get_rect()
                self.timeTextpos.centerx = self.screen.get_rect().centerx
                

                # Inicializace Kinectu 
                self.hlava = [0,0,0]
                self.hlavaSize = 100
                self.leva = [0,0,0]
                self.prava = [0,0,0]

                kp = getParam('kinect')
		if kp=='':
                       self.isKinect = 1
                else:
                        self.isKinect = kp

                if self.isKinect == 1:
                        self.kinect = KinectTrack()
                        self.kinect.startVideo()
                        self.kinect.startSkeleton()
                        self.kinect.setElevation(7)
                        
                        self.kinect.width = self.WINSIZE[0]
                        self.kinect.height = self.WINSIZE[1]

                        
                else:
                        self.kam = Kamera()
                        self.kam.loadKamera()


        ''' Funkce pro urceni offsetu pri vyrezu hlavy.'''
        def cropHead(self,headB,offset,image):
                
                head=[0,0]
                head[0] = int((float(headB[0])/self.WINSIZE[0])*self.VIDEOSIZE[0])
                head[1] = int((float(headB[1])/self.WINSIZE[1])*self.VIDEOSIZE[1])
               
                # Horti offset
                top = head[1]

                # Levy offset
                if not head[0] - offset[0] < 1:left = head[0] - offset[0]
                else: left = 0

                # Pravy offset
                if not head[0] + offset[2]> self.WINSIZE[0]-1:right = head[0] + offset[2]
                else: right = self.WINSIZE[0]-1

                # Spodni offset
                if not head[1] + 2*offset[3] > self.WINSIZE[1]-1:bottom = head[1] + 2*offset[3]
                else: bottom = self.WINSIZE[1]-1


                if top<0: top=0
                if left<0: left=0
                if right>self.WINSIZE[0]-1: right=self.WINSIZE[0]-1
                if bottom>self.WINSIZE[1]-1: right=self.WINSIZE[1]-1
                
                image = image[top:bottom,left:right]
                return image
                
        
        '''Odeslani obrazovych dat'''
        def videoIn(self):
                videoString = 'empty'

                #Kinect
                if self.isKinect == 1:
                        if not self.kinect.videoQ.empty():
                                if not self.hlava[0] == 0:
                                        img = self.kinect.videoQ.get()

                                        # Urceni hranice pro vyriznuti hlavy (ruzne Kinecty)
                                        if getParam('idkinect')==1:
                                                offset = [int(70000/self.hlava[2])+25,int(70000/self.hlava[2]),int(70000/self.hlava[2])-25,int(70000/self.hlava[2])]
                                        else:
                                                offset = [int(70000/self.hlava[2]),int(70000/self.hlava[2]),int(70000/self.hlava[2]),int(70000/self.hlava[2])]

                                        # Vyriznuti hlavy pro ruzne Kinecty
                                        img = self.cropHead(self.hlava,offset,img)
                                        img = cv2.resize(img, (self.hlavaSize,self.hlavaSize), 0, 0, interpolation = cv2.INTER_LINEAR)
                                        videoString = saveJpegToMemory(img,100,1)

                #Webova kamera
                else:
                        img = self.kam.getImage()
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        img = img[int(img.shape[0]/2)-50:int(img.shape[0]/2)+50,int(img.shape[1]/2)-50:int(img.shape[1]/2)+50]
                        videoString = saveJpegToMemory(img,100,1)

                return videoString

        '''Zpracovani prichozich obrazovych dat'''
        def videoOut(self,videoString):
                if sys.getsizeof(videoString)>100:#Pojistka proti malym datum neobsahujici obraz                        
                        img = makeCvImageFromMemory(videoString)
                  
                        try:
                                # Predzpracovani prichoziho obrazu
				img = cv2.bilateralFilter(img,9,75,75) #Rozostreni
                                tmp = cv2.GaussianBlur(img,(5,5),5)#Doostreni
                                cv2.addWeighted(img, 1.5, tmp, -0.5, 0, img)#Doostreni
                                
                                self.videoImage = pygame.image.frombuffer(img.tostring(), (100,100),"RGB")
                                self.isVideo = True
                        except pygame.error, message:
                                pass
                        
        '''Vykresleni'''        
	def render(self, client):
                self.screen.fill((255,255,255))
                self.serverDots = client.gameState['dotsS']

                try:

                        # Vykresleni casu
                        if client.gameState['timeS'] > 3:
                                self.timeText = self.timeFont.render(str("{0:.0f}".format(client.gameState['timeS'])), 0, (210, 210, 210))
                        else:
                                self.timeText = self.timeFont.render(str("{0:.0f}".format(client.gameState['timeS'])), 0, (240, 150, 150))
                        self.timeTextpos = self.timeText.get_rect()
                                        
                        self.timeTextpos.centerx = self.screen.get_rect().centerx
                        self.timeTextpos.centery = 220
                        self.screen.blit(self.timeText, self.timeTextpos)
                                        
                        # Vykresleni videa od protihrace
                        if self.isVideo:
                                self.screen.blit(self.videoImage,(self.WINSIZE[0]/2-self.hlavaSize/2-5,self.WINSIZE[1]/2-self.hlavaSize/2))
                                self.screen.blit(self.mask,(self.WINSIZE[0]/2-55,self.WINSIZE[1]/2-50))
                        else:
                                self.screen.blit(self.nocamImg,(self.WINSIZE[0]/2-55,self.WINSIZE[1]/2-50))


                        # Vykresleni hracova skore
                        for i,p in client.players.iteritems():
                                if i==client.clientId: 
                                        self.scoreText = self.scoreFont.render(str(p['scoreCS'])+" ", 0, (112, 217, 9))
                                        self.scoreTextpos = self.scoreText.get_rect()
                                        
                                        self.scoreTextpos.centerx = self.screen.get_rect().centerx - int(self.scoreText.get_rect()[2]/2)
                                        self.scoreTextpos.centery = 550
                                        self.screen.blit(self.scoreText, self.scoreTextpos)

                        # Vykresleni protihracova skore
                        for i,p in client.players.iteritems():
                                if not i==client.clientId:
                                        self.oscoreText = self.oscoreFont.render(" " + str(p['scoreCS']), 0, (217, 9, 53))
                                        self.oscoreTextpos = self.oscoreText.get_rect()
                                        
                                        self.oscoreTextpos.centerx = self.screen.get_rect().centerx + int(self.oscoreText.get_rect()[2]/2)
                                        self.oscoreTextpos.centery = 550
                                        self.screen.blit(self.oscoreText, self.oscoreTextpos)

                        # Vykresleni prikazu hraci
                        if client.gameState['attackerS']==client.clientId:
                                self.infoText = self.infoFont.render("MAKE POINTS!!", 0, (0, 150, 255))
                        else:
                                self.infoText = self.infoFont.render("CATCH POINTS!!", 0, (0, 150, 255))
                        self.infoTextpos = self.infoText.get_rect()
                        self.infoTextpos.centerx = self.screen.get_rect().centerx
                        self.infoTextpos.centery = 500
                        self.screen.blit(self.infoText, self.infoTextpos)
                                
                        # Vykresleni kolecek
                        if not self.serverDots==0:
                                for index in range(len(self.serverDots)):
                                        dot = self.dotgreen
                                        if self.serverDots[index][1]==0:
                                                dot = self.dotgreen
                                        if self.serverDots[index][1]==1:
                                                 dot = self.dotorange
                                        if self.serverDots[index][1]==2:
                                                dot = self.dotpurple
                                        self.screen.blit(dot,(int(self.serverDots[index][0][0]),int(self.serverDots[index][0][1])))

                        #Leva dlan
                        if self.isKinect == 1 and self.leva[0]>0:
                                if self.hlava[2]-self.leva[2]<400:#Dostatecne rozdil mezi vzdalenosti hlavy od dlane v ose z.
                                        self.screen.blit(self.handblue,(self.leva[0],self.leva[1]))
                                else: 
                                        if(client.gameState['attackerS']==client.clientId):
                                                self.screen.blit(self.handred,(self.leva[0],self.leva[1]))
                                        else:
                                                self.screen.blit(self.handblue,(self.leva[0],self.leva[1]))
                                        
                        #Prava dlan
                        if self.isKinect == 1 and self.prava[0]>0:
                                if self.hlava[2]-self.prava[2]<400:#Dostatecne rozdil mezi vzdalenosti hlavy od dlane v ose z.
                                        self.screen.blit(self.handblue,(self.prava[0],self.prava[1]))
                                else:
                                        if(client.gameState['attackerS']==client.clientId):
                                                self.screen.blit(self.handred,(self.prava[0],self.prava[1]))
                                        else:
                                                self.screen.blit(self.handblue,(self.prava[0],self.prava[1]))
                        #Mys
                        if self.isKinect == 0:
                                self.mouse = pygame.mouse.get_pos()
                                self.screen.blit(self.handblue,(self.mouse[0],self.mouse[1]))# Zobrazeni pozice mysi.
                                for event in pygame.event.get():
                                        if event.type == pygame.MOUSEBUTTONDOWN and self.nextDotC:# Stisknuti leveho tlacitka mysi.
                                                self.screen.blit(self.handred,(self.mouse[0],self.mouse[1]))

                        
                                        
                                        
                except pygame.error, message:
                        pass
                

                # Zisk pozice hlavy a dlani hrace
                if self.isKinect == 1: 
                        if not self.kinect.skeletonQ.empty():
                                skelet = self.kinect.skeletonQ.get()
                                self.hlava[0] = int(skelet[7][0])
                                self.hlava[1] = int(skelet[7][1])
                                self.hlava[2] = int(skelet[7][2]*1000)

                                self.leva[0] = int(skelet[15][0])
                                self.leva[1] = int(skelet[15][1])
                                self.leva[2] = int(skelet[15][2]*1000)

                                self.prava[0] = int(skelet[23][0])
                                self.prava[1] = int(skelet[23][1])
                                self.prava[2] = int(skelet[23][2]*1000)
                        else:
                                skelet = 0
                

                
                pygame.display.update()
                self.fpsClock.tick(30)



                
		
			
	def handleUserInput(self, playerState, gameState, client):
                events = pygame.event.get()
                for event in events:
                        if event.type == QUIT or event.type == KEYDOWN:
                            sys.exit(0)
                pass
                            
                                
                                
		

if __name__ == "__main__":
        #Spusteni rozhrani#
	myGame = citygate.runGame(TestGame())
