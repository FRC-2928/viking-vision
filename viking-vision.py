#byVisionDaddy
#!/usr/bin/env python2
from __future__ import division
import sys
import argparse
import cv2
import sys
import numpy as np
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
        return sum(normalized) / len(normalized)
    return -2

def degreesToCenter(contours, frameWidth):
    distances = []
    for m in [cv2.moments(c) for c in contours][:2]:
        cx = int(m['m10'] / m['m00'])
        distances.append(cx)
    if len(distances) > 0:
        distance = sum(distances) / len(distances)
        return (distance / frameWidth * 61) - 30.5
    return -2
        

def blobFilter(src):
    params = cv2.SimpleBlobDetector_Params()
    params.minThreshold = 0
    params.maxThreshold = 0xFF
    params.filterByArea = True
    params.minArea = 125
    params.maxArea = 10000
    params.filterByCircularity = True
    params.minCircularity = 0.5
    params.maxCircularity = 0.95
    params.filterByColor = False
    params.filterByConvexity = True
    params.minConvexity = 0.6
    params.maxConvexity = 1
    params.filterByInertia = True
    params.minInertiaRatio = 0
    params.maxInertiaRatio = 0.6
    params.minDistBetweenBlobs = 0
    detector = cv2.SimpleBlobDetector_create(params)
    keypoints = detector.detect(src)
    keypoints.sort(key = lambda kp: kp.size)
    keypoints = keypoints[:2]
    print keypoints
    return keypoints

def main(camera, display, haveNetworktables):
    if haveNetworktables:
        vc = ntInit('VisionControl')
    if display:
        cv2.namedWindow("Output")
    cap = cv2.VideoCapture(camera)
    ret, frame = cap.read()
    print frame.shape[0]
    distance, oldDistance = 0, 0
    while ret:
        distanceSent = False
        ret, frame = cap.read()
        frame = T(frame, toGreenscale, brightPass, medianBlur)
        '''frame, contours = outline(frame)
        contours = pairs(quads(contours))
        distance = distanceToCenter(contours, frame.shape[1])'''
        keypoints = blobFilter(frame)
        oldDistance = distance
        if len(keypoints) >= 1:
            distance = 61 * sum([kp.pt[0] for kp in keypoints]) / frame.shape[1] - 30.5
            oldDistance = distance * .65 + oldDistance * .35
        else:
            distance = oldDistance
        if abs(distance) <= 1:
            if haveNetworktables:
                vc.putValue("detectedValue", distance)
            distanceSent = True
        logging.info(str((distance, distanceSent)))
        if haveNetworktables:
            vc.putBoolean("targetLocked", distanceSent)
        if display:
            cv2.drawKeypoints(frame, keypoints, frame, 0x7F, cv2.DRAW_MATCHES_FLAGS_DRAW_OVER_OUTIMG)
            cv2.imshow("Output", frame)
        if(cv2.waitKey(30) & 0xFF == ord('q')):
            break
    cap.release()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vision tracking script for FRC team 2928.")
    parser.add_argument("camera", help="camera input to use", type=int, default=0, nargs="?")
    parser.add_argument("-d", "--debug", help="displays the processed video feed (requires X Windows)", action="store_true")
    parser.add_argument("-n", "--no-networktables", help="disables networktables", action="store_true")
    args = parser.parse_args()
    if not args.no_networktables:
        from networktables import NetworkTables
    main(args.camera, args.debug, not args.no_networktables)
