#!/usr/bin/env python2
from __future__ import division # int/int = float
import sys
import collections
import argparse
import cv2
import sys
import numpy as np
import logging
# Constants
BLUR_SIZE = (11, 11) # Size for the gaussian blur (not used)
BLUR_FACTOR = 90 # Blur factor for the gaussian blur (not used)
GREEN_LOWER_LIMIT = 235 # Lower threshold for the green 
MEDIAN_BLUR_SIZE = 5 # Size for the median blur, which we are currently using
HEIGHT_WIDTH_RATIO = 5/2 # Ratio of the height and width of the gear target
HEIGHT_WIDTH_TOLERANCE = .85 # tolerance for the ratio (accounts for the angle of the robot and general measurement errors). Currently not used with the blob algorithm
AREA_TOLERANCE = 1.7 # tolerance for the ratio of the areas of selected contours to detirmine if they're pairs. Currently not used with the blob algorithm 
VISION_DEADZONE = (0.3, 0.3) # 30% off the top and bottom when choosing blobs
logging.basicConfig(level=logging.DEBUG)


def ntInit(table, ip):
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

def outline(src):
    dst = np.zeros(src.shape, np.uint8)
    im2, contours, hierarchy  = cv2.findContours(src, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(dst, contours, -1, (255), 1)
    return dst, contours

def quads(contours):
    output = []
    boxes = []
    polys = [cv2.approxPolyDP(c, 5, True) for c in contours]
    polys = filter(lambda c: len(c) == 4, polys) # extract quadrilaterals
    for p in polys:
        _, _, w, h = cv2.boundingRect(p) # get the width and height of the bounding boxes, which is similar enough to the quadrilaterals and much easier to deal with
        boxes.append(abs(h/w - HEIGHT_WIDTH_RATIO) <= HEIGHT_WIDTH_TOLERANCE)
    for i in range(len(boxes)):
        if boxes[i]:
            output.append(polys[i])
    return output

def pairs(contours):
    areas = [cv2.contourArea(c) for c in contours]
    outputMask = [False] * len(areas) # builds up an array to keep track of which contours to keep
    output = []
    '''Awful imperative code TODO: write something better
    The general algorithm for the following code is pretty simple. For every area, it looks for another unpaired area such
    that the ratio between them is within AREA_TOLERANCE. It runs in O(n^2) time (I think), so not awful, but the blobbing algorithm
    works much better and faster. When possible, use that instead.
    '''
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
    # Calculates the distance (normalized to be between [-1, 1]) of the x distance of the centers of the contours, ignoring the y positions
    moments = [cv2.moments(c) for c in contours][:2]
    normalized = []
    for m in moments:
        cx = int(m['m10'] / m['m00']) # Calculates the centroid of the contour. OpenCV docs don't explain this very well, unfortunately
        normalized.append(2*cx/frameWidth - 1)
    if len(normalized) > 0:
        return apply(lambda a, b: a + b, normalized) / len(normalized) # Averages the distances
    return -2

def blobFilter(src):
    params = cv2.SimpleBlobDetector_Params()
    # The next several lines just set parameters for the blob detection
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
    # Applies the deadzone
    keypoints = filter(lambda kp: VISION_DEADZONE[0] * src.shape[0] <= kp.pt[1] <= (1 - VISION_DEADZONE[1]) * src.shape[1], keypoints)
    # Take the largest 2 blobs
    keypoints.sort(key = lambda kp: kp.size)
    return keypoints[:2]

def main(camera, display, haveNetworktables, raw_feed, nt_suffix, address):
    if haveNetworktables:
        vc = ntInit('VisionControl', address)
    if display:
        cv2.namedWindow("Output")
    cap = cv2.VideoCapture(camera)
    ret, frame = cap.read()
    distance = 0
    previousDistances = collections.deque(maxlen = 3)
    while ret:
        distanceSent = False
        ret, frame = cap.read()
        if not ret:
            logging.error("Failed to read frame, aborting!")
            sys.exit(1)
        if raw_feed:
            feed = frame.copy()
        frame = T(frame, toGreenscale, brightPass, medianBlur)
        '''frame, contours = outline(frame)
        contours = pairs(quads(contours))
        distance = distanceToCenter(contours, frame.shape[1])'''
        keypoints = blobFilter(frame)
        if len(keypoints) >= 1:
            distance = sum([kp.pt[0] for kp in keypoints]) / frame.shape[1] - 1
            previousDistances.appendleft(distance)
        elif len(previousDistances) > 1:
            distance = sum(map(lambda a, b: a * b, previousDistances[:3], [0.5, 0.35, 0.15][:len(previousDistances)]))
        else:
            distance = -2
        if abs(distance) <= 1:
            if haveNetworktables:
                vc.putValue("detectedValue" + nt_suffix, distance)
            distanceSent = True
        logging.info(str((distance, distanceSent)))
        if haveNetworktables:
            vc.putBoolean("targetLocked" + nt_suffix, distanceSent)
        if display:
            cv2.drawKeypoints(frame, keypoints, frame, 0x7F, cv2.DRAW_MATCHES_FLAGS_DRAW_OVER_OUTIMG)
            cv2.imshow("Output", frame)
            if raw_feed:
                cv2.imshow("Output", feed)
        if(cv2.waitKey(30) & 0xFF == ord('q')):
            break
    cap.release()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vision tracking script for FRC team 2928.", epilog="When using NetworkTables and 2 seperate processes (for 2 cameras), be sure to set different suffixes. They should just be Left and Right, but double check the vision subsystem in the robot code just to be sure.")
    parser.add_argument("camera", help="camera input to use", type=int, default=0, nargs="?")
    parser.add_argument("-s", "--nt-suffix", help="suffix for NetworkTables keys", type=str, default="", nargs="?")
    parser.add_argument("-d", "--debug", help="displays the processed video feed (requires X Windows)", action="store_true")
    parser.add_argument("-n", "--no-networktables", help="disables networktables", action="store_true")
    parser.add_argument("-f", "--raw-feed", help="shows a raw camera feed", action="store_true")
    parser.add_argument("-a", "--address", help="IP address to use for the roborio", default="10.29.28.56", type=str, nargs="?")
    args = parser.parse_args()
    if not args.no_networktables:
        from networktables import NetworkTables
    main(args.camera, args.debug, not args.no_networktables, args.raw_feed, args.nt_suffix, args.address)
