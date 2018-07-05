#!/usr/bin/env python

# Import necessary modules
import socket
import dweepy
import pygame
import xbox360_controller
import time
import math
import argparse

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 65, 65)
GREEN = (75, 225, 25)
BLUE = (65, 65, 255)
AMBER = (255, 175, 0)
GREY = (175, 175, 175)

FPS = 60
clock = pygame.time.Clock()

def display_text(screen, text, x, y):
    my_font = pygame.font.Font(None, 30)
    output = my_font.render(text, True, WHITE)
    screen.blit(output, [x, y])

class RaspPiController(xbox360_controller.Controller):
    def __init__(self, debug):
        ctrl_cmd = [
                'forward',
                'backward',
                'left',
                'right',
                'stop',
                'read cpu_temp',
                'home',
                'distance',
                'x+',
                'x-',
                'y+',
                'y-',
                'xy_home']

        self.speed_multiplier = 100
        self.tcpCliSock = None
        if not debug:
            self.connect_to_rpi()

        self.curr_fwd = True
        self.curr_speed = 0
        self.curr_angle = 0

        super(RaspPiController, self).__init__(0)

    def connect_to_rpi(self):
        # Server(Raspberry Pi) IP address
        HOST = dweepy.get_latest_dweet_for('hsharma35-rpi3')[0]['content']['ip']
        PORT = 21567
        ADDR = (HOST, PORT)

        connected = False
        while not connected:
            try:
                tcpCliSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Create a socket
                tcpCliSock.connect(ADDR)                    # Connect with the server
                self.tcpCliSock = tcpCliSock
                print('Connected to rpi')
                tcpCliSock.send('xy_home')
                return tcpCliSock
            except socket.error:
                print('Can\'t connect to rpi')
                time.sleep(1)

    def set_speed(self):
        tmp = 'speed'
        spd = self.speed_multiplier
        data = tmp + str(spd)  # Change the integers into strings and combine them with the string 'speed'. 
        self.tcpCliSock.send(data)

    def get_car_motion(self):
        move_lr, _ = self.get_left_stick()
        pan_lr, tilt_ud = self.get_right_stick()

        speed = int(self.speed_multiplier * self.get_triggers())
        angle = int((move_lr + 1) * 255 / 2.)

        if speed < 0:
            fwd = False
        else:
            fwd = True
        speed = abs(speed)

        return speed, angle, fwd

    def send_car_motion(self):
        speed, angle, fwd = self.get_car_motion()
        if self.curr_fwd != fwd or self.curr_speed != speed:
            self.curr_speed = speed
            self.curr_fwd = fwd
            if fwd:
                self.tcpCliSock.send('forward={}'.format(speed))
            else:
                self.tcpCliSock.send('backward={}'.format(speed))
        if self.curr_angle != angle:
            self.curr_angle = angle
            self.tcpCliSock.send('turn={}'.format(angle))

    def send_cam_motion(self):
        pan_lr, tilt_ud = self.get_right_stick()
        if tilt_ud < -0.5:
            self.tcpCliSock.send('y+')
        elif tilt_ud > 0.5:
            self.tcpCliSock.send('y-')

        if pan_lr > 0.5:
            self.tcpCliSock.send('x+')
        elif pan_lr < -0.5:
            self.tcpCliSock.send('x-')

    def send_buttons(self):
        self.send_car_motion()
        self.send_cam_motion()

    def __del__(self):
        self.tcpCliSock.close()


def main(debug):
    pygame.init()
    size = [600, 970]
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("X-Box 360 Controller")
    controller = RaspPiController(debug)
    done = False
    while not done:
        # event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done=True

        # joystick stuff
        pressed = controller.get_buttons()
        if not debug:
            controller.send_buttons()

        a_btn = pressed[xbox360_controller.A]
        b_btn = pressed[xbox360_controller.B]
        x_btn = pressed[xbox360_controller.X]
        y_btn = pressed[xbox360_controller.Y]
        back = pressed[xbox360_controller.BACK]
        start = pressed[xbox360_controller.START]
        # guide = pressed[xbox360_controller.GUIDE]
        lt_bump = pressed[xbox360_controller.LEFT_BUMP]
        rt_bump = pressed[xbox360_controller.RIGHT_BUMP]
        lt_stick_btn = pressed[xbox360_controller.LEFT_STICK_BTN]
        rt_stick_btn = pressed[xbox360_controller.RIGHT_STICK_BTN]

        lt_x, lt_y = controller.get_left_stick()
        rt_x, rt_y = controller.get_right_stick()

        triggers = controller.get_triggers()
        if back == 1:
            done = True

        pad_up, pad_right, pad_down, pad_left = controller.get_pad()

        # game logic


        # drawing
        screen.fill(BLACK)

        ''' controller outline '''
        pygame.draw.rect(screen, GREY, [40, 20, 520, 320], 3)

        ''' a, b, x, y '''
        x, y = 450, 120

        if a_btn == 1:
            pygame.draw.ellipse(screen, GREEN, [x + 30, y + 60, 25, 25])
        else:
            pygame.draw.ellipse(screen, GREEN, [x + 30, y + 60, 25, 25], 2)

        if b_btn == 1:
            pygame.draw.ellipse(screen, RED, [x + 60, y + 30, 25, 25])
        else:
            pygame.draw.ellipse(screen, RED, [x + 60, y + 30, 25, 25], 2)

        if x_btn == 1:
            pygame.draw.ellipse(screen, BLUE, [x, y + 30, 25, 25])
        else:
            pygame.draw.ellipse(screen, BLUE, [x, y + 30, 25, 25], 2)

        if y_btn == 1:
            pygame.draw.ellipse(screen, AMBER, [x + 30, y, 25, 25])
        else:
            pygame.draw.ellipse(screen, AMBER, [x + 30, y, 25, 25], 2)

        ''' back, start '''
        x, y = 250, 145

        if back == 1:
            pygame.draw.ellipse(screen, WHITE, [x, y, 25, 20])
        else:
            pygame.draw.ellipse(screen, WHITE, [x, y, 25, 20], 2)

        pygame.draw.ellipse(screen, GREY, [x + 40, y - 10, 40, 40])

        if start == 1:
            pygame.draw.ellipse(screen, WHITE, [x + 95, y, 25, 20])
        else:
            pygame.draw.ellipse(screen, WHITE, [x + 95, y, 25, 20], 2)

        ''' bumpers '''
        x, y = 100, 50

        if lt_bump == 1:
            pygame.draw.rect(screen, WHITE, [x, 50, y, 25])
        else:
            pygame.draw.rect(screen, WHITE, [x, 50, y, 25], 2)

        if rt_bump == 1:
            pygame.draw.rect(screen, WHITE, [x + 365, y, 50, 25])
        else:
            pygame.draw.rect(screen, WHITE, [x + 365, y, 50, 25], 2)

        ''' triggers '''
        x, y = 210, 60

        trigger_x = x + 100 + round(triggers * 100)
        pygame.draw.line(screen, WHITE, [x, y], [x + 200, y])
        pygame.draw.line(screen, WHITE, [trigger_x, y - 10], [trigger_x, y + 10])

        ''' left stick '''
        x, y = 65, 100

        left_x = x + 50 + round(lt_x * 50)
        left_y = y + 50 + round(lt_y * 50)

        pygame.draw.line(screen, WHITE, [x + 60, y], [x + 60, y + 120], 1)
        pygame.draw.line(screen, WHITE, [x, y + 60], [x + 120, y + 60], 1)
        if lt_stick_btn == 0:
            pygame.draw.ellipse(screen, WHITE, [left_x, left_y, 20, 20], 2)
        else:
            pygame.draw.ellipse(screen, WHITE, [left_x, left_y, 20, 20])

        ''' right stick '''
        x, y = 330, 190

        right_x = x + 50 + round(rt_x * 50)
        right_y = y + 50 + round(rt_y * 50)

        pygame.draw.line(screen, WHITE, [x + 60, y], [x + 60, y + 120], 1)
        pygame.draw.line(screen, WHITE, [x, y + 60], [x + 120, y + 60], 1)
        if rt_stick_btn == 0:
            pygame.draw.ellipse(screen, WHITE, [right_x, right_y, 20, 20], 2)
        else:
            pygame.draw.ellipse(screen, WHITE, [right_x, right_y, 20, 20])

        ''' hat '''
        x, y = 180, 200

        pygame.draw.ellipse(screen, WHITE, [x, y, 100, 100])
        if pad_up:
            pygame.draw.ellipse(screen, GREY, [x + 40, y, 20, 20])
        if pad_right:
            pygame.draw.ellipse(screen, GREY, [x + 80, y + 40, 20, 20])
        if pad_down:
            pygame.draw.ellipse(screen, GREY, [x + 40, y +80, 20, 20])
        if pad_left:
            pygame.draw.ellipse(screen, GREY, [x, y + 40, 20, 20])

        ''' joystick values '''
        x, y = 50, 370
        display_text(screen, "BUTTONS", x, y)
        display_text(screen, "A: {}".format(a_btn), x, y+ 25)
        display_text(screen, "B: {}".format(b_btn), x, y + 50)
        display_text(screen, "X: {}".format(x_btn), x, y + 75)
        display_text(screen, "Y: {}".format(y_btn), x, y + 100)
        display_text(screen, "LB: {}".format(lt_bump), x, y + 125)
        display_text(screen, "RB: {}".format(rt_bump), x, y + 150)
        display_text(screen, "Back: {}".format(back), x, y + 175)
        display_text(screen, "Start: {}".format(start), x, y + 200)
        display_text(screen, "LT Stick Btn: {}".format(lt_stick_btn), x, y + 225)
        display_text(screen, "RT Stick Btn: {}".format(rt_stick_btn), x, y + 250)

        display_text(screen, "AXES", x + 275, y)
        display_text(screen, "Left Stick: ({}, {})".format(round(lt_x, 2), round(lt_y, 2)), x + 275, y + 25)
        display_text(screen, "Right Stick: ({}, {})".format(round(rt_x, 2), round(rt_y, 2)), x + 275, y + 50)
        display_text(screen, "Triggers: {}".format(round(triggers, 2)), x + 275, y + 75)

        display_text(screen, "D-PAD", x + 275, y + 125)
        display_text(screen, "Up: {}".format(pad_up), x + 275, y + 150)
        display_text(screen, "Right: {}".format(pad_right), x + 275, y + 175)
        display_text(screen, "Down: {}".format(pad_down), x + 275, y + 200)
        display_text(screen, "Left: {}".format(pad_left), x + 275, y + 225)

        mag, angle, fwd = controller.get_car_motion()
        display_text(screen, "Mag: {}".format(mag), x + 275, y + 250)
        display_text(screen, "Angle: {}".format(angle), x + 275, y + 275)

        pygame.display.flip()

        # update screen
        pygame.display.flip()
        clock.tick(20)
    pygame.quit()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Raspberry Pi Xbox360 controller.')
    parser.add_argument('--debug', action='store_true',
                        help='Debug mode (no raspberry)')
    args = parser.parse_args()

    main(args.debug)
