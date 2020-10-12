#!/usr/bin/python
import ogr, os, sys
import numpy as np
import MatrixPlot as mp
import parameters as param
from matplotlib import cm 
import infolog
import argparse
import json
import pickle

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
groupmap4   = param.groupmap4 # Classification Legend

#####################
if(False):

    sc = ['CZH', 'BLE', 'ORP', 'FVX', 'TRN', 'SOG', 'MAI', 'SOJ', 'SRS', 'LEG', 'HAR', 'LIP', 'JXX', 'PPX', 'PTR', 'PTX', 'LUX', 'TRX', 'OTH']


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

    if "OTH" not in sc:
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
 
    npsc = np.array(sc, dtype='<U3')

    # Export to file #
    np.savez("StatStructure-%d-%d-%s"%(year1,year2,name), legend = npsc, groupmap = groupmap, parcels=mat, surface=sur,condproba=CondPro,invproba=InvPro)

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


######################################################## MAIN #################################################################
if __name__ == "__main__":

    log = infolog.infolog()
    parser=argparse.ArgumentParser()
    parser.add_argument("-in", "--inputfile", nargs='+', help="Input shapefile")
    parser.add_argument("-y", "--years", nargs='+',help="""Couple of years.
Syntax:
./ShapefileEditor.py -in shapefile.shp -y 15 16"
""")
    parser.add_argument("-s", "--several", nargs='+',help="""List of consecutive years""")
 
    args=parser.parse_args()
    if(args.inputfile==None and args.years==None and args.several==None):
      # Handle help message because mutual exclusive option required it.
      print "usage: ShapefileEditor [-h]  [-in] SHAPEFILES [-y] year1 year2 [-s] year1 year2 year3"
      print "ShapefileEditor: error: too few arguments"
      quit()

    if(args.years!=None):    
      shpname = args.inputfile[0]
      year1 = int(args.years[0])
      year2 = int(args.years[1])
      log.msg("Input shapefile: %s"%(shpname))
      log.msg("Year 1: %d"%(year1))
      log.msg("Year 2: %d"%(year2))
     
      # Open and initialize shapefile #
      driver = ogr.GetDriverByName('ESRI Shapefile')
      datasource = driver.Open(shpname, 1)
      if datasource is None:
        print 'Could not open file'
        sys.exit(1)
      
      layer = datasource.GetLayer()
      nf = layer.GetFeatureCount()
      log.msg("# feature = %d"%(nf))
      
      # Export matrix with precise gathering
      log.msg("Export matrix with precise gathering")
   ##   #ExportMatrix("Precise-Filtered",year1,year2,layer,groupmap1)
      
      # Export matrix with large gathering
      log.msg("Export matrix with large gathering")
      ExportMatrix("Large-Filtered",year1,year2,layer,groupmap2)
      
      # Export matrix with large gathering
      log.msg("Export matrix with large gathering")
   ##   #ExportMatrix("Season-Filtered",year1,year2,layer,groupmap3)
     
      # Export matrix with classif gathering
      log.msg("Export matrix with classif gathering")
   ##   #ExportMatrix("Classif-Filtered",year1,year2,layer,groupmap4)

      file1 = "Rotation-RPG-%d-%d-%s.pdf"%(year1,year2,"Precise-Filtered") 
      file2 = "Rotation-RPG-%d-%d-%s.pdf"%(year1,year2,"Large-Filtered") 
      file3 = "Rotation-RPG-%d-%d-%s.pdf"%(year1,year2,"Season-Filtered") 
      file4 = "Rotation-RPG-%d-%d-%s.pdf"%(year1,year2,"Classif-Filtered") 
      fileout = "Rotation-RPG-%d-%d-%s.pdf"%(year1,year2,"Filtered") 
      
      #os.system("pdfunite %s %s %s %s"%(file1,file2,file3,fileout))

    else:
        statlist = args.inputfile
	legendlist = ["StatStructure"+x[13:-4] for x in statlist]
        yearlist = [int(x) for x in args.several]
        ycouplelist = [[x,x+1] for x in yearlist]

        # check if legend are the same between all couple of years
        AllLegend = []
        AllName = []
        for legendfile in legendlist:
            data = np.load(legendfile)
	    legend=str(data['legend'])
	    AllLegend.append(legend)
	    AllName.append(legendfile[13:])


        QLegend = True
        QName = True
	for x,y in zip(AllLegend,AllName):
	    QLegend = QLegend and (x==AllLegend[0])
	    QName = QName and (y==AllName[0])
 
	if QLegend and QName:

            name = AllName[0]
	    # Calculate Mean and std #
            parcelsMean   = 0.0
	    surfaceMean   = 0.0
	    CondProbaMean = 0.0
	    InvProbaMean  = 0.0

            parcelsStd    = 0.0
	    surfaceStd    = 0.0
	    CondProbaStd  = 0.0
	    InvProbaStd   = 0.0

            Nmax = len(statlist)
	    print Nmax
            for legendfile,statfile,ycouple in zip(legendlist,statlist,ycouplelist):
	        legend=pickle.load(open(legendfile, 'rb'))
	        stat = np.load(statfile)

                parcelsMean = parcelsMean + stat['parcels']/Nmax
	        surfaceMean = surfaceMean + stat['surface']/Nmax
	        CondProbaMean = CondProbaMean + stat['condproba']/Nmax
	        InvProbaMean = InvProbaMean + stat['invproba']/Nmax

       	        parcelsStd = parcelsStd + (stat['parcels']**2)/(Nmax)
	        surfaceStd = surfaceStd + (stat['surface']**2)/(Nmax)
	        CondProbaStd = CondProbaStd + (stat['condproba']**2)/(Nmax)
	        InvProbaStd = InvProbaStd + (stat['invproba']**2)/(Nmax)

            parcelsStd = np.sqrt(parcelsStd - (parcelsMean**2))
            surfaceStd = np.sqrt(surfaceStd - (surfaceMean**2))
            CondProbaStd = np.sqrt(CondProbaStd - (CondProbaMean**2))
            InvProbaStd = np.sqrt(InvProbaStd - (InvProbaMean**2))

            titlesMean = [
                     "Rotation RPG - %s - Mean of Parcel Number"%(name),
                     "Rotation RPG - %s - Mean of Surface ($ha$)"%(name),
                     "Rotation RPG - %s - Mean of Conditionnal Probabilities"%(name),
                     "Rotation RPG - %s - Mean of Inversed Probabilities"%(name)
                      ]
            titlesStd = [
                     "Rotation RPG - %s - Std of Parcel Number"%(name),
                     "Rotation RPG - %s - Std of Surface ($ha$)"%(name),
                     "Rotation RPG - %s - Std of Conditionnal Probabilities"%(name),
                     "Rotation RPG - %s - Std of Inversed Probabilities"%(name)
                      ]

            matListMean = [parcelsMean,surfaceMean,CondProbaMean,InvProbaMean]
            matListStd =  [parcelsStd,surfaceStd,CondProbaStd,InvProbaStd]


            year1 = yearlist[0] 
            year2 = yearlist[-1] 
            colormapList = ["rainbow","rainbow","white","white"]
	    log.msg("Export Mean values")
            mp.exportNew(matListMean,colormapList,legend,"Mean-RPG-%d-%d-%s.pdf"%(year1,year2,name),titlesMean)

	    log.msg("Export Std values")
            mp.exportNew(matListStd,colormapList,legend,"Std-RPG-%d-%d-%s.pdf"%(year1,year2,name),titlesStd)

	elif not(QLegend):
	    log.msg("The legends between the different couples of year are different. Please check.","ERROR")

        elif not(QName):
	    log.msg("The type names between the different couples of year are different. Please check.","ERROR")

