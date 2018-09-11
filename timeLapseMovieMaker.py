#!/usr/bin/python

# This program will convert sequence of images into a movie

import os
import imp
import fnmatch
import argparse
from subprocess import run

def ApplyTimeLapseMovieMaker( convert, folder, glob, speed, movie ):
    command_string = [convert, "-delay", speed, "-loop", "0"]
    for root, dirnames, filenames in os.walk( folder ):
        for filename in fnmatch.filter( filenames, glob ):
            command_string.append( str( os.path.join( root, filename ) ) )
        break  # Only use files in top level subdir
    command_string.append( movie )

    print( command_string )

    run( command_string )

if __name__ == '__main__':
    parser = argparse.ArgumentParser( 
        description='Apply timeLapseMovieMaker to files in a folder.' )
    parser.add_argument( 'folder', help='Folder to apply the script to.' )
    parser.add_argument( 'movie', help='Output movie name.' )
    parser.add_argument( '--convert',
        help='Path to the convert executable from ImageMagick.',
        default='convert' )
    parser.add_argument( '--glob',
        help='Glob to find files recursively in the given folder.',
        default='*.???' )
    parser.add_argument( '--speed',
        help='playback speedup.',
        default='10' )
    args = parser.parse_args()
    ApplyTimeLapseMovieMaker( args.convert, args.folder, args.glob,
        args.speed, args.movie )
