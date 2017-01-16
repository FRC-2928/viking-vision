#include "quad-filter.h"

using namespace cv;
using namespace cv::xfeatures2d;

contour_t rectToContour(Rect rect)
{
	contour_t contour;
	contour.push_back(Point(rect.x, rect.y));
	contour.push_back(Point(rect.x + rect.width, rect.y));
	contour.push_back(Point(rect.x + rect.width, rect.y + rect.height));
	contour.push_back(Point(rect.x, rect.y + rect.height));
	return contour;
}

contours_t boundingBoxes(contours_t contours, double heightWidthRatio, double tolerance)
{
	contours_t boxes;
	Rect box;
	for (int i = 0; i < contours.size(); i++)
	{
		box = boundingRect(contours[i]);
		if (abs((double)box.height/box.width - heightWidthRatio) <= tolerance)
		{
			boxes.push_back(rectToContour(box));
		}
	}
	return boxes;
}

contours_t pairs(contours_t contours, double tolerance)
{
	double iArea, jArea;
	contours_t output;
	std::vector<bool> paired(contours.size(), false);
	for (int i = 0; i < contours.size(); i++)
	{
		if (paired[i])
		{
			continue;
		}
		double iArea = contourArea(contours[i]);
		for (int j = 0; j < contours.size(); j++)
		{
			if (i == j || paired[j])
			{
				continue;
			}
			double jArea = contourArea(contours[j]);
			if ((abs(max(iArea, jArea)/min(iArea, jArea)) - 1) <= tolerance)
			{
				paired[j] = true;
				paired[i] = true;
			}
		}
	}
	for (int i = 0; i < paired.size(); i++)
	{
		if (paired[i])
		{
			output.push_back(contours[i]);
		}
	}
	return output;
}
