#include <iostream>
#include <opencv2/opencv.hpp>
#include <opencv2/xfeatures2d.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/videoio.hpp>
#include "utildefs.h"

contour_t rectToContour(cv::Rect rect);
contours_t boundingBoxes(contours_t contours, double heightWidthRatio, double tolerance);
contours_t pairs(contours_t contours, double tolerance); 
