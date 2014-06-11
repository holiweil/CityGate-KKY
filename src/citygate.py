''' 
Modul citygate definuje vlastni rozhrani pomoci tridy Game. Dale definuje stavove promenne
(tridy State a StateMod), zajistuje jejich prenos mezi serverem a klienty a obsahuje
hlavni smycku programu.

Autor: Jakub Vit + Jan Holecek
'''


import enet
import sys, getopt, time, string, random
from pprint import pprint
import pickle

import thread
from videostream import *
from parameters import *


'''Definuje tri mody, ve kterych se muze (z pohledu konretni entity)
stav nachazet. '''
class StateMode:
	SERVER = 1
	CLIENT_LOCAL = 2
	CLIENT_REMOTE = 3


''' Trida definuje strukturu, ve ktere jsou uchovavany stavove promenne
a operace s temito strukturami.'''
class State(object):
	def __init__(self, mode):
		self.mode = mode
		self.values = {}

	''' Vytvoreni nove stavove promenne.'''
	def addParam(self, name, type = 'float', ownedByServer = True, defaultValue = 0):
		owner = False	
		if (ownedByServer and self.mode == StateMode.SERVER) or (not ownedByServer and self.mode == StateMode.CLIENT_LOCAL):
			owner = True
		self.values[name] = {
			'value': defaultValue,
			'type': type,
			'owner': owner
		}

        ''' Deserializace  dat '''
	def updateFromPacket(self, str):
		d = pickle.loads(str)
		for i in self.values:
			if self.values[i]['owner'] == True:
				continue			
			val = self.values[i]['value']
			t = self.values[i]['type']
			if t == 'float':
				val = float(val)
			if not i in d:
				print "Key does not exist"
				print d
			self.values[i]['value'] = d[i]['value']		

	''' Serializace  dat '''	
	def formatPacket(self):
		data = {}
		for i in self.values:
			data[i] = {
				'value': self.values[i]['value']
			}	
		packetData = pickle.dumps(data)		
		return packetData

	def __str__(self):
		s = ""
		for i in self.values:
			s += str(i) + ":" + str(self.values[i]['value']) + ";"
		return s
 
	def __getitem__(self, index):
		return self.values[index]['value']

	def __setitem__(self, key, value):
		if not key in self.values:
			print "Key does not exist"
			print self.values
		self.values[key]['value'] = value

''' Abstraktni trida definujici samotne rozhrani. '''	
class Game(object):
	def name(self):
		raise NotImplementedError()
	def author(self):
		raise NotImplementedError()
	def version(self):
		raise NotImplementedError()
	def createGameState(self, state):
		raise NotImplementedError()
	def updateGameState(self, state, playerState, client):
		raise NotImplementedError()
	def createPlayerState(self, playerId, state, gameState):	
		raise NotImplementedError()
	def updatePlayerState(self, state, delta):
		raise NotImplementedError()
	def handleUserInput(self, playerState, gameState, client):
		raise NotImplementedError()
	def createGUI(self):
		raise NotImplementedError()
	def serverIni(self):
		raise NotImplementedError()
	def render(self):
		raise NotImplementedError()
	def videoIn(self):
		raise NotImplementedError()
	def videoOut(self,videoString):
		raise NotImplementedError()
	
''' Trida definuje hlavni smycku programu v metode run().'''
class ClientServer(object):
	def __init__(self, game, isServer):
		self.players = {} #Uchovava stavove promenne vsech klientu.
		self.gameState = None # Uchovava stavove promenne serveru.
		self.game = game
		self.localTime = -1
		self.timeDelta = 0
		self.isServer = isServer
		self.clientId = None
		self.clientConnected = False	
		
		

	def onClientConnect(self, peer):
		pass
	def onClientDisconnect(self, peer):
		pass
	def onMessageRecieved(self, msg):
		pass
	def sendData(self):		
		pass
	def updatePlayers(self, delta):
		for i, s in self.players.iteritems():
			self.game.updatePlayerState(s, self.clientId, self.gameState, delta)
                        self.game.updateGameState(self.gameState, s, self, delta)

	def debugPrint(self):
		print('................')
		for i, s in self.players.iteritems():
			if i == self.clientId:
				print('>'),
			else:
				print(' '),
			print(i, str(s))
		print('.',str(self.gameState))

	

        
        ''' Metoda obsahujici hlavni smycku programu.'''
	def run(self):
		if self.isServer:
                        #Vytvoreni stavovych promennych.
			self.gameState = self.game.createGameState(StateMode.SERVER)

			#Vytvoreni video serveru.                    
                        self.server.start()
                        
		else:
                        #Vytvoreni stavovych promennych.
			self.gameState = self.game.createGameState(StateMode.CLIENT_REMOTE)

			#Vytvoreni video klienta.                
                        self.client.start()
                        
		start = time.clock()
		self.localTime = 0
		lastLocalTime = 0
		debugCounter = 0
		if not self.isServer:
			self.game.createGUI()
		if self.isServer:
			self.game.serverIni()
			
		##HLAVNI SMYCKA PROGRAMU##	
		while True:                    
			lastLocalTime = self.localTime			
			self.localTime = time.clock() - start	
			self.delta = self.localTime - lastLocalTime		
			self.updatePlayers(self.delta)			
			while True:
				event = self.host.service(0)
				if event == None:
					break
				elif event.type == enet.EVENT_TYPE_CONNECT:#Udalost pripojeni klienta.
					self.onClientConnect(event.peer)
				elif event.type == enet.EVENT_TYPE_DISCONNECT:#Udalost odpojeni klienta.
					self.onClientDisconnect(event.peer)
				elif event.type == enet.EVENT_TYPE_RECEIVE:#Udalost obdrzeni dat.
					msg = pickle.loads(event.packet.data)
					self.onMessageRecieved(msg)
			if not self.isServer and self.clientId != None:
				self.game.handleUserInput(self.players[self.clientId],self.gameState,self)
			self.sendData()
			
			debugCounter += self.delta
			
			if self.isServer and debugCounter > 0:
##				self.debugPrint()
				debugCounter = 0
				
			self.host.flush()
			if not self.isServer and self.clientId != None:
				self.game.render(self)
				
				#Vstup videa
				if VideoClient.videoIn.empty():
                                        VideoClient.videoIn.put(self.game.videoIn())
                                        
			if not self.isServer and self.clientId != None:

                                #Vystup videa
                                if not VideoClient.videoOut.empty():
                                        self.game.videoOut(VideoClient.videoOut.get())
                                pass
                        time.sleep(0.01)
                       
''' Trida dedici od tridy ClientServer definuje vytvoreni serveru a komunikaci s klienty.'''
class GameServer(ClientServer):
	def __init__(self, game):
		super(GameServer,self).__init__(game, True)

        ''' Vytvoreni serveru.'''
	def create(self, args):
                ap = getParam('address')
		if ap=='':
                       ipAddress = '127.0.0.1'
                else:
                        ipAddress = ap

                pp = getParam('port')
		if pp=='':
                       port = 667
                else:
                        port = pp
           
		self.host = enet.Host(enet.Address(ipAddress, port), 16, 0, 0, 0)
		print "Game server started ..."

		self.server = VideoServer(ipAddress)

        ''' Pripojeni noveho klienta.'''
	def onClientConnect(self, peer):
		clientId = int(peer.incomingPeerID)
		print "New client connected", clientId
		self.players[clientId] = self.game.createPlayerState(StateMode.SERVER)

        ''' Odpojeni klienta'''
	def onClientDisconnec(tself, peer):
		clientId = int(peer.incomingPeerID)
		print "players disconnected", clientId
		del self.players[clientId]

        ''' Obdrzeni dat.'''
	def onMessageRecieved(self, msg):
		if msg['action'] == 'player_update':
			clientId = int(msg['clientId'])						
			self.players[clientId].updateFromPacket(msg['state'])
		if msg['action'] == 'game_update':
			self.gameState.updateFromPacket(msg['state'])
			
        ''' Odeslani dat.'''
	def sendData(self):
		for i, s in self.players.iteritems():
			msg = pickle.dumps({
					'action': 'player_update',
					'clientId': str(i),
					'state': s.formatPacket()
				});
			packet = enet.Packet(msg,3)
			
                        #Odeslani vsech klientskych stavovych promennych vsem klientum.
			self.host.broadcast(0, packet)
			
		
		msg = pickle.dumps({
				'action': 'game_update',
				'time': self.localTime,
				'state': self.gameState.formatPacket()
		});
		packet = enet.Packet(msg,3)
		#Odeslani serverovych stavovych promennych vsem klientum.
		self.host.broadcast(0, packet)
                

	def stop(self):
		print "Stopping server ..."
		self.server.stop()
                self.server.sock.close()
                self.server.join()
                
''' Trida dedici od tridy ClientServer definuje vytvoreni klienta a komunikaci se serverem.'''
class GameClient(ClientServer):
	def __init__(self, game):
		super(GameClient,self).__init__(game, False)

        ''' Vytvoreni klienta'''
	def create(self, args):

		ap = getParam('address')
		if ap=='':
                       ipAddress = '127.0.0.1'
                else:
                        ipAddress = ap

                pp = getParam('port')
		if pp=='':
                       port = 667
                else:
                        port = pp

                print self.clientConnected
		self.host = enet.Host(None, 32, 2, 0, 0)
		self.peer = self.host.connect(enet.Address(ipAddress, port), 1)
		print "Game client connecting to " + ipAddress + ":" + str(port)	
                self.client = VideoClient(ipAddress)

        ''' Pripojeni klienta.'''
	def onClientConnect(self, peer):
		self.clientConnected = True
		self.clientId = peer.outgoingPeerID	
		self.players[self.clientId] = self.game.createPlayerState(StateMode.CLIENT_LOCAL)
		print "Client connected with id=" + str(self.clientId)

        ''' Odpojeni klienta.'''
	def onClientDisconnect(self, peer):
		pass

        ''' Odeslani dat serveru.'''
	def sendData(self):
		if self.clientId != None:
			s = self.players[self.clientId]
			msg = pickle.dumps({
					'action': 'player_update',
					'clientId': str(self.clientId),
					'state': s.formatPacket()
				});
			packet = enet.Packet(msg,3)
			self.peer.send(0, packet)
			
        ''' Obdrzeni dat.'''
	def onMessageRecieved(self, msg):
		if msg['action'] == 'player_update':
			clientId = int(msg['clientId'])						
			if not clientId in self.players:
				self.players[clientId] = self.game.createPlayerState(StateMode.CLIENT_REMOTE)				
			self.players[clientId].updateFromPacket(msg['state'])	
		if msg['action'] == 'game_update':
			self.gameState.updateFromPacket(msg['state'])
			
	def stop(self):                
		if self.clientId != None:
			print "Discconnecting client ..."
        	self.peer.disconnect()
        	self.host.service(0)
        	self.host.flush()
        	

def printHelp():
	print "usage: python citygate.py gameModule mode [gameArgs]"

''' Metoda vytvarejici instance GameServer nebo GameClient'''	
def runGame(game):

        ''' Kontroluje prvni argument pri spusteni z CMD'''       
	if len(sys.argv) < 2:
		print >> sys.stderr, "Missing mode parameter"
		printHelp()
		sys.exit(1)
				
	if sys.argv[1] != "client" and sys.argv[1] != "server":
		print "Unknown mode option (either 'server' or 'client')"
		sys.exit(1)
			
	if sys.argv[1] == "server":
		isServer = True
	else:
		isServer = False
			
	print ""
	print "-------------------------------------------"
	print " " + game.name() + " (" + game.version() + ") by " + game.author()
	print "-------------------------------------------"
	print ""
	
	if isServer:
		gameObj = GameServer(game)
	else:
		gameObj = GameClient(game)
		
	gameObj.create(sys.argv[2:])
	try:
                
		gameObj.run()
	except KeyboardInterrupt:
		gameObj.stop()
	
	
