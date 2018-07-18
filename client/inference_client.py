from Queue import Queue, Empty
from threading import Thread
import urllib 
from darkflow.net.build import TFNet
import cv2
import time
import numpy as np

import imutils.video

class InferenceClient(object):
    def __init__(self, host_ip='143.215.111.138', host_port=8080):
    # def __init__(self, host_ip, host_port):
        self.host_ip = host_ip
        self.host_port = host_port

        self.fps = imutils.video.FPS().start()
        self.prev_time = None
        self.incoming_img_q = Queue(maxsize=1)
        self.outgoing_img_q = Queue(maxsize=1)
        self.outgoing_det_q = Queue(maxsize=1)

        self.detection_count = 0

        self.image_fetcher = Thread(target=self._image_fetcher)
        self.image_fetcher.setDaemon(True)

        self.inference_engine = Thread(target=self.put_image_and_bbox)
        self.inference_engine.setDaemon(True)

        self.detection_enabled = True

        options = {"model": "cfg/tiny-yolo-voc.cfg", "load": "bin/tiny-yolo-voc.weights", "threshold": 0.1}
        self.tfnet = TFNet(options)

        url = 'http://{}:{}/?action=stream'.format(self.host_ip, self.host_port)
        self.cap = cv2.VideoCapture(url)

    def start_worker(self):
        self.image_fetcher.start()
        self.inference_engine.start()

    def _image_fetcher(self):
        self.bytes = ''
        while True:
            while self.outgoing_img_q.full():
                time.sleep(0.0001)
            fetch_time = time.time()
            ret, frame = self.cap.read()
            frame_copy = frame.copy()
            if not self.incoming_img_q.full():
                self.incoming_img_q.put((frame, fetch_time))
            self.outgoing_img_q.put((frame_copy, fetch_time))

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
            while self.incoming_img_q.empty() or self.outgoing_det_q.full():
                time.sleep(0.0001)
            if self.prev_time is None:
                self.prev_time = time.time()
            img, start = self.incoming_img_q.get(False)
            if self.detection_enabled:
                det = self.get_det(img)
                self.outgoing_det_q.put(det, False)
                self.detection_count += 1
            self.fps.update()
            self.fps.stop()


if __name__ == "__main__":
    i_client = InferenceClient()
    i_client.start_worker()
    while True:
        # if not i_client.outgoing_img_q.empty() or i_client.outgoing_det_q.empty():
        if not i_client.outgoing_img_q.empty():
            img, image_time = i_client.outgoing_img_q.get()
            print('lag: {}'.format(time.time() - image_time))
            if not i_client.outgoing_det_q.empty():
                det = i_client.outgoing_det_q.get()
                if len(det) > 0:
                    for d in det:
                        label, l, r, t, b = d
                        cv2.rectangle(img, (l, b), (r, t), (0,255,0), 2)
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        cv2.putText(img,label,(l,b), font, 1,(255,255,255),2,cv2.LINE_AA)
            cv2.imshow('Video', img)
            try:
                print('Frames per second: {}'.format(i_client.fps.fps()))
            except:
                pass
            if cv2.waitKey(1) == 27:
                exit(0)
            # time.sleep(0.1)

