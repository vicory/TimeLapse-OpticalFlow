find_package( OpenCV REQUIRED )

find_package( ITK REQUIRED )
include( ${ITK_USE_FILE} )

set( reg_srcs ImageSimilarityRegistration.cxx )
add_executable( ImageSimilarityRegistration ${reg_srcs} )
target_link_libraries( ImageSimilarityRegistration ${ITK_LIBRARIES} )

set( interp_srcs InterpByOpticalFlow.cxx )
add_executable( InterpByOpticalFlow ${interp_srcs} )
target_link_libraries( InterpByOpticalFlow ${OpenCV_LIBS} )
