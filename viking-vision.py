#!/usr/bin/env python2

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
    return cv2.GaussianBlur(src, (13, 13), 40)

def blobbify(src):
    data = src.flat
    dims = src.shape
    print dims
    for i in range(0, len(data)):
        if data[i] > 1:
            cv2.ellipse(src, (i % dims[0], i // dims[0]), (15, 6), 90, 0, 360, 0xFF, -1)
    return src

def outline(src):
    dst = np.zeros(src.shape, np.uint8)
    im2, contours, hierarchy  = cv2.findContours(src, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(dst, contours, -1, (255), 1)
    return dst, contours

def quads(contours):
    heightWidthRatio = 3
    tolerance = 1
    boxes = []
    polys = []
    for c in contours:
        polys.append(cv2.approxPolyDP(c, 5, True))
    polys = filter(lambda c: len(c) == 4, polys)
    return polys

def main(camera = 0):
    #vc = ntInit('VisionControl')
    ret = True
    cap = cv2.VideoCapture(camera)
    cv2.namedWindow("Output")
    while ret:
        ret, frame = cap.read()
        frame, contours = outline(T(frame, toGrayscale, brightPass, blur))
        contours = quads(contours)
        cv2.drawContours(frame, contours, -1, (127), 3)
        cv2.imshow("Output", frame)
        #vc.putNumber("frameSum", frame.sum()/255)
        print frame.sum()/255
        if(cv2.waitKey(30) & 0xFF == ord('q')):
            break
    cap.release()
if __name__ == "__main__":
    main()
