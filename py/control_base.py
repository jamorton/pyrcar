
import pygame
from pygame.locals import *
import stackless, stacklesssocket, time
stacklesssocket.install()
import socket

DEBUG = False

def log(*args):
#	if DEBUG:
	print "".join(args)
		
__sleepingTasklets = []

gettime = pygame.time.get_ticks

def sleep(mstowait):
    channel = stackless.channel()
    endTime = gettime() + mstowait
    __sleepingTasklets.append((endTime, channel))
    __sleepingTasklets.sort()
    # Block until we get sent an awakening notification.
    channel.receive()

def __manageSleepingTasklets():
    while 1:
        if len(__sleepingTasklets):
            endTime = __sleepingTasklets[0][0]
            if endTime <= gettime():
                channel = __sleepingTasklets[0][1]
                del __sleepingTasklets[0]
                # We have to send something, but it doesn't matter what as it is not used.
                channel.send(None)
        stackless.schedule()
        pygame.time.wait(5)

stackless.tasklet(__manageSleepingTasklets)()

class FPSMeter(object):
	SAMPLE_SIZE = 20
	def __init__(self):
		self.start_time = gettime()
		self.ticks = 0
		self.fps = 0
		
	def tick(self):
		self.ticks += 1
		if (self.ticks == self.SAMPLE_SIZE):
			t = gettime()
			self.fps = self.ticks / ((t - self.start_time) / 1000.0)
			self.ticks = 0
			self.start_time = t
			
		return self.fps

class Actor(object):
	def __init__(self):
		self.channel = stackless.channel()
		self._task_recv = stackless.tasklet(self.recv)
		self._task_recv()
		
	def send(self, target, cmd, *args):
		target.send((self.channel, cmd, args))
		
	def stop(self):
		self._task_recv.kill()
		
	def recv(self):
		while 1:
			sender, cmd, args = self.channel.receive()
			stackless.tasklet(self.msg)(sender, cmd, args)
		
	def msg(self, sender, cmd, args):
		pass
		
class Module(Actor):
	uses_loop = False
	def __init__(self, app, *args):
		Actor.__init__(self)
		self.app = app
		stackless.tasklet(self.init)(*args)
		if self.uses_loop:
			self._task_run = stackless.tasklet(self.run)
			self._task_run()
		
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
			stackless.schedule()
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
