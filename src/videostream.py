'''
Soubor videotrack.py zahrnuje tridu ManagingClient pro komunikaci videoserveru
s jednotlivymi (video)klienty, tridu VideoServer pro vytvoreni videoserveru
a odchytavani klientu a tridu VideoClient pro tvorbu techto klientu.
Trida umi spravovat vice nez dva klienty, ale routovani videa je vyreseno pouze
pro dva (klient 0 a klient 1),
Autor: Jan Holecek
'''
import time, sys, cv2
import Queue
import threading
import socket
import msvcrt


'''Vystupni fronty pro dva klienty.'''
videoFrom0 = Queue.Queue()
videoFrom1 = Queue.Queue()


'''
Trida pro spravu odchytnutych klientu vytvorena v novem vlakne.
'''
class ManagingClient(threading.Thread):
    buffersize = 1024000 #Minimalne velka jako velikost dat.
    timeOld = 0

    def __init__ (self,conn,idClient):
        threading.Thread.__init__(self)
        self.conn = conn
        self.idClient = idClient

    def run(self):
        while True:
            time.sleep(0.01)# Z duvodu uvolneni fronty pro ostatni vlakna.    
            timeCurr=time.time()
            timeDiff = timeCurr - self.timeOld
            
            #Klient 0
            if self.idClient == 0:
                while True:
                    timeCurr=time.time()
                    timeDiff = timeCurr - self.timeOld  
                    if not videoFrom1.empty():
                        #Odeslani dat od klienta 1 klientu 0.
                        self.conn.send(videoFrom1.get())
                        break
                    if  timeDiff > 0.01:
                        #V pripade zadnych dat od klienta 1 odeslani 'prazdneho' retezce.
                        self.conn.send('empty')
                        break
                #Prijem dat od klienta 0
                data = self.conn.recv(self.buffersize)
                if videoFrom0.empty():
                    videoFrom0.put(data)
                    
            #Klient 1
            elif self.idClient == 1:
                while True:
                    timeCurr=time.time()
                    timeDiff = timeCurr - self.timeOld  
                    if not videoFrom0.empty():
                        #Odeslani dat od klienta 0 klientu 1.
                        self.conn.send(videoFrom0.get())
                        break
                    if  timeDiff > 0.01:
                        #V pripade zadnych dat od klienta 1 odeslani 'prazdneho' retezce.
                        self.conn.send('empty')
                        break
                #Prijem dat od klienta 1 
                data = self.conn.recv(self.buffersize) 
                if videoFrom1.empty():
                    videoFrom1.put(data)

            self.timeOld=time.time()   




'''
Trida pro vytvoreni videoserveru a odchyt klientu.
'''
class VideoServer(threading.Thread):
    host = ''  
    port = 52000
    idClient = 0
    sock = 0
    conn = ''
    addr = ''
    bufferSize = 1024000 #Minimalne velka jako velikost dat.
    threads = []
    
    
    def __init__(self,host='127.0.0.1',port=52000):
        threading.Thread.__init__(self)
        self.go = True
        self.host = host
        self.port = port

        #Vytvoreni TCP serveru
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#TCP
        self.sock.bind((host, port))
        print 'tcp server starting...'
        print 'tcp server: ip: ' + host
        self.sock.listen(5) #Parametr znaci maximalni pocet pripojenych klientu.
     
     
    #Metoda pro odchyt klientu. Musi byt spustena v samostatnem vlakne.
    def run(self):
        while True:
            
            if not self.go:
                print "tcp server: stoping..."
                break
            print 'tcp server: waitting for client...'
            self.conn, self.addr = self.sock.accept()
            print 'tcp server: found new client with id ' + str(self.idClient)
            thread = ManagingClient(self.conn, self.idClient)
            thread.daemon = True
            thread.start()
            self.threads.append(thread)    
            self.idClient += 1
            

    #Zruseni serveru.        
    def stop(self):
        self.go = False
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((self.host, self.port))
        self.sock.close()

        


'''
Trida vytvyrejici klienty a zajistujici odesilani obrazovych dat na server
'''
class VideoClient(threading.Thread):
    host='localhost'
    port = 52000
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#TCP
    buffersize = 1024000#Minimalne velka jako velikost dat.

    #Fronta pro data, ktera jsou odesilana druhemu klientovi.
    videoIn = Queue.Queue()

    #Fronta pro data, od druheho klienta.
    videoOut = Queue.Queue()


    def __init__(self,host='127.0.0.1',port=52000):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.sock.connect((host, port))#Vytvoreni spojeni
        print ('host',self.host)
        print ('port',self.port)

    def run(self):
        while True:
            time.sleep(0.04)
            imgStr = 'empty'
            
            #Obdrzeni dat od druheho klienta.
            imgStr = self.sock.recv(self.buffersize)
            if self.videoOut.empty():
                self.videoOut.put(imgStr)

            
            if not self.videoIn.empty():         
                imgStr = self.videoIn.get()
            else:
                imgStr= 'empty'
                
            #Obdrzeni dat od druheho klienta
            self.sock.send(imgStr)
        
            if cv2.waitKey(10) == 27:
                 break

     
        self.sock.close()
