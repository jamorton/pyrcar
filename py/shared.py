
import time
import pygame
from pygame.locals import *
pygame.init()

gettime = pygame.time.get_ticks

CAMERA_SIZE = (

def log(*args):
	print "".join(args)

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