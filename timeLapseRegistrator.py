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

def ApplyTimeLapseRegistrator( inDir, outDir, glob, maskFile, tmpDir, convert ):
    # TO DO: This scale should be proportional to the mask size or adjusted
    #   based on some similar logic
    edge_scale = "5"

    file_list = []
    filename_list = []
    for root, dirnames, filenames in os.walk( inDir ):
        for filename in fnmatch.filter( filenames, glob ):
            filename_list.append( filename )
            file_list.append( os.path.join( root, filename ) )
        break
    number_of_files = len( file_list )

    print( "Number of files = " + str( number_of_files ) )
    
    # Make a training mask
    #    Label pixels in the mask at 255 and pixels just outside that
    #    region as 127.
    run( ["ImageMath", maskFile, "-M", "1", "30", "255", "0",
        "-a", "1", "-1", maskFile,
        "-a", "0.5", "1", maskFile,
        "-W", "0", tmpDir+"/maskPlus.mha" ] )

    # Register everything with the time 0 image
    atlasFile = file_list[0]
    run( [convert, atlasFile, outDir + "/" + filename_list[0] + "_RegAtlas.png" ] )

    # Optimize use of color images
    #   Split the image into color channels and determine optimum 
    #   linear combination of color channels that best distinguish
    #   the pixels in the mask from the pixels just outside of the mask
    run( [convert, "-separate", atlasFile, tmpDir+"/base.png" ] )
    run( ["EnhanceUsingDiscriminantAnalysis",
        "--saveBasisInfo", tmpDir+"/basis.mlda",
        "--objectId", "255,127",
        "--labelmap", tmpDir+"/maskPlus.mha",
        tmpDir + "/base-0.png," + \
        tmpDir + "/base-1.png," + \
        tmpDir + "/base-2.png",
        tmpDir+"/atlasMasked"] )
    run( ["EnhanceUsingDiscriminantAnalysis",
        "--loadBasisInfo", tmpDir+"/basis.mlda",
        "--objectId", "255,127",
        tmpDir + "/base-0.png," + \
        tmpDir + "/base-1.png," + \
        tmpDir + "/base-2.png",
        tmpDir+"/atlas"] )
    run( ["ImageMath", tmpDir+"/atlas.basis00.mha",
        "-b", edge_scale,
        "-w", tmpDir+"/atlasB.mha"] )

    # Create an registration ROI from the object of interest mask
    #   Dilate the mask file to create an interesting ROI for registration
    #   TO DO: Dilation should be proportional to the mask size or 
    #   some similar logic used to define this parameter
    run( ["ImageMath", maskFile, "-M", "1", "15", "255", "0",
        "-W", "0", tmpDir+"/maskDilate.jpg" ] )
    run( [convert, tmpDir+"/maskDilate.jpg", tmpDir + "/atlasMask.png"] )
    regMaskFile = tmpDir + "/atlasMask.png"

    # Generate an identity transform
    run( ["RegisterImages", atlasFile, maskFile,
        "--saveTransform", tmpDir+"/identity.tfm",
        "--registration", "None",
        "--initialization", "None",
        "--rigidMaxIterations", "0"] )
    copyfile( tmpDir+"/identity.tfm",
        tmpDir + "/" + filename_list[0] + "_RegAtlas.tfm" )

    for i, curFile in enumerate( file_list ):

        print( "*** " + curFile )

        if i>0:
            tmpCurFile = tmpDir + "/" + filename_list[i]
            outCurFile = outDir + "/" + filename_list[i]

            preTransformFile = tmpDir + "/" + filename_list[i-1] + "_RegAtlas.tfm"

            # Blend color channels using basis
            run( [convert, "-separate", curFile, tmpDir+"/base.png" ] )
            run( ["EnhanceUsingDiscriminantAnalysis",
                  "--loadBasisInfo", tmpDir+"/basis.mlda",
                  "--objectId", "255,127",
                  tmpDir + "/base-0.png," + \
                  tmpDir + "/base-1.png," + \
                  tmpDir + "/base-2.png",
                  tmpDir + "/cur"] )
            run( ["ImageMath", tmpDir+"/cur.basis00.mha",
                 "-b", edge_scale,
                 "-w", tmpDir + "/curB.mha"] )
 
            # Register the current image (blurred) to the atlas
            run( ["RegisterImages", tmpDir+"/AtlasB.mha",
                tmpDir+"/curB.mha",
                "--resampledImage", tmpCurFile + "_RegAtlasB.mha",
                "--saveTransform", tmpCurFile + "_RegAtlas.tfm",
                "--registration", "Affine",
                "--loadTransform", preTransformFile,
                "--initialization", "None",
                "--expectedRotation", "0.001",
                "--expectedScale", "0.01",
                "--expectedSkew", "0.0001",
                "--expectedOffset", "60",
                "--fixedImageMask", regMaskFile,
                "--affineSamplingRatio", "0.5",
                "--affineMaxIterations", "1000",
                "--rigidSamplingRatio", "0.5",
                "--rigidMaxIterations", "1000"] )
                #"--metric", "MeanSqrd",

            # Apply the image to atlas transform to the current image (raw)
            run( ["RegisterImages", atlasFile,
                tmpDir+"/base-0.png",
                "--resampledImage", tmpDir+"/RegAtlas-0.mha",
                "--loadTransform",tmpCurFile + "_RegAtlas.tfm",
                "--registration", "None",
                "--initialization", "None",
                "--rigidMaxIterations", "0"] )
            run( ["RegisterImages", tmpDir+"/AtlasB.mha",
                tmpDir+"/base-1.png",
                "--resampledImage", tmpDir+"/RegAtlas-1.mha",
                "--loadTransform",tmpCurFile + "_RegAtlas.tfm",
                "--registration", "None",
                "--initialization", "None",
                "--rigidMaxIterations", "0"] )
            run( ["RegisterImages", tmpDir+"/AtlasB.mha",
                tmpDir+"/base-2.png",
                "--resampledImage", tmpDir+"/RegAtlas-2.mha",
                "--loadTransform",tmpCurFile + "_RegAtlas.tfm",
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
                outCurFile + "_RegAtlas.png"] )


if __name__ == '__main__':
    parser = argparse.ArgumentParser( 
        description='Apply timeLapseRegistrator to files in a folder.' )
    parser.add_argument( 'inputFolder', help='Folder to apply the script to.' )
    parser.add_argument( 'outputFolder', help='Folder to save the results to.' )
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
    ApplyTimeLapseRegistrator( args.inputFolder, args.outputFolder,
        args.glob, args.maskFile, args.tmpDir, args.convert )
