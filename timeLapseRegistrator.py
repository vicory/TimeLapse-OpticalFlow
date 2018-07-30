#!/usr/bin/python

#  This program will register a sequence of photographs to align a masked
#      region

import os
import imp
import fnmatch
import argparse
from subprocess import run
from shutil import copyfile

import itk

def ApplyTimeLapseRegistratorIteration( folder, glob, maskFile, tmpDir,
                                        convert, iteration, portion ):
    edge_scale = "5"

    file_list = []
    for root, dirnames, filenames in os.walk( folder ):
        for filename in fnmatch.filter( filenames, glob ):
            file_list.append( os.path.join( root, filename ) )
    number_of_files = len( file_list )

    print( "Number of files = " + str( number_of_files ) )
    
    #Make a training mask
    run( ["ImageMath", maskFile, "-M", "1", "10", "255", "0",
              "-a", "1", "-1", maskFile,
              "-a", "0.5", "1", maskFile,
              "-W", "0", tmpDir+"/maskPlus.mha" ] )
    run( [convert, "-separate", file_list[0], tmpDir+"/base.png" ] )
    run( ["EnhanceUsingDiscriminantAnalysis",
          "--saveBasisInfo", tmpDir+"/basis.mlda",
          "--objectId", "255,127",
          "--labelmap", tmpDir+"/maskPlus.mha",
          tmpDir+"/base-0.png,"+tmpDir+"/base-1.png,"+tmpDir+"/base-2.png",
          tmpDir+"/baseEnh"] )

    for i, input_file in enumerate( file_list ):

        baseFile = input_file
        if iteration == 0:
            curFile = input_file
        else:
            curFile = input_file + "-I" + str( iteration-1 ) + \
                      "_RegAtlas.png"
        run( [convert, "-separate", curFile, tmpDir+"/curFile.png" ] )

        print( "*** " + baseFile )

        if i>0 and i<number_of_files-1:
            preFile = file_list[0] + "-I" + str( iteration ) + \
                      "_RegAtlas.png"
            preMaskFile = file_list[0] + "-I" + str( iteration ) + \
                      "_Mask.png"
            if iteration == 0:
                postFile = file_list[i-1]
            else:
                postFile = file_list[i-1] + "-I" + str( iteration-1 ) + \
                      "_RegAtlas.png"

            # Blend color channels using basis
            run( [convert, "-separate", curFile, tmpDir+"/base.png" ] )
            run( ["EnhanceUsingDiscriminantAnalysis",
                  "--loadBasisInfo", tmpDir+"/basis.mlda",
                  "--objectId", "255,127",
                  tmpDir+"/base-0.png,"+tmpDir+"/base-1.png,"+tmpDir+"/base-2.png",
                  tmpDir+"/Temp1B"] )
            run( ["ImageMath", tmpDir+"/Temp1B.basis00.mha", "-b", edge_scale,
                 "-w", tmpDir+"/Temp1B.mha"] )

            #run( ["ImageMath", curFile, "-B", edge_scale, "1", "0", "-w",
                 #tmpDir+"/TempX.mha"] )
            #run( ["ImageMath", curFile, "-B", edge_scale, "1", "1", "-w",
                 #tmpDir+"/TempY.mha"] )
            #run( ["ImageMath", tmpDir+"/TempX.mha", "-a", "0.5", "0.5",
                 #tmpDir+"/TempY.mha",
                 #"-p", "0", "-w", tmpDir+"/Temp1B.mha"] )
            #run( ["EnhanceContrastUsingAHE", curFile,
                  #tmpDir+"/Temp1B.mha"] )
 
            run( [convert, "-separate", preFile, tmpDir+"/base.png" ] )
            run( ["EnhanceUsingDiscriminantAnalysis",
                  "--loadBasisInfo", tmpDir+"/basis.mlda",
                  "--objectId", "255,127",
                  tmpDir+"/base-0.png,"+tmpDir+"/base-1.png,"+tmpDir+"/base-2.png",
                  tmpDir+"/TempPreB"] )
            run( ["ImageMath", tmpDir+"/TempPreB.basis00.mha", "-b", edge_scale,
                 "-w", tmpDir+"/TempPreB.mha"] )
            #
            #run( ["ImageMath", preFile, "-B", edge_scale, "1", "0", "-w",
                 #tmpDir+"/TempX.mha"] )
            #run( ["ImageMath", preFile, "-B", edge_scale, "1", "1", "-w",
                 #tmpDir+"/TempY.mha"] )
            #run( ["ImageMath", tmpDir+"/TempX.mha", "-a", "0.5", "0.5",
                 #tmpDir+"/TempY.mha",
                 #"-p", "0", "-w", tmpDir+"/TempPreB.mha"] )
            #run( ["EnhanceContrastUsingAHE", preFile,
                  #tmpDir+"/TempPreB.mha"] )
 
            run( [convert, "-separate", postFile, tmpDir+"/base.png" ] )
            run( ["EnhanceUsingDiscriminantAnalysis",
                  "--loadBasisInfo", tmpDir+"/basis.mlda",
                  "--objectId", "255,127",
                  tmpDir+"/base-0.png,"+tmpDir+"/base-1.png,"+tmpDir+"/base-2.png",
                  tmpDir+"/TempPostB"] )
            run( ["ImageMath", tmpDir+"/TempPostB.basis00.mha", "-b", edge_scale,
                 "-w", tmpDir+"/TempPostB.mha"] )
            #run( ["ImageMath", postFile, "-B", edge_scale, "1", "0", "-w",
                 #tmpDir+"/TempX.mha"] )
            #run( ["ImageMath", postFile, "-B", edge_scale, "1", "1", "-w",
                 #tmpDir+"/TempY.mha"] )
            #run( ["ImageMath", tmpDir+"/TempX.mha", "-a", "0.5", "0.5",
                 #tmpDir+"/TempY.mha",
                 #"-p", "0", "-w", tmpDir+"/TempPostB.mha"] )
            #run( ["EnhanceContrastUsingAHE", postFile,
                  #tmpDir+"/TempPostB.mha"] )

            # Define the atlas (blurred) for the current file
            run( ["RegisterImages", tmpDir+"/TempPreB.mha",
                tmpDir+"/TempPostB.mha",
                "--resampledImage", tmpDir+"/AtlasB.mha",
                "--saveTransform", tmpDir+"/AtlasB.tfm",
                "--registration", "PipelineAffine",
                "--initialization", "ImageCenters",
                "--metric", "MeanSqrd",
                "--expectedRotation", "0.001",
                "--expectedScale", "0.01",
                "--expectedSkew", "0.0001",
                "--expectedOffset", "60",
                "--fixedImageMask", preMaskFile,
                "--affineSamplingRatio", "0.5",
                "--affineMaxIterations", "1000",
                "--rigidSamplingRatio", "0.5",
                "--rigidMaxIterations", "1000"] )
                #"--resampledImagePortion", "0.5",
                #"--skipInitialRandomSearch",
                #"--loadTransform", tmpDir+"/AtlasB.tfm",

            run( ["ImageMath", tmpDir+"/AtlasB.mha",
                "-a", "0.4", "0.6", tmpDir+"/TempPreB.mha",
                "-w", tmpDir+"/AtlasB.mha"] )

            # Register the pre image (blurred) to the atlas
            run( ["RegisterImages", tmpDir+"/TempPreB.mha",
                tmpDir+"/AtlasB.mha",
                "--resampledImage", tmpDir+"/AtlasBRegTempPreB.mha",
                "--saveTransform", tmpDir+"/AtlasBRegTempPreB.tfm",
                "--registration", "PipelineAffine",
                "--initialization", "ImageCenters",
                "--metric", "MeanSqrd",
                "--expectedRotation", "0.001",
                "--expectedScale", "0.01",
                "--expectedSkew", "0.0001",
                "--expectedOffset", "10",
                "--fixedImageMask", preMaskFile,
                "--affineSamplingRatio", "0.5",
                "--affineMaxIterations", "1000",
                "--rigidSamplingRatio", "0.5",
                "--rigidMaxIterations", "1000"] )
                #"--skipInitialRandomSearch",
                #"--loadTransform", tmpDir+"/AtlasBRegTempPreB.tfm",


            # Produce a mask for the atlas
            #   by applying the pre image to atlas transform to the
            #   pre image mask
            run( ["RegisterImages", tmpDir+"/AtlasB.mha", preMaskFile,
                "--resampledImage", tmpDir+"/MaskRegAtlasB.mha",
                "--loadTransform", tmpDir+"/AtlasBRegTempPreB.tfm",
                "--invertLoadedTransform", 
                "--interpolation", "NearestNeighbor",
                "--registration", "None",
                "--rigidMaxIterations", "0"] )
                #"--initialization", "None",

            # Register the current image (blurred) to the atlas
            run( ["RegisterImages", tmpDir+"/AtlasB.mha",
                tmpDir+"/Temp1B.mha",
                "--resampledImage", tmpDir+"/Temp1BRegAtlasB.mha",
                "--saveTransform", tmpDir+"/RegAtlas.tfm",
                "--resampledImagePortion", str( portion ),
                "--registration", "PipelineAffine",
                "--metric", "MeanSqrd",
                "--initialization", "ImageCenters",
                "--expectedRotation", "0.001",
                "--expectedScale", "0.01",
                "--expectedSkew", "0.0001",
                "--expectedOffset", "60",
                "--fixedImageMask", tmpDir+"/MaskRegAtlasB.mha",
                "--affineSamplingRatio", "0.5",
                "--affineMaxIterations", "1000",
                "--rigidSamplingRatio", "0.5",
                "--rigidMaxIterations", "1000"] )
                #"--skipInitialRandomSearch",
                #"--loadTransform", tmpDir+"/RegAtlas.tfm",

            # Apply the image to atlas transform to the current image (raw)
            run( [convert, "-separate", curFile, tmpDir+"/base.png" ] )
            run( ["RegisterImages", tmpDir+"/AtlasB.mha",
                tmpDir+"/base-0.png",
                "--resampledImage", tmpDir+"/RegAtlas-0.mha",
                "--loadTransform",tmpDir+"/RegAtlas.tfm",
                "--registration", "None",
                "--initialization", "None",
                "--rigidMaxIterations", "0"] )
            run( ["RegisterImages", tmpDir+"/AtlasB.mha",
                tmpDir+"/base-1.png",
                "--resampledImage", tmpDir+"/RegAtlas-1.mha",
                "--loadTransform",tmpDir+"/RegAtlas.tfm",
                "--registration", "None",
                "--initialization", "None",
                "--rigidMaxIterations", "0"] )
            run( ["RegisterImages", tmpDir+"/AtlasB.mha",
                tmpDir+"/base-2.png",
                "--resampledImage", tmpDir+"/RegAtlas-2.mha",
                "--loadTransform",tmpDir+"/RegAtlas.tfm",
                "--registration", "None",
                "--initialization", "None",
                "--rigidMaxIterations", "0"] )
            run( ["ImageMath", tmpDir+"/RegAtlas-0.mha",
                "-W", "0", tmpDir+"/RegAtlas-0.png"] )
            run( ["ImageMath", tmpDir+"/RegAtlas-1.mha",
                "-W", "0", tmpDir+"/RegAtlas-1.png"] )
            run( ["ImageMath", tmpDir+"/RegAtlas-2.mha",
                "-W", "0", tmpDir+"/RegAtlas-2.png"] )
            run( [convert, "-combine",
                tmpDir+"/RegAtlas-0.png",
                tmpDir+"/RegAtlas-1.png",
                tmpDir+"/RegAtlas-2.png",
                "-colorspace", "sRGB",
                "-type", "truecolor",
                baseFile + "-I" + str( iteration ) + "_RegAtlas.png"] )

            # Make the atlas make the registered current image mask
            run( ["ImageMath", tmpDir+"/MaskRegAtlasB.mha",
                "-W", "0",
                baseFile + "-I" + str( iteration ) + "_Mask.png"] )

        else:
            # First image we don't perform a registration
            run( [convert, baseFile,
                baseFile + "-I" + str( iteration ) + "_RegAtlas.png"] )
            run( [convert, maskFile,
                baseFile + "-I" + str( iteration ) + "_Mask.png"] )

            # Generate an identity transform
            #run( ["RegisterImages", baseFile, maskFile,
                #"--saveTransform", tmpDir+"/identity.tfm",
                #"--registration", "None",
                #"--initialization", "None",
                #"--rigidMaxIterations", "0"] )
            #copyfile( tmpDir+"/identity.tfm", tmpDir+"/AtlasB.tfm" )
            #copyfile( tmpDir+"/identity.tfm",
                #tmpDir+"/AtlasBRegTempPreB.tfm" )
            #copyfile( tmpDir+"/identity.tfm", tmpDir+"/MaskRegAtlasB.tfm" )
            #copyfile( tmpDir+"/identity.tfm", tmpDir+"/RegAtlas.tfm" )


def ApplyTimeLapseRegistrator( folder, glob, maskFile, tmpDir, convert ):
    # Make three registration passes through the data.
    ApplyTimeLapseRegistratorIteration( folder, glob, maskFile, tmpDir,
        convert, 0, 1.0 )
    #ApplyTimeLapseRegistratorIteration( folder, glob, maskFile, tmpDir,
         # convert, 1, 1.0 )
    #ApplyTimeLapseRegistratorIteration( folder, glob, maskFile, tmpDir,
         # convert, 2, 1.0 )

if __name__ == '__main__':
    parser = argparse.ArgumentParser( 
        description='Apply timeLapseRegistrator to files in a folder.' )
    parser.add_argument( 'folder', help='Folder to apply the script to.' )
    parser.add_argument( '--glob',
        help='Glob to find files recursively in the given folder.',
        default='*.???' )
    parser.add_argument( '--convert',
        help='Path to the convert executable from ImageMagick.',
        default='convert' )
    parser.add_argument( '--maskFile', help='File for masking ROI.',
        default='mask.png' )
    parser.add_argument( '--tmpDir', help='Folder for Temp files.',
        default='tmp' )
    args = parser.parse_args()
    ApplyTimeLapseRegistrator( args.folder, args.glob, args.maskFile,
        args.tmpDir, args.convert )
