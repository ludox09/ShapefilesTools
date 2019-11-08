#!/usr/bin/python
#    Python 2.7   #
# Ludo 2019-10-16 #

import os,sys
import numpy as np
import pandas as pd
import collections
from osgeo import gdal
from osgeo import ogr
import infolog
import time

# Parmeters
log = infolog.infolog()
epsilon = 1e-10


def updatename(name,tag):
    """ Add tage to already define name """
    return name.split(".")[:-1][0] + "_%s"%(tag)  + "." + name.split(".")[-1] 

#parcel_out
def numpyrize(rasterizedfile, layer, nmin = None, nmax = None, verbose=False):
    log.msg("Opening Rasterized Shapefile %s (it might take a while)"%(rasterizedfile))
    
    if verbose:log.msg("gdal.Open()","DEBUG")
    raster = gdal.Open(rasterizedfile)
    
    if verbose:log.msg("parcels.GetRasterBand(1)","DEBUG")
    rasterdata = raster.GetRasterBand(layer)
   

    if verbose:log.msg("np.array(parcelsdata.ReadAsArray())","DEBUG")
    npraster = np.array(rasterdata.ReadAsArray())

    [x,y] = np.where(~np.equal(npraster,0))
    log.msg(("Rasterize Shapefile Size: ",npraster.shape))
    
    if verbose:log.msg("np.unique(parcels_raster)","DEBUG")
    rasterList = np.unique(npraster[x,y])


    if( (nmin != None) and (nmax == None) ):
        if verbose:log.msg(("Nmin = ", nmim))
        rasterList = rasterList[nmin:]

    if( (nmin == None) and (nmax != None) ):
        if verbose:log.msg(("Nmax = ", nmax))
        rasterList = rasterList[:nmax]

    if( (nmin != None) and (nmax != None) ):
        if verbose:log.msg(("Nmin = ", nmin,"Nmax = ", nmax))
        rasterList = rasterList[nmin:nmax]

    log.msg("Classes proportion in rasterize shapefile:")
    
    if verbose:log.msg("np.copy()","DEBUG")
    count = np.copy(rasterList)

    if verbose:log.msg("Counter loop","DEBUG")
    for i,c in enumerate(rasterList):
        count[i] = np.sum(np.equal(npraster,c))
    
    
    log.msg("Classes proportion in rasterize shapefile:")
    for k,c in zip(rasterList,count):
        print int(k),"\t->\t",int(c)
    
    if verbose:log.msg("Done","DEBUG")
    return npraster,rasterList,count 

def PrepareDataFrame(rasterizedfile, columns, nmin = None, nmax = None, verbose=False):
    log.msg("Prepare Profiles DataFrame:")
    if verbose:log.msg(" - Opening Rasterized Shapefile %s (it might take a while)"%(rasterizedfile),"DEBUG")

    # Open rasterized shapefile
    raster = gdal.Open(rasterizedfile)

    # extract layer information
    if verbose:log.msg("Get Rastrized layers:","DEBUG")
    layers = []
    for j,fi in enumerate(columns):
        if verbose:log.msg("    - %s"%(fi), "DEBUG")
        l = j+1
        rasterdata = raster.GetRasterBand(l) 
        layers.append(np.array(rasterdata.ReadAsArray()).astype(np.int))
  
    # Taeken time
    log.msg("Calculate valide parcel (X,Y) ","DEBUG")
    X = {}
    Y = {}
    wherelayer = np.where(np.greater(layers[0],0))
    print wherelayer
    for x,y in zip(wherelayer[0],wherelayer[1]):
        try:
           par = layers[0][x,y]
           X[par].append(x)
           Y[par].append(y)
        except:
           X[par] = [x]
           Y[par] = [y]


    # Numpy-ize DATA and PARCEL layer information
    if verbose:log.msg("Numpy-ize data layers","DEBUG")
    data_raster = np.asarray(layers)

    if verbose:log.msg("Numpy-ize parcel layer","DEBUG")
    parcel_raster = layers[0]
    parcelsList = X.keys()

    # Restric parcels range for debuging
    if( (nmin != None) and (nmax == None) ):
        if verbose:log.msg(("Nmin = ", nmim), "DEBUG")
        parcelsList = parcelsList[nmin:]

    elif( (nmin == None) and (nmax != None) ):
        if verbose:log.msg(("Nmax = ", nmax), "DEBUG")
        parcelsList = parcelsList[:nmax]

    elif( (nmin != None) and (nmax != None) ):
        if verbose:log.msg(("Nmin = ", nmin,"Nmax = ", nmax), "DEBUG")
        parcelsList = parcelsList[nmin:nmax]
    else:
        parcelsList = parcelsList[1:]

    # Create and feel database
    columns.append("NPIXELS")
    profilesBase = pd.DataFrame([],columns = columns)
 
    log.msg("DEBUT SCANING","DEBUG")
    for i,p in enumerate(parcelsList):
        #log.msg("Parcel %d"%(p),"DEBUG")

        #log.msg("Get (X,Y)","DEBUG")
        [x,y] = [X[p],Y[p]]
        npixel = len(x)
        #[x,y] = np.where(np.equal(parcel_raster,p))

        #log.msg("    DataVector","DEBUG")
    #   # Mettre bon commentaire !!!
        DataVector = data_raster[:,x[0],y[0]]

        #log.msg("    Append","DEBUG")
        DataVector = np.append(DataVector,npixel)

        #log.msg("    loc[i]","DEBUG")
        profilesBase.loc[i] = DataVector

    log.msg("END SCANING","DEBUG")
    return X, Y, parcel_raster, parcelsList, profilesBase

def npprimitive(img,t,prim):
    if prim == "NDVI":
        B4pos = 10*t + 2 + 1
        B8pos = 10*t + 6 + 1
        B4img = img.GetRasterBand(B4pos)
        B8img = img.GetRasterBand(B8pos)
        log.msg("Get B4","DEBUG")  
        B4 = np.array(B4img.ReadAsArray()).astype(np.float)

        log.msg("Get B8","DEBUG")  
        B8 = np.array(B8img.ReadAsArray()).astype(np.float)

        log.msg("Calculate NDVI","DEBUG")  
        NDVI = (B8 - B4)/(B4 + B8 + epsilon)
        return NDVI

    if prim == "SOIL":
        SoilImg = img.GetRasterBand(1)
        return Val

 

def getSoilStat(p,X,Y,soilClasses,npprim):
        [x,y] = [X[p],Y[p]]
        masked = npprim[x,y]

        # Numpy
        soilStat1 = np.sum(np.equal(masked[:,np.newaxis],soilClasses[np.newaxis,:]), axis = 0)

        return soilStat1


# Main #
profilesName= sys.argv[1]
parcelshapefileName = sys.argv[2]
soilshapefileName = sys.argv[3]
newprofilesName = updatename(profilesName,"soil")

log.msg("Load profiles")
profiles = pd.read_pickle(profilesName)

# Prepare Image raster reading
log.msg("Open Soil Stack %s (it might take a while)"%(soilshapefileName))
soilObject = gdal.Open(soilshapefileName)
soilData = soilObject.GetRasterBand(1)
soil = np.array(soilData.ReadAsArray()).astype(np.int)

log.msg("Get Soil classe (it might take a while)")
soilClasses = np.unique(soil)

log.msg("Soil classes:")
log.msg(soilClasses)


log.msg("Numpyze parcel raster (it might take a while)")
fieldList = ["I17"]
#X, Y, npparcels, parcelsList, parcelsdf = PrepareDataFrame(parcelshapefileName, fieldList, verbose = False,nmin = 1000,nmax = 1020)
X, Y, npparcels, parcelsList, parcelsdf = PrepareDataFrame(parcelshapefileName, fieldList, verbose = False)

# Add relevant colums to profiles df

StrCol = []
for sc in soilClasses:
    scStr = "soil_%d"%(sc) 
    #parcelsdf[scStr] = np.nan
    parcelsdf[scStr] = 0
    StrCol.append(scStr)

#print(profiles.info())
#print(parcelsdf)

###npprim = npprimitive(img,t,prim)
for i,p in enumerate(parcelsList):
    log.msg("Parcel %d"%(p),"DEBUG")

    SoilStat = getSoilStat(p,X,Y,soilClasses,soil)
    #parcelsdf.at[i,StrCol] = meansoil
    #parcelsdf.loc[i,StrCol] = np.array([i,p,12,21,23,24,25,31,32,43])
    parcelsdf.loc[i,StrCol] = SoilStat

    #try:
    #    profiles[int(p)][1].append(meanprim)
    #    profiles[int(p)][2].append(stdprim)
    #except:
    #    profiles[int(p)] = [[meanprim],[stdprim]]

log.msg("Merge dataframe")
mergeProfiles = pd.merge(profiles, parcelsdf, on='I17')

log.msg("Export soil %s"%(newprofilesName))
mergeProfiles.to_pickle(newprofilesName)

log.msg("Done")
#log.msg("Export to file")
#np.savez("Profiles-%s"%(prim), classes_list = classes_list, profiles = profiles)
#log.msg("Done")


#log.msg("Counting classes - Counter method (it might take a while)")
#count = collections.Counter(cla_raster.flatten())
#log.msg("Counter Count:")
#for k in count:
#    print k,"\t->\t",count[k]

#log.msg("Counting classes - Numpy method (it might take a while)")
#classes = np.unique(cla_raster)
#ncount = np.copy(classes)
#for i,c in enumerate(classes):
#    ncount[i] = np.sum(np.equal(cla_raster,c))
#
#log.msg("Numpy Count:")
#for k,c in zip(classes,ncount):
#    print "\t",k,"\t->\t",c


