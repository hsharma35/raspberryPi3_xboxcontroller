#!/usr/bin/env python
import PCA9685 as servo
import time                  # Import necessary modules

MinPulse = 200
MaxPulse = 700

Current_x = 0
Current_y = 0

def setup(busnum=None):
	global Xmin, Ymin, Xmax, Ymax, home_x, home_y, pwm
	offset_x = 0
	offset_y = 0
	try:
		for line in open('config'):
			if line[0:8] == 'offset_x':
				offset_x = int(line[11:-1])
                                print('Offset x: {}'.format(offset_x))
                                print('Line: {}'.format(line))
				#print 'offset_x =', offset_x
			if line[0:8] == 'offset_y':
				offset_y = int(line[11:-1])
                                print('Offset y: {}'.format(offset_y))
                                print('Line: {}'.format(line))
				#print 'offset_y =', offset_y
	except:
		pass
	Xmin = MinPulse
	Xmax = MaxPulse
	Ymin = MinPulse
	Ymax = MaxPulse
	home_x = (Xmax + Xmin) / 2 + offset_x
	home_y = (Ymax + Ymin) / 2 + offset_y
	if busnum == None:
		pwm = servo.PWM()                  # Initialize the servo controller.
	else:
		pwm = servo.PWM(bus_number=busnum) # Initialize the servo controller.
	pwm.frequency = 60

# ==========================================================================================
# Control the servo connected to channel 14 of the servo control board to make the camera 
# turning towards the positive direction of the x axis.
# ==========================================================================================
def move_decrease_x():
	global Current_x
	Current_x += 25
	if Current_x > Xmax:
		Current_x = Xmax
        pwm.write(14, 0, Current_x)   # CH14 <---> X axis
# ==========================================================================================
# Control the servo connected to channel 14 of the servo control board to make the camera 
# turning towards the negative direction of the x axis.
# ==========================================================================================
def move_increase_x():
	global Current_x
	Current_x -= 25
	if Current_x <= Xmin:
		Current_x = Xmin
        pwm.write(14, 0, Current_x)
# ==========================================================================================
# Control the servo connected to channel 15 of the servo control board to make the camera 
# turning towards the positive direction of the y axis. 
# ==========================================================================================
def move_increase_y():
	global Current_y
	Current_y += 25
	if Current_y > Ymax:
		Current_y = Ymax
        pwm.write(15, 0, Current_y)   # CH15 <---> Y axis
# ==========================================================================================
# Control the servo connected to channel 15 of the servo control board to make the camera 
# turning towards the negative direction of the y axis. 
# ==========================================================================================		
def move_decrease_y():
	global Current_y
	Current_y -= 25
	if Current_y <= Ymin:
		Current_y = Ymin
        pwm.write(15, 0, Current_y)
# ==========================================================================================		
# Control the servos connected with channel 14 and 15 at the same time to make the camera 
# move forward.
# ==========================================================================================
def home_x_y():
	global Current_y
	global Current_x
	Current_y = home_y 
	Current_x = home_x
        print('Writing {},{} to pwm'.format(Current_x, Current_y))
	pwm.write(14, 0, Current_x)
	pwm.write(15, 0, Current_y)

def calibrate(x,y):
        print('Writing {},{} to pwm'.format(x, y))
	pwm.write(14, 0, (MaxPulse+MinPulse)/2+x)
	pwm.write(15, 0, (MaxPulse+MinPulse)/2+y)

def test():
	while True:
		home_x_y()
		time.sleep(0.5)
		for i in range(0, 9):
			move_increase_x()
			move_increase_y()
			time.sleep(0.5)
		for i in range(0, 9):
			move_decrease_x()
			move_decrease_y()
			time.sleep(0.5)

if __name__ == '__main__':
	setup()
	home_x_y()
