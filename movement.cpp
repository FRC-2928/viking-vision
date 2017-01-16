#include "movement.h"
using namespace cv;
using namespace cv::xfeatures2d;

Point targetCenter(contour_t contour)
{
	// Requires the contour to be
	// 0 1
	// 4 3
	// For example, bounding boxes converted to contours.
	// Otherwise, things will break and the robot will catch fire.
	return Point(contour[3].x - contour[0].x, contour[3].y - contour[0].x);
}
