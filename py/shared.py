
import time
import pygame
from pygame.locals import *
pygame.init()

getms = pygame.time.get_ticks
getseconds = lambda: getms() / 1000.0
wait = pygame.time.wait

CAMERA_SIZE = (256, 192)

def log(*args):
	print "".join(args)

class FPSMeter(object):
	SAMPLE_SIZE = 20
	def __init__(self):
		self.start_time = getms()
		self.ticks = 0
		self.fps = 0
		
	def tick(self):
		self.ticks += 1
		if (self.ticks == self.SAMPLE_SIZE):
			t = getms()
			self.fps = self.ticks / ((t - self.start_time) / 1000.0)
			self.ticks = 0
			self.start_time = t
			
		return self.fps