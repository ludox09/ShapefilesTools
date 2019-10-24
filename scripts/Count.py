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
cfile = sys.argv[1]
# Index of the classification layer/band in the raster (start at 1)
band = int(sys.argv[2])

log.msg("Importing Classification Raster (it might take a while)")
img = gdal.Open(cfile)
imgBand = img.GetRasterBand(band)
cla_raster = np.array(imgBand.ReadAsArray())
log.msg(("Classification raster size: ",cla_raster.shape))

#log.msg("Counting classes - Counter method (it might take a while)")
#count = collections.Counter(cla_raster.flatten())
#log.msg("Counter Count:")
#for k in count:
#    print k,"\t->\t",count[k]

log.msg("Counting classes - Numpy method (it might take a while)")
classes = np.unique(cla_raster)
ncount = np.copy(classes)
for i,c in enumerate(classes):
    ncount[i] = np.sum(np.equal(cla_raster,c))

log.msg("Numpy Count:")
for k,c in zip(classes,ncount):
    print "\t",k,"\t->\t",c


