
from control_base import *
import sys, struct
import cStringIO as StringIO
from PIL import Image

AXIS_LEFT_X, AXIS_LEFT_Y, AXIS_RIGHT_X, AXIS_RIGHT_Y = range(4)

class Camera(Module):
	uses_loop = True
	def init(self, size, addr):
		self.size = size
		self.addr = addr
	
	def my_init(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect(self.addr)
		self.buffer = ""
		self.size_len = struct.calcsize("!I")
		self.img_len = 0
		self.recving = 0
		self.cam_number = 0
		
	def msg(self, sender, cmd, args):
		if cmd == "NEW_CONNECTION":
			self.my_init()
			self._task_run.kill()
			self._task_run = tasklet(self.my_loop)
		
	def my_loop(self):
		fpsm = FPSMeter()
		while 1:
			self.buffer += self.sock.recv(4096)
			while self.buffer:
				if not self.recving:
					if len(self.buffer) >= self.size_len:
						self.recving = 1
						self.img_len = struct.unpack("!I", self.buffer[:self.size_len])[0]
						self.buffer = self.buffer[self.size_len:]
					else:
						break
				else:
					if len(self.buffer) >= self.img_len:
						self.recving = 0
						img_data = struct.unpack("!%ds" % self.img_len, self.buffer[:self.img_len])[0]
						self.buffer = self.buffer[self.img_len:]
						disp = pygame.image.load(StringIO.StringIO(img_data))
						self.broadcast("CAMERA_IMAGE", disp, fpsm.tick())
					else:
						break
			

class Pinger(Module):
	uses_loop = True
	def init(self, wait):
		self.wait = wait
		self.last_ping = time.time()
	
	def loop(self):
		thetime = time.time()
		if thetime - self.last_ping > self.wait:
			self.last_ping = thetime
			self.broadcast("PING")

class Connection(Module):
	delimiter = "."
	uses_loop = True
	def init(self, port):
		self.port = port
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind(("", self.port))
		self.client = None
		self.buffer = ""
		
	def net_send(self, data):
		if self.client is not None:
			print "Sending:", data
			self.sock.sendto(data + ".", self.client)
			
	def msg(self, sender, cmd, args):
		if cmd == "NET_SEND":
			self.net_send(args[0])
		elif cmd == "EXITING":
			self.net_send("quit")
		elif cmd == "PING":
			self.net_send("p")
		elif cmd == "DRIVE_VALUE":
			self.net_send("y%s" % chr(args[0]))
		elif cmd == "TURN_VALUE":
			self.net_send("x%s" % chr(args[0]))
		elif cmd == "CAM_VALUE":
			self.net_send("z%s" % chr(args[0]))
		
	def loop(self):
		data, addr = self.sock.recvfrom(1024)
		self.buffer += data
		self.client = addr
		while self.buffer:
			idx = self.buffer.find(self.delimiter)
			if idx != -1:
				msg = self.buffer[:idx]
				if idx > 0:
					self.on_recv(msg)
				self.buffer  = self.buffer[idx + len(self.delimiter):]
			else:
				break
				
	def on_recv(self, msg):
		if msg.lower() == "hello":
			print self.client
			self.broadcast("NEW_CONNECTION", self.client)
		else:
			self.send(self.app, "NET_RECV", msg)
		
class Controller(Module):
	uses_loop = True
	def init(self):
		self.track = {"x": -1, "y": -1, "c": 90}
		self.buttons = {}
		for x in range(11):
			self.buttons[x] = 0
		if pygame.joystick.get_count() == 0:
			log("No joysticks connected. Disabling Control module.")
			self.stop()
		self.joy = pygame.joystick.Joystick(0)
		self.joy.init()
		
	def msg(self, sender, cmd, args):
		if cmd == "EVENT":
			event, type = args[0], args[0].type
			if type == JOYAXISMOTION:
				value = event.dict["value"]
				axis  = event.dict["axis"]
				self.on_axis(axis, value)
				
			elif type == JOYBUTTONUP:
				value = event.dict["button"] + 1
				self.buttons[value] = 0
				self.on_button_up(value)
				
			elif type == JOYBUTTONDOWN:
				value = event.dict["button"] + 1
				self.buttons[value] = 1
				self.on_button_down(value)
				
			elif type == JOYHATMOTION:
				hat   = event.dict["hat"]
				value = event.dict["value"]
				
				
	def scale(self, value, min1, max1, min2, max2):
		return (value - min1) * (float(max2 - min2) / float(max1 - min1)) + min2
				
	def on_button_up(self, button):
		if button == 10:
			self.send(self.app, "QUIT")
		elif button == 7:
			self.track["c"] = 90
			self.broadcast("CAM_VALUE", 90)
			
	def on_button_down(self, button):
		pass
		
	def loop(self):
		sleep(7)
		if self.buttons[5]:
			if self.track["c"] < 180:
				self.track["c"] += 2
				self.broadcast("CAM_VALUE", self.track["c"])
		elif self.buttons[6]:
			if self.track["c"] > 0:
				self.track["c"] -= 2
				self.broadcast("CAM_VALUE", self.track["c"])

				
	def on_axis(self, axis, value):
		value = -value
		if axis == AXIS_LEFT_Y:
			deg = int(self.scale(value, -1, 1, 70, 110))
			if deg != self.track["y"]:
				self.track["y"] = deg
				self.broadcast("DRIVE_VALUE", deg)
		
		elif axis == AXIS_RIGHT_X:
			deg = int(self.scale(value, -1, 1, 45, 135))
			if deg != self.track["x"]:
				self.track["x"] = deg
				self.broadcast("TURN_VALUE", deg)


class Display(Module):
	uses_loop = True
	def init(self, caption):
		pygame.display.set_caption(caption)
		self.screen = pygame.display.set_mode((640, 480))
		self.bg = pygame.Surface(self.screen.get_size()).convert()
		self.bg.fill((255, 255, 255))
		self.labels = {}
		self.font = font("Arial Black", 15)
		self.clock = pygame.time.Clock()
		self.cmimg = None
		self.fpsm = FPSMeter()

		
	def msg(self, sender, cmd, args):
		if cmd == "MODULE_LIST":
			self.setup_labels(args[0])
		elif cmd == "DRIVE_VALUE":
			self.update_label("driveval", "Drive: " + str(args[0]) + " deg")
		elif cmd == "TURN_VALUE":
			self.update_label("turnval", "Turn: " + str(args[0]) + " deg")
		elif cmd == "CAM_VALUE":
			self.update_label("camval", "Cam: " + str(args[0]) + " deg")
		elif cmd == "NEW_CONNECTION":
			self.update_label("client", "Connected: %s (%d)" % (args[0][0], args[0][1]))
		elif cmd == "CAMERA_IMAGE":	
			self.cmimg = args[0]
			self.update_label("fps", "Cam FPS: %d" % args[1])
		
	def setup_labels(self, modules):
		if "controller" in modules:
			self.add_label("driveval", "Drive: 90 deg", (20, 20))
			self.add_label("turnval", "Turn: 90 deg", (20, 50))
			self.add_label("camval", "Cam: 90 deg", (20, 80))
		if "connection" in modules:
			self.add_label("client", "Connected: none", (150, 20))
		if "camera" in modules:
			self.add_label("fps", "Cam FPS: 0", (20, 110))
		
	def add_label(self, name, text, location = (0, 0), color = (0, 0, 0)):
		self.labels[name] = Label(self.font, text, location, color)
		
	def update_label(self, name, text):
		if name in self.labels:
			self.labels[name].set_text(text)
		
	def render(self):
		sleep(30)
		pygame.display.flip()
		self.screen.blit(self.bg, (0, 0))
		for v in self.labels.values():
			v.blit(self.screen)
		if self.cmimg is not None:
			self.screen.blit(pygame.transform.smoothscale(self.cmimg, (480, 360)), (150, 60))
		
	def loop(self):
		self.render()
		#print self.fpsm.tick()
	
class Application(Actor):
	def __init__(self):
		Actor.__init__(self)
		self.modules = {}
		self.bad_events = [ACTIVEEVENT, MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP]
		
	def start_modules(self, modules):
		for m in modules:
			if isinstance(m, list) or isinstance(m, tuple):
				self.modules[m[0].__name__.lower()] = m[0](self.channel, *m[1:])
			else:
				self.modules[m.__name__.lower()] = m(self.channel)
		self.broadcast("MODULE_LIST", self.modules.keys())
		
	def get_module(self, name):
		return self.modules.get(name, None)
				
	def broadcast(self, cmd, *args):
		for m in self.modules.values():
			self.send(m.channel, cmd, *args)
			
	def msg(self, sender, cmd, args):
		if cmd == "BROADCAST":
			for m in self.modules.values():
				if m.channel != sender:
					m.channel.send((sender, args[0], args[1:]))
				
		elif cmd == "QUIT":
			self.exit()
			
	def exit(self):
		self.broadcast("EXITING")
		schedule()
		sys.exit()
	
	def start(self, modules):
		self.start_modules(modules)
		
		while 1:
			schedule()
			#pygame.time.wait(1)
			for event in pygame.event.get():
				type = event.type
				if type == QUIT:
					self.exit()
					return
				if type not in self.bad_events:
					self.broadcast("EVENT", event)
		
def start(modules):
	pygame.init()
	main_task = stackless.tasklet(Application().start)
	main_task(modules)
	stackless.run()

if __name__ == "__main__":

	modules = [
		(Display, "RC Car Test"),
		(Connection, 23456),
		(Pinger, 2),
		(Camera, CAMERA_SIZE, ("192.168.0.14", 23457)),
		Controller
	]
	
	start(modules)
	