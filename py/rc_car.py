
import socket
import serial
import cStringIO as StringIO
from VideoCapture import Device
import time
import threading
import socket
from struct import pack
import pygame
pygame.init()

gettime = pygame.time.get_ticks

COM_PORT = "COM3"
CMD_SET_TURN, CMD_SET_DRIVE, CMD_SET_CAM = range(3)
CAM_SIZE = (640, 480)


class FPSMeter(object):
	SAMPLE_SIZE = 25
		
	def start(self):
		self.start_time = gettime()
		self.ticks = 0
		self.fps = 0
		
	def tick(self):
		self.ticks += 1
		if (self.ticks == self.SAMPLE_SIZE):
			t = gettime()
			self.fps = self.ticks / ((t - self.start_time) / 1000.0)
			self.start_time = t
			self.ticks = 0
			
		return self.fps

def log(*args):
	print " ".join(args)

class CameraManager(threading.Thread):
	def __init__(self, size, fps):
		threading.Thread.__init__(self)
		self.size = size
		self.camera = Device(0)
		#self.camera.setResolution(size[0], size[1])
		self.should_stop = threading.Event()
		self.freq = 1.0 / float(fps)
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind(("", 23457))
		self.sock.listen(5)
		self.client = None
		self.camera.displayCapturePinProperties()
		
	def stop(self):
		self.should_stop.set()
		
	def run(self):
		while 1:
			client, addr = self.sock.accept()
			log("Camera connection")
			self.client = client
			break
		fpsm = FPSMeter()
		fpsm.start()
		ld = ""
		while 1:
			if self.should_stop.isSet():
				return
			print fpsm.tick()
			pygame.time.wait(40)
			data = self.get_image()
			ld = data
			dl = len(data)
			self.client.send(pack("!I%ds" % dl, dl, data))
			
		
	def get_image(self):
		io = StringIO.StringIO()
		image = self.camera.getImage().resize((192, 144))
		image.save(io, "JPEG", quality = 50, optimize = True)
		data = io.getvalue()
		io.close()
		return data
		
		

class Client(object):
	def __init__(self, host, port, fps):
		log("Starting up")
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind(("", port))
		self.addr = (host, port)
		try:
			self.serial = serial.Serial(COM_PORT, 9600)
		except:
			self.serial = None
		self.data = ""
		self.cam = CameraManager(CAM_SIZE, fps)
		self.cam.start()
		self.run()
		
	def send(self, msg):
		self.sock.sendto(msg, self.addr)
	
	def run(self):
		log("Connecting")
		self.send("hello.")
		while 1:
			quit = False
			data, addr = self.sock.recvfrom(1024)
			self.data += data
			while self.data:
				idx = self.data.find(".")
				if idx != -1:
					msg = self.data[:idx]
					if idx > 0:
						if msg.lower() == "quit":
							quit = True
						self.ondata(msg)
					self.data = self.data[idx + 1:]
				else:
					break
			if quit == True:
				log("Exiting")
				if self.serial is not None:
					self.serial.close()
				self.sock.close()
				self.cam.stop()
				break
				
	def byte(self, data):
		if self.serial is not None:
			self.serial.write(chr(data))
					
	def ondata(self, msg):
		if len(msg) < 2:
			return
		if msg[0] == "x":
			self.byte(CMD_SET_TURN)
			self.byte(ord(msg[1]))
		elif msg[0] == "y":
			self.byte(CMD_SET_DRIVE)
			self.byte(ord(msg[1]))
		elif msg[0] == "z":
			self.byte(CMD_SET_CAM)
			self.byte(ord(msg[1]))
			
Client("192.168.0.12", 23456, 20)
