#!/usr/bin/python
import ogr, os, sys
import numpy as np
import MatrixPlot as mp
import parameters as param
from matplotlib import cm 

def union(a,b):
  c = a
  for x in b:
    if(x not in c):
      c.append(x)
  return sorted(c)

# Main #

subclasses = param.subclasses
groupmap1   = param.groupmap1 # Precise legend
groupmap2   = param.groupmap2 # Large Legend
groupmap3   = param.groupmap3 # Seasonal Legend

#####################
if(False):
    sc = ['CZH', 'BTH', 'BDH', 'ORH', 'TTH', 'AVH', 'ORP', 'FVL', 'PHI', 'LIH', 'TRN', 'SOG', 'MIS', 'MIE', 'MID', 'SOJ', 'SRS', 'PCH', 'LEC', 'HAR', 'LIP', 'BTN', 'AIL', 'JXX', 'PPX', 'PTR', 'PTX', 'LXX', 'TRX', 'OTH']
    
    titles = [
    "Rotation RPG 2016 (V) and 2017 (H) - Parcel Number",
    "Rotation RPG 2016 (V) and 2017 (H) - Surface (ha)"
    ]
    
    mat = np.load("RPG-16-17.npy")
    sur = np.load("SUR-16-17.npy")

    mp.export([mat,sur],sc,"Rotation-RPG-2016-2017.pdf",titles)
    
    quit()
###################

# construct subclass set # 

def ExportMatrix(name,year1,year2,layer,groupmap):
    c1 = []
    c2 = []

    layer.ResetReading()
    for f in layer:
        f1 = f["C%d"%year1] 
        f2 = f["C%d"%year2]    
        if (f1 in subclasses) and (groupmap[f1] not in c1) and (f['OK'] != 0.0):
            c1.append(groupmap[f1])
    
        if (f2 in subclasses) and (groupmap[f2] not in c2) and (f['OK'] != 0.0):
            c2.append(groupmap[f2])
     
    sc = union(c1,c2)
    if set(sc) != set(groupmap.values()):
        print "sc = ",set(sc)
        print "groupmap = ",set(groupmap.values())
        print "sc - groupmap = ",set(sc).difference(set(groupmap.values()))
        print "groumap - sc = ",set(groupmap.values()).difference(set(sc))
        print "Set of class different than selected class. Abord."
        quit()

  
    sc = []
    for x in subclasses:
        if groupmap[x] not in sc:
            sc.append(groupmap[x])

    sc.append("OTH")
    Nc = len(sc)
    print "Subclasses common between the two years."
    print sc
    
    # Prefill Overlap Dictionary #
    overdic = {}
    surfdic = {}
    for g1 in sc:
        for g2 in sc:
           overdic[g1,g2] = 0
           surfdic[g1,g2] = 0.0
    
    # Construct Overlap Dictionary #
    layer.ResetReading()
    c = 0
    for f in layer:
        if (f['OK'] != 0):
            try:
              g1 = groupmap.get(f["C%d"%year1],'OTH')
              g2 = groupmap.get(f["C%d"%year2],'OTH')
    
              geom = f.GetGeometryRef()
              try:
                #s = 1000.0*float(geom.GetArea())/1000.0 # convert m2 in ha
                s = float(geom.GetArea())/10000.0
              except AttributeError:
                c += 1 
                print "Debug counter:",c
                s = 0.0
    
              if g1 in sc and g2 in sc:
                overdic[g1,g2] += 1
                surfdic[g1,g2] = surfdic[g1,g2] + s
               
            except:
              raise
    
    print "Construction of overlap matrix"
    mat = np.zeros((Nc,Nc))
    sur = np.zeros((Nc,Nc))
    for i,g1 in enumerate(sc):
        for j,g2 in enumerate(sc):
            mat[i][j] = overdic[g1,g2]
            sur[i][j] = surfdic[g1,g2]
    
    np.save("RPG-%d-%d-%s"%(year1,year2,name), mat)
    np.save("SUR-%d-%d-%s"%(year1,year2,name), sur)
    titles = [
    "Rotation RPG %d (V) and %d (H) - %s - Parcel Number"%(year1,year2,name),
    "Rotation RPG %d (V) and %d (H) - %s - Surface ($ha$)"%(year1,year2,name),
    "Rotation RPG %d (V) and %d (H) - %s - Conditionnal Probabilities"%(year1,year2,name),
    "Rotation RPG %d (V) and %d (H) - %s - Inversed Probabilities"%(year1,year2,name)
    ]

    # calculate conditional priobability 

    pi = np.sum(sur, axis=0)
    pj = np.sum(sur, axis=1)
    InvPro = 100.0*sur/pi[None,:]
    CondPro = 100.0*sur/pj[:,None]
   
    matList = [mat,sur,CondPro,InvPro]
    #colormapList = ["rainbow","rainbow","ocean"] 
    colormapList = ["rainbow","rainbow","white","white"] 

    #mp.export(matList,colormapList,sc,"Rotation-RPG-%d-%d-%s.pdf"%(year1,year2,name),titles,year1,year2)
    mp.exportNew(matList,colormapList,sc,"Rotation-RPG-%d-%d-%s.pdf"%(year1,year2,name),titles)


#print "Test scientific writting"
#fval,fcol = mp.scientific(0.9999,"rainbow",0,1000)
#print fval,fcol
#fval,fcol = mp.scientific(2.9999,"rainbow",0,1000)
#print fval,fcol
#fval,fcol = mp.scientific(3.4999,"rainbow",0,1000)
#print fval,fcol


# Input variables #
shpname = sys.argv[1]
year1 = int(sys.argv[2])
year2 = int(sys.argv[3])
print("Input shapefile: %s"%(shpname))
print "Year 1: %d"%(year1)
print "Year 2: %d"%(year2)

# Open and initialize shapefile #
driver = ogr.GetDriverByName('ESRI Shapefile')
datasource = driver.Open(shpname, 1)
if datasource is None:
  print 'Could not open file'
  sys.exit(1)

layer = datasource.GetLayer()
nf = layer.GetFeatureCount()
print "# feature = ",nf

# Export matrix with precise gathering
print "Export matrix with precise gathering"
ExportMatrix("Precise-Filtered",year1,year2,layer,groupmap1)

# Export matrix with large gathering
print "Export matrix with large gathering"
ExportMatrix("Large-Filtered",year1,year2,layer,groupmap2)

# Export matrix with large gathering
print "Export matrix with large gathering"
ExportMatrix("Season-Filtered",year1,year2,layer,groupmap3)

file1 = "Rotation-RPG-%d-%d-%s.pdf"%(year1,year2,"Precise-Filtered") 
file2 = "Rotation-RPG-%d-%d-%s.pdf"%(year1,year2,"Large-Filtered") 
file3 = "Rotation-RPG-%d-%d-%s.pdf"%(year1,year2,"Season-Filtered") 
fileout = "Rotation-RPG-%d-%d-%s.pdf"%(year1,year2,"Filtered") 

os.system("pdfunite %s %s %s %s"%(file1,file2,file3,fileout))

