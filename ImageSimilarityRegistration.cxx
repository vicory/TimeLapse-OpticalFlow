/*=========================================================================
 *
 *  Copyright Insight Software Consortium
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *         http://www.apache.org/licenses/LICENSE-2.0.txt
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 *
 *=========================================================================*/

// Adapted from ITK's ImageRegistration7 example

#include "itkImageRegistrationMethodv4.h"
#include "itkMeanSquaresImageToImageMetricv4.h"
#include "itkMattesMutualInformationImageToImageMetricv4.h"
#include "itkCorrelationImageToImageMetricv4.h"
#include "itkRegularStepGradientDescentOptimizerv4.h"


#include "itkCenteredTransformInitializer.h"


#include "itkCenteredSimilarity2DTransform.h"

#include "itkImageMaskSpatialObject.h"
#include "itkImageFileReader.h"
#include "itkImageFileWriter.h"
#include "itkRGBPixel.h"
#include "itkRGBToLuminanceImageFilter.h"

#include "itkVectorResampleImageFilter.h"
#include "itkCastImageFilter.h"
#include "itkSubtractImageFilter.h"
#include "itkRescaleIntensityImageFilter.h"
#include "itkIdentityTransform.h"


int main( int argc, char *argv[] )
{
  if( argc < 5 )
    {
    std::cerr << "Missing Parameters " << std::endl;
    std::cerr << "Usage: " << argv[0];
    std::cerr << " fixedImageFile  movingImageFile ";
    std::cerr << " maskImageFile  outputImagefile";
    std::cerr << std::endl;
    return EXIT_FAILURE;
    }

  const    unsigned int    Dimension = 2;
  typedef  float           PixelType;
  typedef  itk::RGBPixel<unsigned char> RGBPixelType;
  
  typedef itk::Image< RGBPixelType, Dimension >  RGBImageType;

  typedef itk::Image< PixelType, Dimension > ImageType;

  typedef itk::CenteredSimilarity2DTransform< double > TransformType;

  typedef itk::RegularStepGradientDescentOptimizerv4<double>         OptimizerType;
  typedef itk::MeanSquaresImageToImageMetricv4< ImageType, ImageType >    MetricType;
  // typedef itk::CorrelationImageToImageMetricv4< ImageType, ImageType >    MetricType;
  typedef itk::ImageRegistrationMethodv4< ImageType,
                                          ImageType,
                                          TransformType >            RegistrationType;

  TransformType::Pointer  transform = TransformType::New();

  typedef itk::ImageFileReader< RGBImageType  > FixedImageReaderType;
  typedef itk::ImageFileReader< RGBImageType > MovingImageReaderType;

  FixedImageReaderType::Pointer  fixedImageReader  = FixedImageReaderType::New();
  MovingImageReaderType::Pointer movingImageReader = MovingImageReaderType::New();

  fixedImageReader->SetFileName(  argv[1] );
  movingImageReader->SetFileName( argv[2] );

  typedef itk::RGBToLuminanceImageFilter<RGBImageType, ImageType> RGB2GrayType;

  RGB2GrayType::Pointer fixedrgb2gray = RGB2GrayType::New();
  fixedrgb2gray->SetInput(fixedImageReader->GetOutput());
  fixedrgb2gray->Update();
  ImageType::Pointer fixedImage = fixedrgb2gray->GetOutput();

  RGB2GrayType::Pointer movingrgb2gray = RGB2GrayType::New();
  movingrgb2gray->SetInput(movingImageReader->GetOutput());
  movingrgb2gray->Update();
  ImageType::Pointer movingImage = movingrgb2gray->GetOutput();

  typedef itk::Image<unsigned char, Dimension> ImageMaskType;
  typedef itk::ImageFileReader<ImageMaskType> MaskReaderType;
  MaskReaderType::Pointer maskReader = MaskReaderType::New();
  maskReader->SetFileName(argv[3]);
  maskReader->Update();

  typedef itk::ImageMaskSpatialObject<Dimension> MaskType;
  MaskType::Pointer spatialObjectMask = MaskType::New();

  spatialObjectMask->SetImage(maskReader->GetOutput());

  RegistrationType::Pointer   registration  = RegistrationType::New();

  registration->SetFixedImage( fixedImage );
  registration->SetMovingImage( movingImage );

  MetricType::Pointer         metric        = MetricType::New();
  // metric->SetFixedImageMask(spatialObjectMask);
  registration->SetMetric(        metric        );

  OptimizerType::Pointer      optimizer     = OptimizerType::New();
  registration->SetOptimizer(     optimizer     );

  typedef itk::CenteredTransformInitializer<
    TransformType,
    ImageType,
    ImageType > TransformInitializerType;

  TransformInitializerType::Pointer initializer
                                      = TransformInitializerType::New();

  initializer->SetTransform( transform );

  initializer->SetFixedImage( fixedImage );
  initializer->SetMovingImage( movingImage );

  initializer->MomentsOn();

  initializer->InitializeTransform();

  double initialScale = 1.0;
  double initialAngle = 0.0;

  transform->SetScale( initialScale );
  transform->SetAngle( initialAngle );

  registration->SetInitialTransform( transform );
  registration->InPlaceOn();
  
  typedef OptimizerType::ScalesType       OptimizerScalesType;
  OptimizerScalesType optimizerScales( transform->GetNumberOfParameters() );
  const double translationScale = 1.0 / 100.0;

  optimizerScales[0] = 10.0;
  optimizerScales[1] =  1.0;
  optimizerScales[2] =  translationScale;
  optimizerScales[3] =  translationScale;
  optimizerScales[4] =  translationScale;
  optimizerScales[5] =  translationScale;

  optimizer->SetScales( optimizerScales );

  double steplength = 1.0;

  optimizer->SetLearningRate( steplength );
  optimizer->SetMinimumStepLength( 0.0001 );
  optimizer->SetNumberOfIterations( 500 );

  const unsigned int numberOfLevels = 1;

  RegistrationType::ShrinkFactorsArrayType shrinkFactorsPerLevel;
  shrinkFactorsPerLevel.SetSize( 1 );
  shrinkFactorsPerLevel[0] = 1;

  RegistrationType::SmoothingSigmasArrayType smoothingSigmasPerLevel;
  smoothingSigmasPerLevel.SetSize( 1 );
  smoothingSigmasPerLevel[0] = 0;

  registration->SetNumberOfLevels ( numberOfLevels );
  registration->SetSmoothingSigmasPerLevel( smoothingSigmasPerLevel );
  registration->SetShrinkFactorsPerLevel( shrinkFactorsPerLevel );


  try
    {
    registration->Update();
    std::cout << "Optimizer stop condition: "
              << registration->GetOptimizer()->GetStopConditionDescription()
              << std::endl;
    }
  catch( itk::ExceptionObject & err )
    {
    std::cerr << "ExceptionObject caught !" << std::endl;
    std::cerr << err << std::endl;
    return EXIT_FAILURE;
    }

  TransformType::ParametersType finalParameters =
                                  transform->GetParameters();


  const double finalScale           = finalParameters[0];
  const double finalAngle           = finalParameters[1];
  const double finalRotationCenterX = finalParameters[2];
  const double finalRotationCenterY = finalParameters[3];
  const double finalTranslationX    = finalParameters[4];
  const double finalTranslationY    = finalParameters[5];

  const unsigned int numberOfIterations = optimizer->GetCurrentIteration();

  const double bestValue = optimizer->GetValue();


  const double finalAngleInDegrees = finalAngle * 180.0 / itk::Math::pi;


  typedef itk::VectorResampleImageFilter< RGBImageType, RGBImageType > ResampleFilterType;
  ResampleFilterType::Pointer resampler = ResampleFilterType::New();

  resampler->SetTransform( transform );
  resampler->SetInput( movingImageReader->GetOutput() );

  resampler->SetSize( fixedImage->GetLargestPossibleRegion().GetSize() );
  resampler->SetOutputOrigin(  fixedImage->GetOrigin() );
  resampler->SetOutputSpacing( fixedImage->GetSpacing() );
  resampler->SetOutputDirection( fixedImage->GetDirection() );
  // resampler->SetDefaultPixelValue( 0 );

  typedef  unsigned char  OutputPixelType;

  typedef itk::Image< OutputPixelType, Dimension > OutputImageType;

  typedef itk::CastImageFilter< ImageType, OutputImageType >
    CastFilterType;

  typedef itk::ImageFileWriter< RGBImageType >  WriterType;


  WriterType::Pointer      writer =  WriterType::New();

  writer->SetFileName( argv[4] );

  writer->SetInput( resampler->GetOutput() );
  writer->Update();

  return EXIT_SUCCESS;
}
