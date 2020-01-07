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


# Parmeters
log = infolog.infolog()
epsilon = 1e-10
rasterize_com = "otbcli_Rasterization -in %s -out %s -im %s -mode attribute -mode.attribute.field %s -ram %d"
concatenation_com = "otbcli_ConcatenateImages -il %s -out %s -ram %d"
primlist = ["NDVI","NDWI_SWIR","NDWI_GREEN","BRIGHTNESS"] 

#class ProfileStructure(object):
#    def __init__(self, code, npixels, primitive, mean, std):
#        self.code       = code
#        self.npixels    = npixels
#        self.primitive  = primitive
#        self.mean       = mean
#        self.std        = std

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

    return X, Y, parcel_raster, parcelsList, profilesBase
    log.msg("END SCANING","DEBUG")

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

    if prim == "NDWI_SWIR":
        B8Apos = 10*t + 7 + 1
        B11pos = 10*t + 8 + 1
        B8Aimg = img.GetRasterBand(B8Apos)
        B11img = img.GetRasterBand(B11pos)
        B8A = np.array(B8Aimg.ReadAsArray()).astype(np.float)
        B11 = np.array(B11img.ReadAsArray()).astype(np.float)
        NDWIS = (B8A - B11)/(B8A + B11 + epsilon)
        return NDWIS

    if prim == "NDWI_GREEN":
        B3pos = 10*t + 1 + 1
        B8pos = 10*t + 6 + 1
        B3img = img.GetRasterBand(B3pos)
        B8img = img.GetRasterBand(B8pos)
        B3 = np.array(B3img.ReadAsArray()).astype(np.float)
        B8 = np.array(B4img.ReadAsArray()).astype(np.float)
        NDWIG = (B3 - B8)/(B3 + B8 + epsilon)
        return NDWIG
    
    if prim == "BRIGHTNESS":
        brightness = 0.0
        for b in range(10):
            Bpos = 10*t + b + 1
            Bimg = img.GetRasterBand(Bpos)
            B = np.array(Bimg.ReadAsArray()).astype(np.float)
            brightness = brightness + B*B

        brightness = np.sqrt(brightness)
        return brightness

def getPrimStat(p,X,Y,npprim):
        #mask = np.equal(npparcels,p)
        #masked = np.ma.array(npprim,mask = mask) 
        #[x,y] = np.where(np.equal(npparcels,p))
        [x,y] = [X[p],Y[p]]
        masked = npprim[x,y]
        return np.mean(masked),np.std(masked)


#VgetPrimStat = np.vectorize(getPrimStat)

# print img.GetMetadata()
# stats = imgBand.GetStatistics( True, True )

# Path name of the classifcation raster
rastershapefile = sys.argv[1]
stackfile = sys.argv[2]
prim = sys.argv[3]
try:
    Qrasterize = sys.argv[4] # Creat halt if not defined
    if Qrasterize == r
        Qrasterize = True
    else:
        Qrasterize = True

if(prim not in primlist):
    log.msg("Primitive does not exist. Should be chosen in:",'ERROR')
    log.msg(primlist,'ERROR')
    quit()

fieldList = ["I17","CODE17","CODE18","DERA18","DERB18"]
#fieldList = ["CODE17"]

#tile = stackfile[22:27]
tile = stackfile[3:8]

try:

    #tile = stackfile[3:8]
    rasterized_name = rastershapefile.split("/")[-1].split(".")[0] + "_Rasterized_" + stackfile.split("_")[-1]
    log.msg("Rasterize Output File: %s"%(rasterized_name))
    names = []
    for fi in fieldList:
        name_i = rastershapefile.split("/")[-1].split(".")[0] + "_%s_"%(fi) + stackfile.split("_")[-1]
        names.append(name_i)
        log.msg("    - Rasterize field %s"%(fi))
        os.system(rasterize_com%(rastershapefile,name_i,stackfile,fi,20000))

    # Concatenation
    namesList = ""
    for name in names:
        namesList = namesList + " " + name
    com = concatenation_com%(namesList,rasterized_name,20000)
    os.system(com)
except:
    log.msg("Rasterization already performed. Continue extraction")
    pass

#rasterized_name = "RPG201718-topo_rm-geotest_ero50cm-UnionSAGA-up-solo-sup1ha-ero195cm-sup1ha-scop_Rasterized_31TCJ_31TCJ.tif"
print rasterized_name

#npparcels, parcels_list, parcels_count = numpyrize(rasterized_name, 1, nmin = 1000, nmax=1005, verbose=True)
#npclasses, classes_list, classes_count = numpyrize(rasterized_name, 2, verbose=True)
#npparcels, parcels_list, parcels_count = numpyrize(parcels_out, verbose=True)


#npparcels, parcelsList, profilesdf = PrepareDataFrame(rasterized_name, fieldList, nmin = 25000, nmax = 25010, verbose=True)



# Prepare Image raster reading
log.msg("Open Image Stack %s (it might take a while)"%(stackfile))
img = gdal.Open(stackfile)
NFeatures = img.RasterCount
NDates = NFeatures/10

log.msg(("- Number of band",NFeatures))
log.msg(("- Number of dates",NDates))
log.msg(("- Primitives",prim))

# Get Raster information and masking
X, Y, npparcels, parcelsList, profilesdf = PrepareDataFrame(rasterized_name, fieldList, verbose=True)

tmin = 0
tmax = NDates
profiles = {}
for t in range(tmin,tmax):
    log.msg(" - Calculate %s at date %i"%(prim,t))
    # Add relevant colums to profiles df
    StrColMean = "mean_ndvi_%d"%(t)
    StrColStdv = "stdv_ndvi_%d"%(t)
    profilesdf[StrColMean] = np.nan
    profilesdf[StrColStdv] = np.nan

    npprim = npprimitive(img,t,prim)
    log.msg(("  Image stack size: ",npprim.shape),"DEBUG")

    for i,p in enumerate(parcelsList):
        #log.msg("Parcel %d"%(p),"DEBUG")
        meanprim,stdprim = getPrimStat(p,X,Y,npprim)
        profilesdf.at[i,StrColMean] = meanprim
        profilesdf.at[i,StrColStdv] = stdprim

        #try:
        #    profiles[int(p)][1].append(meanprim)
        #    profiles[int(p)][2].append(stdprim)
        #except:
        #    profiles[int(p)] = [[meanprim],[stdprim]]
 
print profilesdf
log.msg("Export mean and std profiles between date %d and %d"%(tmin,tmax))
profilesdf.to_pickle("Profiles_%s_%s_%d_%d.pkl"%(prim,tile,tmin,tmax))
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


