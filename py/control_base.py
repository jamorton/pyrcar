
import stackless, stacklesssocket, time
stacklesssocket.install()
import socket
from shared import *

channel  = stackless.channel
schedule = stackless.schedule

def tasklet(func, *args, **kwargs):
	t = stackless.tasklet(func)
	t(*args, **kwargs)
	return t

__sleepingTasklets = []

def sleep(mstowait):
    chan = channel()
    endTime = gettime() + mstowait
    __sleepingTasklets.append((endTime, chan))
    __sleepingTasklets.sort()
    # Block until we get sent an awakening notification.
    chan.receive()

def __manageSleepingTasklets():
    while 1:
        if len(__sleepingTasklets):
            endTime = __sleepingTasklets[0][0]
            if endTime <= gettime():
                channel = __sleepingTasklets[0][1]
                del __sleepingTasklets[0]
                # We have to send something, but it doesn't matter what as it is not used.
                channel.send(None)
        schedule()

stackless.tasklet(__manageSleepingTasklets)()

class Actor(object):
	def __init__(self):
		self.channel = stackless.channel()
		self._task_recv = tasklet(self.recv)
		
	def send(self, target, cmd, *args):
		target.send((self.channel, cmd, args))
		
	def stop(self):
		self._task_recv.kill()
		
	def recv(self):
		while 1:
			sender, cmd, args = self.channel.receive()
			tasklet(self.msg, sender, cmd, args)
		
	def msg(self, sender, cmd, args):
		pass
		
class Module(Actor):
	uses_loop = False
	def __init__(self, app, *args):
		Actor.__init__(self)
		self.app = app
		tasklet(self.init, *args)
		if self.uses_loop:
			self._task_run = tasklet(self.run)
		
	def broadcast(self, cmd, *args):
		self.send(self.app, "BROADCAST", cmd, *args)
		
	def init(self):
		pass
		
	def stop(self):
		Actor.stop(self)
		if self.uses_loop:
			self._task_run.kill()
		
	def run(self):
		while 1:
			schedule()
			self.loop()
			
	def loop(self):
		pass

def font(type, size = 12):
	return pygame.font.SysFont(type, size)
	
class Label(object):
	def __init__(self, font, text, location = (0, 0), color = (0, 0, 0)):
		self.font = font
		self.text = text
		self.location = location
		self.color = color
		self.surface = None
		self.valid = False
		
	def render(self):
		self.surface = self.font.render(self.text, 1, self.color)
		
	def blit(self, screen):
		if not self.valid:
			self.render()
		screen.blit(self.surface, self.location)
		
	def set_font(self, font):
		self.valid = False
		self.font = font
		
	def set_text(self, text):
		self.valid = False
		self.text = text
	
	def set_location(self, loc):
		self.location = loc
		
	def set_color(self, color):
		self.valid = False
		self.color = color
