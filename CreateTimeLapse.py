import os
import shutil
import subprocess
import sys

# Input assumption: a list of n filenames
# The first n-2 are the input images in order 
# The second to last is the mask
# The last is the output gif

command_dir = "/work/timelapse/interp/build/" # Location of executables
reg_command = "ImageSimilarityRegistration"
interp_command = "InterpByOpticalFlow"

convert_command = "/usr/bin/convert" #imagemagick convert binary
convert_args = "-delay 10 -loop 0"

out_dir = "/work/timelapse/out/" # Location to write images

def CreateTimeLapse():
    input_images = sys.argv[1:-2]
    mask_image = sys.argv[-2]
    out_image = sys.argv[-1]

    reg_images = DoSimilarityRegistration(input_images,mask_image)

    interp_images = DoOpticalFlow(reg_images)

    CreateGif(interp_images,out_image)

# Register all images to the first one
def DoSimilarityRegistration(images,mask):
    basename = os.path.basename(images[0])
    name,ext = os.path.splitext(basename)
    reg_images = [out_dir + name + "_reg" + ext]

    shutil.copy(images[0],reg_images[0])

    for i in range(1, len(images)):
        name,ext = os.path.splitext(os.path.basename(images[i]))
        out_file = out_dir + name + "_reg" + ext

        subprocess.call([command_dir + reg_command, images[0], images[i], mask, out_file])

        reg_images.append(out_file)

    return reg_images

# Use optical flow to interpolate between registered images
def DoOpticalFlow(images):
    interp_images = [images[0]]

    for i in range(0, len(images)-1):
        subprocess.call([command_dir + interp_command, images[i], images[i+1]])

        name,ext = os.path.splitext(images[i])
        for i in range(1,10):
            interp_images.append(name + "_" + str(i) + ext)
    
    interp_images.append(images[-1])

    return interp_images

# Create animated gif from interpolated images
def CreateGif(images,out_image):
    subprocess.call(convert_command + " " + convert_args + " " + 
                    " ".join(images) + " " + out_dir + out_image, shell=True)
        

if __name__ == "__main__":
    CreateTimeLapse()

