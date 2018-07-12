#!/usr/bin/env python

# Import necessary modules
import socket
import dweepy
import pygame
import rpi_controller
import xbox360_controller
import time
import math
import argparse

import requests
import cv2
import numpy as np
from io import BytesIO
from PIL import Image, ImageDraw, ImageTk
from darkflow.net.build import TFNet

from Queue import Queue, Empty
from threading import Thread

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 65, 65)
GREEN = (75, 225, 25)
BLUE = (65, 65, 255)
AMBER = (255, 175, 0)
GREY = (175, 175, 175)

FPS = 20
clock = pygame.time.Clock()

class InferenceClient(object):
    def __init__(self, host_ip, host_port):
        self.host_ip = host_ip
        self.host_port = host_port

        self.fps = 0
        self.incoming_img_q = Queue(maxsize=2)
        self.outgoing_det_q = Queue(maxsize=2)
        self.outgoing_img_q = Queue(maxsize=2)

        self.image_fetcher = Thread(target=self._image_fetcher)
        self.image_fetcher.setDaemon(True)

        self.inference_engine = Thread(target=self.put_image_and_bbox)
        self.inference_engine.setDaemon(True)

        options = {"model": "cfg/tiny-yolo-voc.cfg", "load": "bin/tiny-yolo-voc.weights", "threshold": 0.2}
        self.tfnet = TFNet(options)

    def start_worker(self):
        self.image_fetcher.start()
        self.inference_engine.start()

    def _image_fetcher(self):
        while True:
            while self.incoming_img_q.full():
                time.sleep(0.01)
            r = requests.get('http://{}:8998/image.jpg'.format(self.host_ip)) # replace with your ip address
            curr_img = Image.open(BytesIO(r.content))
            self.incoming_img_q.put(curr_img, False)

    def get_det(self, image):
        curr_img_cv2 = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        result = self.tfnet.return_predict(curr_img_cv2)
        out = []
        for det in result:
            l = det['topleft']['x']
            r = det['bottomright']['x']
            t = det['topleft']['y']
            b = det['bottomright']['y']
            out.append((det['label'], l,r,t,b))
        return out

    def put_image_and_bbox(self):
        while True:
            while self.incoming_img_q.empty() or self.outgoing_det_q.full() or self.outgoing_img_q.full():
                time.sleep(0.01)
            img = self.incoming_img_q.get(False)
            det = self.get_det(img)
            self.outgoing_img_q.put(img, False)
            self.outgoing_det_q.put(det, False)

    def get_image_bbox(self):
        self.queue.get()

def display_text(screen, text, x, y):
    my_font = pygame.font.Font(None, 30)
    output = my_font.render(text, True, WHITE)
    screen.blit(output, [x, y])

def main(debug):
    pygame.init()
    size = [1200, 800]
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("X-Box 360 Controller")
    controller = rpi_controller.RaspPiController(debug)
    done = False
    connected = False

    frame = None

    infer = InferenceClient(controller.host_ip, 8998)
    infer.start_worker()
    xmax, ymax = 640, 480
    while not done:
        # event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done=True

        if not connected:
            connected = controller.connect_to_rpi()

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

        if not infer.outgoing_img_q.empty():
            curr_img = infer.outgoing_img_q.get()
            frame = np.rot90(curr_img)
            frame = pygame.surfarray.make_surface(frame)

        if frame is not None:
            screen.blit(frame, (0,0))

        if not infer.outgoing_det_q.empty():
            bbox = infer.outgoing_det_q.get()
            for b in bbox:
                label, l,r,t,b = b
                l = xmax - l
                r - xmax - r
                pygame.draw.line(screen, GREEN, [l, t], [l, b], 2)
                pygame.draw.line(screen, GREEN, [l, b], [r, b], 2)
                pygame.draw.line(screen, GREEN, [r, b], [r, t], 2)
                pygame.draw.line(screen, GREEN, [r, t], [l, t], 2)
                # pygame.draw.rect(screen, GREEN, [r,l-r,b,t-b], 1)
                # draw.text([det['topleft']['x'], det['topleft']['y'] - 13], det['label'], fill=(255, 0, 0))
                display_text(screen, label, r-80, b-20)


        ''' controller outline '''
        pygame.draw.rect(screen, GREY, [680, 20, 520, 320], 3)

        ''' a, b, x, y '''
        x, y = 1090, 120

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
        x, y = 890, 145

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
        x, y = 740, 50

        if lt_bump == 1:
            pygame.draw.rect(screen, WHITE, [x, 50, y, 25])
        else:
            pygame.draw.rect(screen, WHITE, [x, 50, y, 25], 2)

        if rt_bump == 1:
            pygame.draw.rect(screen, WHITE, [x + 365, y, 50, 25])
        else:
            pygame.draw.rect(screen, WHITE, [x + 365, y, 50, 25], 2)

        ''' triggers '''
        x, y = 850, 60

        trigger_x = x + 100 + round(triggers * 100)
        pygame.draw.line(screen, WHITE, [x, y], [x + 200, y])
        pygame.draw.line(screen, WHITE, [trigger_x, y - 10], [trigger_x, y + 10])

        ''' left stick '''
        x, y = 705, 100

        left_x = x + 50 + round(lt_x * 50)
        left_y = y + 50 + round(lt_y * 50)

        pygame.draw.line(screen, WHITE, [x + 60, y], [x + 60, y + 120], 1)
        pygame.draw.line(screen, WHITE, [x, y + 60], [x + 120, y + 60], 1)
        if lt_stick_btn == 0:
            pygame.draw.ellipse(screen, WHITE, [left_x, left_y, 20, 20], 2)
        else:
            pygame.draw.ellipse(screen, WHITE, [left_x, left_y, 20, 20])

        ''' right stick '''
        x, y = 970, 190

        right_x = x + 50 + round(rt_x * 50)
        right_y = y + 50 + round(rt_y * 50)

        pygame.draw.line(screen, WHITE, [x + 60, y], [x + 60, y + 120], 1)
        pygame.draw.line(screen, WHITE, [x, y + 60], [x + 120, y + 60], 1)
        if rt_stick_btn == 0:
            pygame.draw.ellipse(screen, WHITE, [right_x, right_y, 20, 20], 2)
        else:
            pygame.draw.ellipse(screen, WHITE, [right_x, right_y, 20, 20])

        ''' hat '''
        x, y = 820, 200

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
        x, y = 690, 370
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
        clock.tick(FPS)
    pygame.quit()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Raspberry Pi Xbox360 controller.')
    parser.add_argument('--debug', action='store_true',
                        help='Debug mode (no raspberry)')
    args = parser.parse_args()

    main(args.debug)
