#include <iostream>
#include <opencv2/opencv.hpp>

using namespace cv;
using namespace cv::features2d;

Mat blobbify(Mat src, int radius)
{
	Mat dst(src.rows, src.cols, CV_8U, Scalar(0));
	for (int r = 0; r < dst.cols; r++) //WHY DOES THIS WORK WTF TODO: understand this
		for (int c = 0; c < dst.rows; c++)
		{
			if (src.data[r + c * dst.cols] > 1)
			{
				ellipse(dst, Point(r, c), Size(radius, radius * 2 / 5), 90, 0, 360, Scalar(src.data[r + c * dst.cols]), -1);
			}
		}
	return dst;
}

int main(int argc, char **argv)
{
	Mat input;
	int rows, cols;
	if (argc != 3)
	{
		std::cout << "Usage: viking-vision-blobber rows cols" << std::endl;
		exit(0);
	}
	rows = atoi(argv[1]);
	cols = atoi(argv[2]);
	Mat input = new Mat(rows, cols, CV_8U);
	for (int i = 0; i < rows * cols; i++)
	{
		std::cin.read(Mat.data, rows * cols);
	}
	input = blobbify(input, 
