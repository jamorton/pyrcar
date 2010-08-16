
import socket, serial, threading
import cStringIO as StringIO
from VideoCapture import Device
from struct import pack
from shared import *

CMD_SET_TURN, CMD_SET_DRIVE, CMD_SET_CAM = range(3)

class CameraManager(threading.Thread):
	def __init__(self, size, fps):
		threading.Thread.__init__(self)
		self.size = size
		self.camera = Device(0)
		self.should_stop = threading.Event()
		self.freq = int(1.0 / float(fps) * 1000.0)
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client = None
		#self.camera.displayCapturePinProperties()
		
	def stop(self):
		self.should_stop.set()
		
	def run(self):
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind(("", 23457))
		self.sock.listen(5)
		
		while 1:
			client, addr = self.sock.accept()
			log("Camera connection")
			self.client = client
			break
			
		fpsm = FPSMeter()
		while 1:
			if self.should_stop.isSet():
				return
			print fpsm.tick()
			wait(self.freq)
			data = self.get_image()
			data_len = len(data)
			self.client.send(pack("!I%ds" % data_len, data_len, data))
			
		
	def get_image(self):
		io = StringIO.StringIO()
		image = self.camera.getImage().resize(self.size)
		image.save(io, "JPEG", quality = 75, optimize = True)
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
			self.serial = serial.Serial("COM3", 9600)
		except:
			self.serial = None
		self.data = ""
		self.cam = CameraManager(CAMERA_SIZE, fps)
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
			if isinstance(data, str):
				self.serial.write(data)
			elif isinstance(data, int):
				try:
					self.serial.write(chr(data))
				except ValueError:
					self.serial.write(str(data))
			else:
				try:
					for i in iter(data):
						self.byte(i)
				except TypeError:
					pass
					
	def ondata(self, msg):
		if len(msg) < 2:
			return
		cmd = msg[0]
		val = msg[1]
		if   cmd == "x":
			self.byte(CMD_SET_TURN)
			self.byte(val)
		elif cmd == "y":
			self.byte(CMD_SET_DRIVE)
			self.byte(val)
		elif cmd == "z":
			self.byte(CMD_SET_CAM)
			self.byte(val)
			
Client("192.168.0.12", 23456, 30)
