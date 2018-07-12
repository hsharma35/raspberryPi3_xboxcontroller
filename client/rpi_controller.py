#!/usr/bin/env python

# Import necessary modules
import socket
import dweepy
import xbox360_controller
import time
import math
import argparse

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

        self.curr_fwd = True
        self.curr_speed = 0
        self.curr_angle = 0

        self.host_ip = dweepy.get_latest_dweet_for('hsharma35-rpi3')[0]['content']['ip']

        super(RaspPiController, self).__init__(0)

    def connect_to_rpi(self):
        # Server(Raspberry Pi) IP address
        PORT = 21567
        ADDR = (self.host_ip, PORT)

        connected = False
        try:
            tcpCliSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Create a socket
            tcpCliSock.connect(ADDR)                    # Connect with the server
            self.tcpCliSock = tcpCliSock
            print('Connected to rpi')
            tcpCliSock.send('xy_home')
            return True
        except socket.error:
            # print('Can\'t connect to rpi')
            return False

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
        if self.tcpCliSock is None:
            return
        self.send_car_motion()
        self.send_cam_motion()

    def __del__(self):
        if self.tcpCliSock is not None:
            self.tcpCliSock.close()
