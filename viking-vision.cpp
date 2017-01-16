#include <iostream>
#include <opencv2/opencv.hpp>
#include <opencv2/xfeatures2d.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/videoio.hpp>
#include "utildefs.h"
#include "quad-filter.h"

using namespace cv;
using namespace cv::xfeatures2d;

// Grayscale
// Threshhold
// Blobbify
// Outline
// Identify quads / Image matching

bool parallelogram(std::vector<Point>)
{
	return true;
}

Mat toGrayscale(Mat src)
{
	Mat dst;
	cvtColor(src, dst, COLOR_BGR2GRAY);
	return dst;
}

Mat brightPass(Mat src)
{
	Mat dst;
	inRange(src, Scalar(230), Scalar(255), dst);
	return dst;
}

Mat blur(Mat src)
{
	Mat dst;
	GaussianBlur(src, dst, Size(13, 13), 40);
	return dst;
}

Mat blobbify(Mat src, int radius)
{
	Mat dst(src.rows, src.cols, CV_8U, Scalar(0));
	for (int r = 0; r < dst.cols; r++) //WHY DOES THIS WORK WTF TODO: understand this
		for (int c = 0; c < dst.rows; c++)
		{
			if (src.data[r + c * dst.cols] > 1)
			{
				circle(dst, Point(r, c), radius, Scalar(src.data[r + c * dst.cols]), -1);
			}
		}
	return dst;
}

Mat outline(Mat src)
{
	Mat dst(src.rows, src.cols, CV_8U, Scalar(0));
	std::vector<std::vector<Point>> contours, polys;
	std::vector<Point> poly;
	findContours(src, contours, CV_RETR_LIST, CV_CHAIN_APPROX_NONE);
	for (int i = 0; i < contours.size(); i++)
	{
		approxPolyDP(contours[i], poly, 5, true);
		polys.push_back(poly);
	}
	for (int i = 0; i < polys.size(); i++)
	{
		if (polys[i].size() == 4)
		{
			drawContours(dst, polys, i, Scalar(0xFF));
			circle(dst, polys[i][0], 3, Scalar(0xFF));
		}
	}
	dst = Mat::zeros(dst.rows, dst.cols, CV_8U);
	drawContours(dst, pairs(boundingBoxes(polys, (double)5/2, .5), 0.75), -1, Scalar(0xFF));
	return dst;
}

Mat quads(Mat src)
{
	return src;
}

int main(int argc, char** argv)
{
	VideoCapture cap;
	Mat frame;
	if (argc > 1 && !strcmp(argv[1], "-h"))
	{
		std::cout << "Usage: viking-vision <device>\ndevice defaults to 0" << std::endl;
		return 0;
	}

	if (argc > 1)
	{	
		cap = VideoCapture(atoi(argv[1]));
	} else
	{
		cap = VideoCapture(0);
	}

	if (!cap.isOpened())
	{
		std::cerr << "Failed to open device " << atoi(argv[1]) << std::endl;
		return -1;
	}
	namedWindow("Output", WINDOW_AUTOSIZE);
	cap >> frame; //Throw away first frame
	while (true)
	{
		cap >> frame;
		frame = toGrayscale(frame);
		frame = blur(frame);
		frame = brightPass(frame);
		frame = outline(frame);
		//frame = blobbify(frame, 1);
		frame = quads(frame);

		imshow("Output", frame);
		if (waitKey(30) == 27)
		{
			return 0;
		}
	}
}
