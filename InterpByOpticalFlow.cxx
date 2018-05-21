#include "opencv2/imgproc.hpp"
#include "opencv2/highgui.hpp"
#include "opencv2/optflow.hpp"

#include "iostream"

// This code is adapted from https://github.com/Meltz014/ocv
int main(int argc, char *argv[])
{
    if (argc < 4)
    {
        std::cout << "Usage: " << argv[0] << " image1 image2 output_prefix" << std::endl;
        return EXIT_FAILURE;
    }
    // Read images in
	cv::Mat from, to, from_gray, to_gray;

	from = cv::imread(argv[1]);
	to = cv::imread(argv[2]);

	cv::cvtColor( from, from_gray, cv::COLOR_RGB2GRAY );
	cv::cvtColor( to, to_gray, cv::COLOR_RGB2GRAY );

    // Compute flows
    cv::Ptr<cv::DenseOpticalFlow> dof;
    cv::Mat flow_fw, flow_bw;

	dof = cv::optflow::createOptFlow_DeepFlow( );
	dof->calc(from_gray, to_gray, flow_fw);
    dof->calc(to_gray, from_gray, flow_bw);

    cv::Mat flowxy_fw[2], flowxy_bw[2];
    cv::split(flow_fw, flowxy_fw);
    cv::split(flow_bw, flowxy_bw);

    // Create output image
	cv::Mat out(from.rows, from.cols, CV_8SC3, cv::Scalar(0));

    cv::Mat out_fw, out_bw;

	cv::Vec3b pt_0;
	cv::Vec3b pt_1;
	double flow_x, flow_x_fw, flow_x_bw;
	double flow_y, flow_y_fw, flow_y_bw;

    int r_fw_new = 0;
    int c_fw_new = 0;
    int r_bw_new = 0;
    int c_bw_new = 0;

	int rows = from_gray.rows;
	int cols = from_gray.cols;
	int channels = from.channels( );

	double steps[] = {0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9};

	for (int i = 0; i < 9; i++)
	{
		double current_ti = steps[i];

        cv::addWeighted(from,(1.0f-current_ti),to,current_ti,0.0,out_fw);
        cv::addWeighted(from,(1.0f-current_ti),to,current_ti,0.0,out_bw);

    	for (int r = 0; r < rows; ++r) 
        {
    		for ( int c = 0; c < cols; ++c )
             {
                // forward flow
                flow_x_fw = flowxy_fw[ 0 ].at<float>( r, c );
                if ( std::isnan( flow_x_fw ) )
                {
                   flow_x_fw = 0.0f;
                }
                flow_y_fw = flowxy_fw[ 1 ].at<float>( r, c );
                if ( std::isnan( flow_y_fw ) )
                {
                   flow_y_fw = 0.0f;
                }

                // flow forward
                flow_x = current_ti*flow_x_fw;
                flow_y = current_ti*flow_y_fw;

                // compute new image locations
                r_fw_new = r + flow_y;
                c_fw_new = c + flow_x;

                // bounds checking
                c_fw_new = std::min( std::max( c_fw_new, 0 ), cols - 1 );
                r_fw_new = std::min( std::max( r_fw_new, 0 ), rows - 1 );

                cv::Vec3b input_pixel = from.at<cv::Vec3b>(r,c);
                cv::Vec3b out_pixel = out_fw.at<cv::Vec3b>(r_fw_new, c_fw_new);

                out_pixel[0] = input_pixel[0];
                out_pixel[1] = input_pixel[1];
                out_pixel[2] = input_pixel[2];

                out_fw.at<cv::Vec3b>(r_fw_new, c_fw_new) = out_pixel;

                // backward flow
                flow_x_bw = flowxy_bw[ 0 ].at<float>( r, c );
                if ( std::isnan( flow_x_bw ) )
                {
                   flow_x_bw = 0.0f;
                }
                flow_y_bw = flowxy_bw[ 1 ].at<float>( r, c );
                if ( std::isnan( flow_y_bw ) )
                {
                   flow_y_bw = 0.0f;
                }

                // flow backward
                flow_x = (1-current_ti)*flow_x_bw;
                flow_y = (1-current_ti)*flow_y_bw;

                // compute new image locations
                r_bw_new = r + flow_y;
                c_bw_new = c + flow_x;

                // bounds checking
                c_bw_new = std::min( std::max( c_bw_new, 0 ), cols - 1 );
                r_bw_new = std::min( std::max( r_bw_new, 0 ), rows - 1 );

                input_pixel = to.at<cv::Vec3b>(r,c);
                out_pixel = out_bw.at<cv::Vec3b>(r_bw_new, c_bw_new);

                out_pixel[0] = input_pixel[0];
                out_pixel[1] = input_pixel[1];
                out_pixel[2] = input_pixel[2];

                out_bw.at<cv::Vec3b>(r_bw_new, c_bw_new) = out_pixel;                

             }
        }

        cv::addWeighted(out_fw,(1.0f - current_ti),out_bw,current_ti,0.0,out);         

     std::stringstream outfile; 
     outfile << argv[3] << "_" << 10*current_ti << ".jpg";
     cv::imwrite(outfile.str(), out);

	}

    return EXIT_SUCCESS;

}