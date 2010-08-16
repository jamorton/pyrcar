# Random testing stuff.

def test_joy_buttons():
	import pygame
	pygame.init()

	joy = pygame.joystick.Joystick(0)
	joy.init()

	while 1:
		pygame.time.wait(50)
		for evt in pygame.event.get():
			if evt.type == pygame.JOYBUTTONDOWN:
				print evt.dict["button"]
				
				
if __name__ == "__main__":
	test_joy_buttons()