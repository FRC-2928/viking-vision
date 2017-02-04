#!/usr/bin/env python2
from __future__ import division
import sys

import cv2
import sys
import numpy as np
from networktables import NetworkTables
import logging
BLUR_SIZE = (11, 11)
BLUR_FACTOR = 90
GREEN_LOWER_LIMIT = 235
MEDIAN_BLUR_SIZE = 5
HEIGHT_WIDTH_RATIO = 5/2
HEIGHT_WIDTH_TOLERANCE = .85
AREA_TOLERANCE = 1.7
logging.basicConfig(level=logging.DEBUG)

ip = "10.29.28.56"

def ntInit(table):
    NetworkTables.initialize(ip)
    return NetworkTables.getTable(table)

# From http://stackoverflow.com/questions/4961017/clojure-style-function-threading-in-python
def T(*args):
    return reduce(lambda l, r: r(l), args)

def toGrayscale(src):
    return cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)

def toGreenscale(src):
    return cv2.extractChannel(src, 1)

def brightPass(src):
    return cv2.inRange(src, GREEN_LOWER_LIMIT, 255)

def blur(src):
    return cv2.GaussianBlur(src, BLUR_SIZE, BLUR_FACTOR)

def medianBlur(src):
    return cv2.medianBlur(src, MEDIAN_BLUR_SIZE)
def blobbify(src):
    data = src.flat
    dims = src.shape
    print dims
    for i in range(0, len(data)):
        if data[i] > 1:
            cv2.ellipse(src, (i % dims[0], i / dims[0]), (15, 6), 90, 0, 360, 0xFF, -1)
    return src

def outline(src):
    dst = np.zeros(src.shape, np.uint8)
    im2, contours, hierarchy  = cv2.findContours(src, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(dst, contours, -1, (255), 1)
    return dst, contours

def quads(contours):
    output = []
    boxes = []
    polys = [cv2.approxPolyDP(c, 5, True) for c in contours]
    polys = filter(lambda c: len(c) == 4, polys)
    for p in polys:
        _, _, w, h = cv2.boundingRect(p)
        boxes.append(abs(h/w - HEIGHT_WIDTH_RATIO) <= HEIGHT_WIDTH_TOLERANCE)
    for i in range(len(boxes)):
        if boxes[i]:
            output.append(polys[i])
    return output

def pairs(contours):
    areas = [cv2.contourArea(c) for c in contours]
    outputMask = [False] * len(areas)
    output = []
    # Awful imperative code TODO: write something better
    for i in range(len(areas)):
        for j in range(len(areas)):
            if i == j or outputMask[i] or outputMask[j]:
                continue
            if abs(max(areas[i], areas[j])/min(areas[i], areas[j])) - 1 <= AREA_TOLERANCE:
                outputMask[i] = True
                outputMask[j] = True
    for i in range(len(areas)):
        if outputMask[i]:
            output.append(contours[i])
    return output

def distanceToCenter(contours, frameWidth):
    moments = [cv2.moments(c) for c in contours][:2]
    normalized = []
    for m in moments:
        cx = int(m['m10'] / m['m00'])
        normalized.append(2*cx/frameWidth - 1)
    if len(normalized) > 0:
        return apply(lambda a, b: a + b, normalized) / len(normalized)
    return -2

def main(camera = 0):
    vc = ntInit('VisionControl')
    cap = cv2.VideoCapture(camera)
    #cv2.namedWindow("Output")
    ret, frame = cap.read()
    print frame.shape[0]
    while ret:
        distanceSent = False
        ret, frame = cap.read()
        frame, contours = outline(T(frame, toGreenscale, brightPass, medianBlur))
        contours = pairs(quads(contours))
        distance = distanceToCenter(contours, frame.shape[1])
        if abs(distance) <= 1:
            vc.putValue("detectedValue", distance)
            distanceSent = True
        logging.info(str((distance, distanceSent)))
        vc.putBoolean("targetLocked", distanceSent)
 #       cv2.drawContours(frame, contours, -1, (127), 3)
        #cv2.imshow("Output", frame)
        if(cv2.waitKey(30) & 0xFF == ord('q')):
            break
    cap.release()

if __name__ == "__main__":
    main(0 if len(sys.argv) < 2 else int(sys.argv[1]))
