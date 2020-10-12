#!/usr/bin/env python3
"""
Construct Proportion matrix from rasterize
Export it in npz and csv format
Deal with external reference shape (region, soil...)

L. Arnaud - Cesbio - 2020-09-14 
"""

import os,sys
import numpy as np
import pandas as pd
import collections
import fiona as fio
import rasterio
from rasterio import features
from rasterio.transform import Affine
from pyproj import Proj, transform
from osgeo import gdal
from osgeo import ogr
import infolog
import time
import importlib
import multiprocessing as mp

import matplotlib.pyplot as plt

# Some Parameters
log = infolog.infolog()
epsilon = 1e-10
sys.path.insert(0,os.getcwd() )

def export_to_csv(filename,data,legend):
    """
       Sortcut to export to csv with header legend
    """
    header = ""
    for l in legend:
        header=header+"%s,"%(l)
    header = header[:-1]
    np.savetxt(filename, data, fmt = "%d",delimiter=",", header=header)

def get_geometries(shapefile_name, maskfield):
    """
       Get geometry features from shapefile
    """
    with fio.open(shapefile_name, "r") as shapefile:
        log.msg("Shapefile crs: %s"%(shapefile.crs),"DEBUG")
        feat = [(feature['geometry'], int(feature['properties'][maskfield])) for feature in shapefile]
        origin = Proj(shapefile.crs)
    return (feat,origin)

def updatename(name,tag):
    """ 
       Add tag to already define name
    """
    return name.split(".")[:-1][0] + "_%s"%(tag)  + "." + name.split(".")[-1] 

def SubBlock(inputdata):
    """
       Read piece of rasters
       Needed for parallel usage (with pool)
    """

    nproc, nclass, im, externalclass, external = inputdata
    log.msg("Process %d started"%(nproc),"DEBUG")
    pixel  = np.zeros((len(externalclass),nclass,nclass))
    width  = im.shape[1]
    height = im.shape[2]

    #Dict for rapid conversion 
    c2i = {}
    for i,s in enumerate(externalclass):
        c2i[s] = i

    # Loop over raster. Surprisingly efficient enough.
    for i in range(width):
        for j in range(height):
            c1 = im[0,i,j]
            c2 = im[1,i,j]
            sij = external[i,j]
            #if(c1 != 0 and c2 != 0):
            pixel[c2i[sij],c1,c2] += 1 
    
    log.msg("Process %d finished"%(nproc),"DEBUG")
    return pixel


def reproject_features(feat,origin,destination):
    """
       Reproject coordinate from origin to destination crs
    """

    # CATION: Really inefficient algo. Not used. Shapefile et raster need to be set to the same crs
    newfeat = feat.copy()
    for i,f in enumerate(feat):
        coor  = f[0]['coordinates'][0]
        ncoor = newfeat[i][0]['coordinates'][0]
        for j,c in enumerate(coor):
            x = transform(origin,destination,c[0],c[1])
            newfeat[i][0]['coordinates'][0][j] = x
    return newfeat

def Image_to_Statistics(rasterizedfile,legend,bfirst,blast,npool,geo=None):
    """
       Count in raster(s)
    """

    log.msg("Opening Rasterized Shapefile %s (it might take a while)"%(rasterizedfile))
    with rasterio.open(rasterizedfile) as src:
        log.msg("Raster crs: %s"%(src.crs),"DEBUG")
        destination = Proj(src.crs)
        transform = src.transform
        im = src.read((bfirst,blast), out_dtype = rasterio.uint16) # Note: Band indexing start at 1
 
    # Deal in case of no external shapefile
    if (geo != None):
        log.msg("Rasterize external shapefile")
        feat = geo[0]
        origin = geo[1]
        shape = (im.shape[1],im.shape[2])
        external = features.rasterize(shapes=feat, out_shape = shape, transform = transform)
    else:
        # Define dummy raster
        external = 0*im[0]+1

    externalclass = np.unique(external)
    log.msg("Construct Overlap")
    nclass = len(legend.class2code)

    # Parallel block  
    log.msg("Starting parallel block","DEBUG")
    pool = mp.Pool(npool)
    nblock = int(im.shape[2]/npool) + 1
    inputdata =  [[i,nclass,im[:,:,i*nblock:(i + 1)*nblock],externalclass,external[:,i*nblock:(i + 1)*nblock]] for i in range((im.shape[2] + nblock - 1) // nblock )]
    pixelblock = pool.map(SubBlock,inputdata)

    # Gather all pool results
    pixel = 0.0
    for p in pixelblock:
        pixel = pixel + p

    log.msg("End parallel block","DEBUG")

    # Define and normalize surface matrix
    np.seterr(invalid='ignore')
    pi = np.sum(pixel, axis=2)
    pj = np.sum(pixel, axis=1)  

    # convert nbrpixel in ha
    sur = pixel/100.0   

    # Renormalize rows and colums
    CondPro  = 100.0*pixel/pi[:,:,None]
    InvPro   = 100.0*pixel/pj[:,None,:]
    
    # Get rid of Nan due to 0/0
    CondPro[np.isnan(CondPro)] = 0.0
    InvPro[np.isnan(InvPro)] = 0.0

    # indexation methods (keep just in case)
    #CondPro  = 0.0*pixel
    #InvPro   = 0.0*pixel
    #for i,x in enumerate(pi):
    #    if(x != 0.0):
    #        CondPro[:,i] = pixel[i]/x
    #    else:
    #        CondPro[:,i] = pixel[i]*0

    #for i,y in enumerate(pj):
    #    if(y != 0.0):
    #        InvPro[:,i]  = pixel[:,i]/y
    #    else:
    #        InvPro[:,i]  = pixel[:,i]*0
    #
    #CondPro = 100.0*CondPro
    #InvPro  = 100.0*InvPro

    # some infir for debug 
    log.msg(("pi =",np.sum(np.equal(pi[0],0))),"DEBUG")
    log.msg(("pj =",np.sum(np.equal(pj[0],0))),"DEBUG")
    log.msg(("sur =",np.sum(np.isnan(sur[0]))),"DEBUG")
    log.msg(("IP =",np.sum(np.isnan(InvPro[0]))),"DEBUG")
    log.msg(("Con =",np.sum(np.isnan(CondPro[0]))),"DEBUG")

    # Handle class name
    sc = [legend.code2class[i] for i in range(nclass)]
    npsc = np.array(sc, dtype='<U3')

    return npsc, sur, CondPro, InvPro, externalclass
  
 
########################################################################################

# Init 
FirstYear = 2015
npool = 14

# Get input parameters
try:
    name           = sys.argv[1]
    Image_File     = sys.argv[2]
    Legend_File    = sys.argv[3]
    year1          = int(sys.argv[4])
    year2          = int(sys.argv[5])
except:
    log.msg("""Error in input parameter
Syntax: %s %s %s %s %s %s %s
            """%(__file__.split("/")[-1],"tag_name","image_file","legend","yearN","yearN+1","(shape mask)"),"ERROR")
    quit()

# Deal with region masking
try:
    shapemask = sys.argv[6]
    geo = get_geometries(shapemask,"SMU")
except:
    geo = None

# construct band indices from years
idx1 = year1 - FirstYear + 1
idx2 = year2 - FirstYear + 1

# Get statistic from image
Legend_Name = Legend_File.split(".")[0]
legend = importlib.import_module(Legend_Name)

# Get statistics
npsc, sur, CondPro, InvPro, externalclass = Image_to_Statistics(Image_File, legend, idx1, idx2, npool, geo)

# For debug
#print(sur.shape,CondPro.shape,InvPro.shape)

#create output directory
rep = "StatStructure-%d-%d-%s"%(year1,year2,name)
os.makedirs(rep, exist_ok=True)
os.makedirs(rep + "/npz", exist_ok=True)
os.makedirs(rep + "/csv", exist_ok=True)

if(geo != None):
    # Export for each external class
    for sidx,s in enumerate(externalclass):
        filename = "%s/npz/StatStructure-%d-%d-%s-%d"%(rep,year1,year2,name,s)
        csvfile = "%s/csv/StatStructure-%d-%d-%s-%d.csv"%(rep,year1,year2,name,s)
        log.msg("Exporting %s to npz and csv formats"%(filename.split("/")[-1]))
        # Export in compressed numpy format
        np.savez(filename, legend = npsc, surface=sur[sidx], condproba=CondPro[sidx], invproba=InvPro[sidx])
        # Exporte to csv
        export_to_csv(csvfile,sur[sidx],npsc)

# export for all surface
print()
filename = "%s/npz/StatStructure-%d-%d-%s"%(rep,year1,year2,name)
csvfile = "%s/csv/StatStructure-%d-%d-%s.csv"%(rep,year1,year2,name)
log.msg("Exporting %s to npz and csv fornats"%(filename.split("/")[-1]))
# Export in compressed numpy format
surTot     = np.sum(sur, axis=0)
CondProTot = np.sum(CondPro, axis=0)
InvProTot  = np.sum(InvPro, axis = 0)
np.savez(filename, legend = npsc, surface=surTot, condproba=CondProTot, invproba=InvProTot)
# Exporte to csv
export_to_csv(csvfile,np.sum(sur, axis=0),npsc)

log.msg("Done")

