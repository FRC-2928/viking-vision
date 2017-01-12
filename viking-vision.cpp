#include <iostream>
#include <opencv2/opencv.hpp>
#include <opencv2/xfeatures2d.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/videoio.hpp>
using namespace cv;
using namespace cv::xfeatures2d;

// Grayscale
// Threshhold
// Blobbify
// Outline
// Identify quads / Image matching

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

Mat outline(Mat src, bool colorShift = false)
{
	Mat dst(src.rows, src.cols, CV_8U, Scalar(0));
	dst.zeros(dst.rows, dst.cols, CV_8U);
	std::vector<std::vector<Point>> contours;
	findContours(src, contours, CV_RETR_LIST, CV_CHAIN_APPROX_SIMPLE);
	for (int i = 0; i < contours.size(); i++)
	{
		drawContours(dst, contours, i, Scalar(colorShift ? (42*i)%255 : 255), 1);
	}
	std::cout << contours << std::endl;
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
		frame = brightPass(frame);
		frame = blobbify(frame, 5);
		frame = outline(frame);
		frame = quads(frame);

		imshow("Output", frame);
		if (waitKey(30) == 27)
		{
			return 0;
		}
	}
}
