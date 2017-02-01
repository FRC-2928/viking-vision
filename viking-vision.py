#!/usr/bin/env python2
from __future__ import division
import sys

import cv2
import sys
import numpy as np
#from networktables import NetworkTables
import logging
logging.basicConfig(level=logging.DEBUG)

ip = "10.29.28.2"

'''def ntInit(table):
    NetworkTables.initialize(ip)
    return NetworkTables.getTable(table)'''

# From http://stackoverflow.com/questions/4961017/clojure-style-function-threading-in-python
def T(*args):
    return reduce(lambda l, r: r(l), args)

def toGrayscale(src):
    return cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)

def brightPass(src):
    return cv2.inRange(src, 230, 255)

def blur(src):
    return cv2.GaussianBlur(src, (15, 15), 60)

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
    heightWidthRatio = 5/2
    tolerance = 0.75
    output = []
    boxes = []
    polys = [cv2.approxPolyDP(c, 5, True) for c in contours]
    polys = filter(lambda c: len(c) == 4, polys)
    for p in polys:
        _, _, w, h = cv2.boundingRect(p)
        boxes.append(abs(h/w - heightWidthRatio) <= tolerance)
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
            if abs(max(areas[i], areas[j])/min(areas[i], areas[j])) - 1 <= 1.5:
                outputMask[i] = True
                outputMask[j] = True
    for i in range(len(areas)):
        if outputMask[i]:
            output.append(contours[i])
    return output

def distanceToCenter(contours, frameWidth):
    centerx = int(frameWidth / 2)
    centery = int(frameHeight / 2)
    moments = [cv2.moments(c) for c in contours]
    xaverage, count = 0, 0;
    for m in moments:
        cx = m['m10'] / m['m00']
        xaverage += cx
        count++
    if count == 0:
        return -2 # Out of range
    xaverage /= count

    return 2 * (xaverage - centerx) / frameWidth - 1

def main(camera = 0):
    vc = ntInit('VisionControl')
    cap = cv2.VideoCapture(camera)
    #cv2.namedWindow("Output")
    ret, frame = cap.read()
    while ret:
        ret, frame = cap.read()
        frame, contours = outline(T(frame, toGrayscale, brightPass, blur))
        contours = pairs(quads(contours))
        distance = distanceToCenter(contours, frame.cols)
        if abs(distance) =< 1:
            vc.putDouble("detectedValue", distance)
        #cv2.drawContours(frame, contours, -1, (127), 3)
        #cv2.imshow("Output", frame)
        #vc.putNumber("frameSum", frame.sum()/255)
        if(cv2.waitKey(30) & 0xFF == ord('q')):
            break
    cap.release()

if __name__ == "__main__":
    main(0 if len(sys.argv) < 2 else int(sys.argv[1]))
