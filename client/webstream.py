from Queue import Queue, Empty
import cv2
import imutils.video
from threading import Thread
import time

import numpy as np

class WebStream(object):
    def __init__(self, host_ip='143.215.111.138', host_port=8080):
        self.host_ip = host_ip
        self.host_port = host_port

        self.prev_time = None
        self.incoming_img_q = Queue(maxsize=2)

        self.image_fetcher = Thread(target=self._image_fetcher)
        self.image_fetcher.setDaemon(True)

        url = 'http://{}:{}/?action=stream'.format(self.host_ip, self.host_port)
        self.cap = cv2.VideoCapture(url)

        self.fps = imutils.video.FPS()

    def start_worker(self):
        self.image_fetcher.start()
        self.fps.start()

    def _image_fetcher(self):
        while True:
            while self.incoming_img_q.full():
                time.sleep(0.0001)
            ret, frame = self.cap.read()
            self.incoming_img_q.put(frame, False)
            self.fps.update()
            self.fps.stop()

if __name__ == "__main__":
    ws = WebStream()
    ws.start_worker()
    time.sleep(1)
    while True:
        while ws.incoming_img_q.empty():
            time.sleep(0.0001)
        curr_img = ws.incoming_img_q.get()
        cv2.imshow('Video', curr_img)
        if cv2.waitKey(1) == 27:
            exit(0)
