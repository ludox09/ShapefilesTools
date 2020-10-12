#!/usr/bin/env python3
"""
Mix Raster and Vecteur information to Vector
Suitable for rotation studies
L. Arnaud - Cesbio - 2020-09-25 
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
from shapely.geometry import mapping, shape

import matplotlib.pyplot as plt

# Some Parameters
log = infolog.infolog()
epsilon = 1e-10
sys.path.insert(0,os.getcwd() )


def testshape(inputfile):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    datasource = driver.Open(inputfile, 1)
    
    if datasource is None:
        log.msg("Could not open file","ERROR")
        sys.exit(1)
    
    # get the data layer
    layer = datasource.GetLayer()
    layer_defn = layer.GetLayerDefn()

    print("Construct x1") 
    x1 = {} 
    for c,f in enumerate(layer):
         fid = f.GetFID() # 
         x1[c] = fid

    datasource = None
    
    print("Construct x2") 
    with fio.open(inputfile, "r") as shapefile:
        x2 = {}
        for c,feature in enumerate(shapefile):
            x2[c] = int(feature['id'])

    print(len(x1.keys()))
    print(len(x2.keys()))
    for c in x1.keys():
        if( x1[c] != x2[c] ):
            print(c, x1[c], x2[c])

    print("Done")



def AddPreviousYearInfo(inputfile, maxclass, maxidx, maxprop, externalclass,pytag):
     """ AddPreviousYearInfo """

     # Construct index convertor
     c2i = {}
     for i,s in enumerate(externalclass):
         c2i[s] = i

     # Fast duplication of input shapefile
     outputfile = updatename(inputfile,"%d"%(pytag))
     for ext in ["shp","cpg","dbf","shx","prj"]:
         before = inputfile.replace("shp",ext) 
         after  = updatename(before,"%d"%(pytag))
         os.system("cp %s %s"%(before,after))

     driver = ogr.GetDriverByName('ESRI Shapefile')
     datasource = driver.Open(outputfile, 1)

     if datasource is None:
         log.msg("Could not open file","ERROR")
         sys.exit(1)

     # get the data layer
     layer = datasource.GetLayer()
     layer_defn = layer.GetLayerDefn()
 
     # Add a new fieldi
     cultfield = "CULT_%d"%(pytag)
     codefield = "CODE_%d"%(pytag)
     propfield = "PROP_%d"%(pytag)

     new_class = ogr.FieldDefn(cultfield, ogr.OFTString)
     new_class.SetWidth(3)
     new_class.SetPrecision(0)
     layer.CreateField(new_class)

     new_code = ogr.FieldDefn(codefield, ogr.OFTInteger)
     new_code.SetWidth(3)
     new_code.SetPrecision(0)
     layer.CreateField(new_code)

     new_prop = ogr.FieldDefn(propfield, ogr.OFTInteger)
     new_prop.SetWidth(3)
     new_prop.SetPrecision(3)
     layer.CreateField(new_prop)

     ok = 0
     ko = 0

     log.msg("Filling shapefile %s"%(outputfile))
     for c,f in enumerate(layer):
         fid = f.GetFID() # conversion might not be necessary. Safer

         if(c%50000 ==0):
             log.msg("%d %d %d"%(c,len(layer),f.GetFID()))

         try:

             #layer.SetFeature(i)
             # Note: Casting is important. Without, it generates error.
             #print("maxclass[c2i[fid]]: ",maxclass[c2i[fid]])
             #print("maxidx[c2i[fid]]: ", int(maxidx[c2i[fid]]))
             #print("int(maxprop[c2i[fid]]):",int(maxprop[c2i[fid]]))

             maxclass_c = maxclass[c2i[fid]]
             maxidx_c = int(maxidx[c2i[fid]])
             maxprop_c = int(maxprop[c2i[fid]])

             f.SetField(cultfield, maxclass_c)
             layer.SetFeature(f)

             f.SetField(codefield, maxidx_c)
             layer.SetFeature(f)

             f.SetField(propfield, maxprop_c)
             layer.SetFeature(f)
             ok += 1
         except:
             #ignore index not found
             ko += 1

     log.msg("# of Polygons recorded: %d"%(ok),"DEBUG")
     log.msg("# of Polygons discared: %d"%(ko),"DEBUG")

     # Release shapefile handler
     datasource = None


def export_to_csv(filename,data,legend):
    """
       Sortcut to export to csv with header legend
    """
    header = ""
    for l in legend:
        header=header+"%s,"%(l)
    header = header[:-1]
    np.savetxt(filename, data, fmt = "%d",delimiter=",", header=header)

def get_geometries_id(shapefile_name):
    """
       Get geometry features from shapefile
    """
    with fio.open(shapefile_name, "r") as shapefile:
        log.msg("Shapefile crs: %s"%(shapefile.crs),"DEBUG")
        feat = [(feature['geometry'], int(feature['id'])) for feature in shapefile]
    return feat

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
    pixel  = np.zeros((nclass,len(externalclass)))
    width  = im.shape[0]
    height = im.shape[1]

    #Dict for rapid conversion 
    c2i = {}
    for i,s in enumerate(externalclass):
        c2i[s] = i

    # Loop over raster. Surprisingly efficient enough.
    for i in range(width):
        for j in range(height):
            c1 = im[i,j]
            c2 = c2i[external[i,j]]
            #if(c1 != 0 and c2 != 0):
            pixel[c1,c2] += 1 
    
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

def Image_to_Statistics(raster,band,vector,legend,npool):
    """
       Count in raster(s)
    """

    log.msg("Opening Rasterized Shapefile %s (it might take a while)"%(raster))
    with rasterio.open(raster) as src:
        log.msg("Raster crs: %s"%(src.crs),"DEBUG")
        destination = Proj(src.crs)
        transform = src.transform
        im = src.read(band, out_dtype = rasterio.uint16) # Note: Band indexing start at 1

    log.msg("Opening vector Shapefile %s (it might take a while)"%(vector))
    feat = get_geometries_id(vector)
    
    log.msg("Rasterize external shapefile")
    shape = im.shape
    external = features.rasterize(shapes=feat, out_shape = shape, transform = transform)

    nclass = len(legend.class2code)
    externalclass = np.unique(external)
    log.msg("Number of raster classes: %d"%(nclass))
    log.msg("Number of shapefile features: %d"%(len(externalclass)))
    log.msg("Max id: %d"%(np.max(externalclass)))
    log.msg("Construct Overlap")

    # Parallel block  
    log.msg("Starting parallel block","DEBUG")
    pool = mp.Pool(npool)
    nblock = int(im.shape[1]/npool) + 1
    inputdata =  [[i,nclass,im[:,i*nblock:(i + 1)*nblock],externalclass,external[:,i*nblock:(i + 1)*nblock]] for i in range((im.shape[1] + nblock - 1) // nblock )]
    pixelblock = pool.map(SubBlock,inputdata)

    # Gather all pool results
    pixel = 0.0
    for p in pixelblock:
        pixel = pixel + p

    log.msg("End parallel block","DEBUG")

    # Define and normalize surface matrix
    np.seterr(invalid='ignore')
    #pi = np.sum(pixel, axis=1)
    pj = np.sum(pixel, axis=0)  

    # convert nbrpixel in ha
    #sur = pixel/100.0   

    # Renormalize rows and colums
    #CondPro  = 100.0*pixel/pi[:,None]
    InvPro   = 100.0*pixel/pj[None,:]
    
    # Get rid of Nan due to 0/0
    #CondPro[np.isnan(CondPro)] = 0.0
    InvPro[np.isnan(InvPro)] = 0.0

    log.msg("Calculate Proportion variables")
    maxprop = np.max(InvPro, axis = 0)
    maxidx  = np.argmax(InvPro, axis = 0)
    maxclass = [legend.code2class[x] for x in maxidx] 

    return maxclass, maxidx, maxprop, externalclass
  
 
########################################################################################

# Init 
FirstYear = 2015
npool = 20

# Get input parameters
try:
    legend_file              = sys.argv[1] 
    raster_in_file           = sys.argv[2]
    raster_band              = int(sys.argv[3])
    vector_in_file           = sys.argv[4]
    previous_year_tag        = int(sys.argv[5])
except:
    log.msg("""Error in input parameter
Syntax: %s %s %s %s %s
            """%(__file__.split("/")[-1],"RasterFile","band","VectorFile","previous year"),"ERROR")
    quit()

Legend_Name = legend_file.split(".")[0]
legend = importlib.import_module(Legend_Name)

###testshape(vector_in_file)

# Compare raster and vector data
maxclass, maxidx, maxprop, externalclass = Image_to_Statistics(raster_in_file,raster_band,vector_in_file,legend,npool)

log.msg("Add Previous Year Info")
AddPreviousYearInfo(vector_in_file,maxclass, maxidx, maxprop, externalclass,previous_year_tag)

log.msg("Done")

