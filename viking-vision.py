#!/usr/bin/env python2
import cv2
import cv2.xfeatures2d
import sys
import numpy as np

# From http://stackoverflow.com/questions/4961017/clojure-style-function-threading-in-python
def T(*args):
    return reduce(lambda l, r: r(l), args)

def toGrayscale(src):
    return cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)

def brightPass(src):
    return cv2.inRange(src, 230, 255)

def blur(src):
    return cv2.GaussianBlur(src, (13, 13), 40)

'''def blobbify(src):
    data = src.flat
    dims = src.shape
    print dims
    for i in range(0, len(data)):
        if data[i] > 1:
            cv2.ellipse(src, (i % dims[0], i // dims[0]), (15, 6), 90, 0, 360, 0xFF, -1)
    return src'''

def outline(src):
    dst = np.zeros(src.shape, np.uint8)
    im2, contours, hierarchy  = cv2.findContours(src, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(dst, contours, -1, (255), 1)
    return dst

def main(camera = 0):
    filterPipeline = (toGrayscale, brightPass, blur, outline)
    ret = True
    cap = cv2.VideoCapture(camera)
    cv2.namedWindow("Output")
    while ret:
        ret, frame = cap.read()
        cv2.imshow("Output", T(frame, *filterPipeline)) 
        if(cv2.waitKey(30) & 0xFF == ord('q')):
            break
    cap.release()

main()
