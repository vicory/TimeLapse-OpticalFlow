#! /bin/sh -f 
rm -rf ${1}/tmp
rm -rf ${1}/tmpOutput
mkdir ${1}/tmp
mkdir ${1}/tmpOutput

python timeLapseRegistrator.py --glob "*.jpg" --convert /c/Program\ Files/ImageMagick-7.0.3-Q16/convert.exe --maskFile ${1}/mask.jpg --tmpDir ${1}/tmp ${1}/input ${1}/tmpOutput
python timeLapseOpticFlowInterpolator.py --glob "*_RegAtlas.png" --interp /c/src/TimeLapse-OpticalFlow-Release/InterpByOpticalFlow.exe ./${1}/tmpOutput
python timeLapseMovieMaker.py --convert /c/Program\ Files/ImageMagick-7.0.3-Q16/convert.exe --glob "*_RegAtlas_?.png" ${1}/tmpOutput ${1}/movie.gif
convert -coalesce ${1}/movie.gif ${1}/tmp/movie%04d.png
ffmpeg -r 10 -i ${1}/tmp/movie%04d.png -vcodec mpeg4 -y ${1}/movie.mp4

rm -rf ${1}/tmpOutputOrg
cp -r ${1}/input ${1}/tmpOutputOrg

python timeLapseOpticFlowInterpolator.py --glob "*.jpg" --interp /c/src/TimeLapse-OpticalFlow-Release/InterpByOpticalFlow.exe ${1}/tmpOutputOrg
python timeLapseMovieMaker.py --convert /c/Program\ Files/ImageMagick-7.0.3-Q16/convert.exe --glob "*_?.jpg" ${1}/tmpOutputOrg ${1}/movie-org.gif
convert -coalesce ${1}/movie-org.gif ${1}/tmpOutputOrg/movie-org%04d.png
ffmpeg -r 10 -i ${1}/tmpOutputOrg/movie-org%04d.png -vcodec mpeg4 -y ${1}/movie-org.mp4
