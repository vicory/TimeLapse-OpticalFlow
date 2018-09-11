#!/usr/bin/python
import os
import fnmatch
import argparse
import shutil as sh
from subprocess import run

def ApplyTimeLapseOpticFlowInterpolator(folder, glob, interp):
    file_list = []
    for root, dirnames, filenames in os.walk(folder):
        for filename in fnmatch.filter(filenames, glob):
            file_list.append(os.path.join(root, filename))
        break # only use files in first subdir
    number_of_files = len(file_list)
    print("Number of files = " + str(number_of_files))
    for i, input_file in enumerate(file_list):
        fileName1 = input_file
        if i<number_of_files-1:
            fileName2 = file_list[i+1]
            run( [ interp, fileName1, fileName2 ] )

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Apply timeLapseInterpolator to files in a folder.')
    parser.add_argument('folder', help='Folder to apply the script to.')
    parser.add_argument('--interp',
        help='optic flow interpolator executable.',
        default='InterpByOpticalFlow.exe')
    parser.add_argument( '--glob',
        help='Glob to find files recursively in the given folder.',
        default='*.???')
    args = parser.parse_args()
    ApplyTimeLapseOpticFlowInterpolator(args.folder,
        args.glob, args.interp )
