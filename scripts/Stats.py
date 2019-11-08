#!/usr/bin/python
#    Python 2.7   #
# Ludo 2019-10-16 #

import os,sys
import numpy as np
import collections
from osgeo import gdal
from osgeo import ogr
import infolog

log = infolog.infolog()

# print img.GetMetadata()
# stats = imgBand.GetStatistics( True, True )

# Path name of the classifcation raster

log.msg("Importing Classification Raster (it might take a while)")
imgFile  = sys.argv[1]
img = gdal.Open(imgFile)
imgBand = img.GetRasterBand(1)
npimg = np.array(imgBand.ReadAsArray())
log.msg(("Classification raster size: ",npimg.shape))

try:
    log.msg("Importing Mask Raster (it might take a while)")
    maskFile = sys.argv[2]
    mask = gdal.Open(maskFile)
    maskBand = img.GetRasterBand(1)
    npmask = np.array(maskBand.ReadAsArray())
    log.msg(("Classification mask size: ",npimg.shape))
    Qmask = True
except:
    Qmask = False
    pass


#log.msg("Counting classes - Counter method (it might take a while)")
#count = collections.Counter(cla_raster.flatten())
#log.msg("Counter Count:")
#for k in count:
#    print k,"\t->\t",count[k]

log.msg("Counting classification classes - Numpy method (it might take a while)")
imgClasses = np.unique(npimg)
log.msg("Classification classes:")
print imgClasses

if Qmask:
    log.msg("Counting mask classes - Numpy method (it might take a while)")
    maskClasses = np.unique(npmask)
    log.msg("Mask classes:")
    print imgClasses



#ncount = np.copy(imgClasses)
#for i,c in enumerate(classes):
#    ncount[i] = np.sum(np.equal(cla_raster,c))
#
#log.msg("Numpy Count:")
#for k,c in zip(classes,ncount):
#    print "\t",k,"\t->\t",c
#

