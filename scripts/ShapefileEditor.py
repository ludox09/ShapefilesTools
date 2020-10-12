#!/usr/bin/env python3

""" Ludo 08/2019 """

from __future__ import print_function
import os, sys, glob
import string
import argparse
import json
import ast
import numpy as np
import parameters as param
import infolog
import pickle
import importlib

from osgeo import ogr, osr
try:
    from osgeo import gdal
except ImportError:
    import gdal


log = infolog.infolog()
#log.set_level("WARNING")
#print log.get_level()
#log.msg("message info")
#log.msg("debug","DEBUG")


subclasses = param.subclasses
groupmap1   = param.groupmap1

rpgClasses = param.rpgClasses
derobesClasses = param.derobesClasses

# Add new type if needed
code2type = {ogr.OFTInteger:  "Int   ",
             ogr.OFTReal:     "Real  ",
             #ogr.OFTInteger64:"Int64 ",
             ogr.OFTString:   "String"}

type2code = {"Int":ogr.OFTInteger,
             "Real":ogr.OFTReal,
             #"Int64":ogr.OFTInteger64,
             "String":ogr.OFTString}


def cloneFieldDefn(src_fd):
    """ Clone Field """
    fdef = ogr.FieldDefn(src_fd.GetName(), src_fd.GetType())
    fdef.SetWidth(src_fd.GetWidth())
    fdef.SetPrecision(src_fd.GetPrecision())
    return fdef

def DisplayField(inputfiles):
    """ Dispaly field """
    driver = ogr.GetDriverByName('ESRI Shapefile')
    for inputfile in inputfiles:
        log.msg("*** File %s ***"%(inputfile))
        datasource = driver.Open(inputfile, 1)
        if datasource is None:
            log.msg("Could not open file","ERROR")
            sys.exit(1)

        # get the data layer
        layer = datasource.GetLayer()
        nf = layer.GetFeatureCount()
        log.msg("Number of features: %d"%(nf))

        #line    = "xxxxxxxxxxxxxxxxx" "#DEBUG
        line    = "-----------------"
        sfield  = "Field    \t|"
        stype   = "Type     \t|"
        swidth  = "Width    \t|"
        sprec   = "Precision\t|"

        layerDefn = layer.GetLayerDefn()
        for i in range(layerDefn.GetFieldCount()):
            line = line + "--------"
            src_fd = layerDefn.GetFieldDefn(i)
            fdef = cloneFieldDefn(src_fd)
            fieldName = fdef.GetName()
            fieldType = code2type[fdef.GetType()]
            fieldWidth = fdef.GetWidth()
            fieldPrecision = fdef.GetPrecision()
            tab = "\t|"
            sfield = sfield + "%s%s"%(fieldName,tab)
            stype  = stype  + "%s%s"%(fieldType,tab)
            swidth = swidth + "%s%s"%(fieldWidth,tab)
            sprec = sprec + "%d%s"%(fieldPrecision,tab)
           
        print(line)
        print(sfield)
        print(line)
        print(stype)
        print(swidth)
        print(sprec)
        print(line)
        print("")
       
   
          

def RenameField(inputfile, mappingstring):
    """ Rename field """
    driver = ogr.GetDriverByName('ESRI Shapefile')
    datasource = driver.Open(inputfile, 1)
    if datasource is None:
        log.msg("Could not open file","ERROR")
        sys.exit(1)

    # get the data layer
    layer = datasource.GetLayer()
 
    mapping = ast.literal_eval(mappingstring)

    print("")
    types = [ogr.OFTInteger, ogr.OFTReal, ogr.OFTInteger, ogr.OFTInteger, ogr.OFTInteger, ogr.OFTInteger]

    layerDefn = layer.GetLayerDefn()
    for i in range(layerDefn.GetFieldCount()):
        src_fd = layerDefn.GetFieldDefn(i)
        fdef = cloneFieldDefn(src_fd)
        fieldName = fdef.GetName()
        try:
          newname = mapping[fieldName]
          print("%s becomes %s"%(fieldName,newname))
        except:
          newname = fieldName

        vtype = fdef.GetType()
        fdef.SetName(newname)
        fdef.SetType(vtype)
        layer.AlterFieldDefn(i, fdef, (ogr.ALTER_NAME_FLAG | ogr.ALTER_WIDTH_PRECISION_FLAG))

    print("")
    print("Fields after renaming")
    DisplayField(inputfile)
 
 

def CreateField(inputfile, fieldlist):
    """ Create field"""
    for inputf in inputfile:

        log.msg("Input Shapefile: %s"%(inputf))
        column =  fieldlist[0]
        ftype  =  fieldlist[1]
    
        if ftype not in type2code:
            log.msg("%s is not a valide field type"%(ftype),"ERROR")
            quit()
    
        ogrtype = type2code[ftype]
    
        try:
            width     = int(fieldlist[2])
            precision = int(fieldlist[3])
            log.msg("Create field %s of type %s with %d width and %d precison"%(column,code2type[ogrtype],width,precision))
        except:
            log.msg("Create field %s of type %s"%(column,code2type[ogrtype]))
    
        driver = ogr.GetDriverByName('ESRI Shapefile')
        datasource = driver.Open(inputf, 1)
    
        if datasource is None:
            log.msg("Could not open file","ERROR")
            sys.exit(1)
    
        # get the data layer
        layer = datasource.GetLayer()
        layer_defn = layer.GetLayerDefn()
        
        # Add a new field
        new_field = ogr.FieldDefn(column, ogrtype)
        try:
            width     = int(fieldlist[2])
            precision = int(fieldlist[3])
            new_field.SetWidth(width)
            new_field.SetPrecision(precision)
        except:
            pass
        layer.CreateField(new_field)
    
        datasource = None

def AddSurface(inputfile, column):
    """ Add Surface """
    driver = ogr.GetDriverByName('ESRI Shapefile')
    datasource = driver.Open(inputfile, 1)

    if datasource is None:
        log.msg("Could not open file","ERROR")
        sys.exit(1)

    # get the data layer
    layer = datasource.GetLayer()
    layer_defn = layer.GetLayerDefn()
    
    # Add a new field
    new_field = ogr.FieldDefn(column, ogr.OFTReal)
    new_field.SetWidth(11)
    new_field.SetPrecision(3)
    layer.CreateField(new_field)

       
    for c,i in enumerate(layer):
        geom = i.GetGeometryRef()
        try:
            area = 1000.0*float(geom.GetArea())/1000.0 # convert m2 in ha
        except AttributeError:
            area = 0.0
        #layer.SetFeature(i)
        i.SetField(column, area)
        layer.SetFeature(i)

    datasource = None

def AdaptShapefile(inputfile, adapt):
    """ Adapt shapefile """
    driver = ogr.GetDriverByName('ESRI Shapefile')
    datasource = driver.Open(inputfile, 1)

    legend_file = adapt[0].split(".")[0]
   
    sys.path.insert(0,os.getcwd() )
    try:
        legend = importlib.import_module(legend_file)
    except:
        log.msg("Legend python file invalid","ERROR")
        quit()

    try:
        mapping = ast.literal_eval(adapt[1])
    except:
        log.msg("-ad (-adapt) parameters is invalid","ERROR")  
        quit()

 
    if datasource is None:
        log.msg("Could not open file","ERROR")
        sys.exit(1)

    # get the data layer
    layer = datasource.GetLayer()
    layer_defn = layer.GetLayerDefn()
    
    # Add all new field 
    for m in mapping:
        if(layer.GetLayerDefn().GetFieldIndex(mapping[m]) < 0):
            log.msg("Create %s field"%(mapping[m]))
            new_field = ogr.FieldDefn(mapping[m], ogr.OFTInteger)
            new_field.SetWidth(3)
            new_field.SetPrecision(0)
            layer.CreateField(new_field)

    log.msg("Convert old fields and fill new ones")
    for c,f in enumerate(layer):
        #geom = i.GetGeometryRef()
        #try:
        #    area = 1000.0*float(geom.GetArea())/1000.0 # convert m2 in ha
        #except AttributeError:
        #    area = 0.0
        #layer.SetFeature(i)
        for m in mapping:
            if f[m] == None:
                f.SetField(mapping[m], 0)
            else:
                try:
                    # If field contain a string, mapping to int is applied (for RPG class in general)_
                    f.SetField(mapping[m], legend.class2code[f[m]])
                except:
                    pass
                    # If field contain numerical string, it is is convert to int (for Class field such as D1 and D2 in RPG)
                    #f.SetField(mapping[m],legendd(f[m]))

            layer.SetFeature(f)

    datasource = None


def DeleteField(inputfile, fields):
    """ Delete Field"""

    driver = ogr.GetDriverByName('ESRI Shapefile')
    datasource = driver.Open(inputfile, 1)

    if datasource is None:
        log.msg("Could not open file","ERROR")
        sys.exit(1)

    for fi in fields:
        resp = input("Are you sure you want to delete the field %s (y or n) ?"%(fi))  
        if resp == 'y':
            # get the data layer
            layer = datasource.GetLayer()
            layer_defn = layer.GetLayerDefn()
            print("Delete field %s"%(fi))
            layer.DeleteField(layer_defn.GetFieldIndex(fi))

    datasource = None

def GenerateLegend(inputfileList,arg):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    try:
        column = arg[0]
        legend_file = arg[1]
    except:
        log.msg("The field and/or the file name are invalid","ERROR")
        quit()
    legend = []

    lfile = open(legend_file, 'w+')
    for inputfile in inputfileList:
        datasource = driver.Open(inputfile, 1)

        if datasource is None:
            log.msg("Could not open file","ERROR")
            sys.exit(1)

        # get the data layer
        layer = datasource.GetLayer()
        layer_defn = layer.GetLayerDefn()
        
        # Construct subclass set #
        for f in layer:
            fi = f[column]
            if fi not in legend:
                legend.append(fi)
        
        log.msg("Adds %s in legend (legend contain %d classes)"%(inputfile.split("/")[-1],len(legend)))
        print("#Adds %s in legend (legend contain %d classes)"%(inputfile.split("/")[-1],len(legend)),file=lfile)
   

    legend = sorted(legend)

    class2code = {}
    code2class = {}

    n = 0
    for c in legend:
        n += 1
        class2code[c] = int(n)
        code2class[int(n)] = c

    log.msg("The look-up table need to be manualy copy file %s"%(legend_file))
    print("class2code=",class2code, file = lfile)
    print("code2class=",code2class, file = lfile)
    # Export on disk

def GenStatField(inputfile, genstat):
    """ Calculate shapefile statistic """
 
    #classFilterType   = {"False":"All classes considered in the statistics","True":"Only selected classes considered in the statistics."}
    #featureFilterType = {"False":"All polygons considered in the statistics","True":"Invalid polygon discarded from the statistics."}
    #deleteType        = {"False":"All polygons kept in the input shapefile","True":"Invalid polygons removed from the input shapefile"}


    #inlist = ["","False","False","False"]
    #
    #for i,x in enumerate(statistics):
    #  inlist[i] = x
    column = genstat[0]
    try:
        sortby = genstat[1] # col/area/item 
    except:
        sortby = "field"

    if sortby not in ["field","polygon","area"]:
        log.msg("""The "sortby" argument is invalid""","ERROR")
        log.msg("Valid arguments: field, area or polygon","ERROR")
        quit()

    #print "*** Options chosen for the statistics ***"
    ##log.msg("Year: %s"%year)
    #log.msg(classFilterType[inlist[1]])
    #log.msg(featureFilterType[inlist[2]]) 
    #log.msg(deleteType[inlist[3]])
    # 
    #classFilter = eval(inlist[1])   #False(default) Stat on al class. True: Only selected class
    #featureFilter = eval(inlist[2]) #False(default) Keep all feature. True: Filter invalid feature.
    #delete = eval(inlist[3])        #False(default) True: Delete invalid feature.

    driver = ogr.GetDriverByName('ESRI Shapefile')
    datasource = driver.Open(inputfile, 1)

    if datasource is None:
        log.msg("Could not open file","ERROR")
        sys.exit(1)

    # get the data layer
    layer = datasource.GetLayer()
    layer_defn = layer.GetLayerDefn()
    
    # Construct subclass set #
    print("Calculating statistics for %s field..."%(column))
    stat = {}
    arearecord = set([])
    c = 0
    for f in layer:
        try:
          fi = f[column]
          try:
              prop = f[genstat[2]]
              cond = True
          except:
              cond = False
          #if classFilter:
          #  if fi not in subclasses: 
          #    fi = "OTH"
          #  else:
          #    fi = groupmap[fi]
        except ValueError:
          log.msg("The field %s does not exist."%(column),"ERROR")
          quit()
        geom = f.GetGeometryRef()
        try:
            area   = float(geom.GetArea())
            area100   = 0.0
            area99    = 0.0
            area98    = 0.0
            area97    = 0.0
            area96    = 0.0
            area95    = 0.0
            if prop==100: area100 = float(geom.GetArea())
            if prop>=99:  area99 = float(geom.GetArea())
            if prop>=98:  area98 = float(geom.GetArea())
            if prop>=97:  area97 = float(geom.GetArea())
            if prop>=96:  area96 = float(geom.GetArea())
            if prop>=95:  area95 = float(geom.GetArea())
        except:
            area      = float(geom.GetArea())
            area100   = 0.0
            area99    = 0.0
            area98    = 0.0
            area97    = 0.0
            area96    = 0.0
            area95    = 0.0
            c += 1

        if fi not in stat:
            if cond:
                if fi != None:
                    stat[fi] = np.array([1,area,area100,area99,area98,area97,area96,area95])
                else:
                    stat[-1] = np.array([1,area,area100,area99,area98,area97,area96,area95])
            else:
                if fi != None:
                    stat[fi] = np.array([1,area])
                else:
                    stat[-1] = np.array([1,area])

        else:
            if cond:
                if fi != None:
                    stat[fi] = stat[fi] + np.array([1,area,area100,area99,area98,area97,area96,area95])
                else:
                    stat[-1] = stat[-1] + np.array([1,area,area100,area99,area98,area97,area96,area95])
            else:
                if fi != None:
                    stat[fi] = stat[fi] + np.array([1,area])
                else:
                    stat[-1] = stat[-1] + np.array([1,area])


    # Calculate total polygons and surface
    if cond:
        total = np.array([0,0.0,0.0,0.0,0.0,0.0,0.0,0.0])
    else:
        total = np.array([0,0.0])
    for k in stat.keys():
        total = total +  stat[k]
            
 
    if sortby == "field":
        sortedStat = sorted(stat.items(), key=lambda x: x[0])
    if sortby == "polygon":
        sortedStat = sorted(stat.items(), key=lambda x: x[1][0],reverse = True)
    if sortby == "area":
        sortedStat = sorted(stat.items(), key=lambda x: x[1][1],reverse = True)

    if cond:
        print(" %s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"%("Class","#Poly.","Area (pix)","Area100","Area99","Area98","Area97","Area96","Area95"))
        print("_________________________________________")
        for ss in sortedStat:
            print(" %s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d"%(ss[0],ss[1][0],ss[1][1]/100.,ss[1][2]/100.,ss[1][3]/100.,ss[1][4]/100.,ss[1][5]/100.,ss[1][6]/100.,ss[1][7]/100))
    	    #print " %s\t%d\t%d"%(k,stat[k][0],stat[k][1])
        print("_________________________________________")
        print(" %s\t%d\t%.2f\t%3.1f"%("Total",total[0],total[1],100.0))
        print("(%d polygons with null surface detected)"%(c))
    else:
        print(" %s\t%s\t%s\t%s"%("Class","#Poly.","Area (ha)","Area (%)"))
        print("_________________________________________")
        for ss in sortedStat:
            print(" %s\t%d\t%.2f\t%3.1f"%(ss[0],ss[1][0],ss[1][1]/10000.,100.0*ss[1][1]/total[1]))
    	    #print " %s\t%d\t%d"%(k,stat[k][0],stat[k][1])
        print("_________________________________________")
        print(" %s\t%d\t%.2f\t%3.1f"%("Total",total[0],total[1],100.0))
        print("(%d polygons with null surface detected)"%(c))


def StatField(inputfile, statistics):
    """ Calculate shapefile statistic """
 
    classFilterType   = {"False":"All classes considered in the statistics","True":"Only selected classes considered in the statistics."}
    featureFilterType = {"False":"All polygons considered in the statistics","True":"Invalid polygon discarded from the statistics."}
    deleteType        = {"False":"All polygons kept in the input shapefile","True":"Invalid polygons removed from the input shapefile"}


    inlist = ["","False","False","False"]
    
    for i,x in enumerate(statistics):
      inlist[i] = x
 
    year = inlist[0]
    column = "C%s"%(year)
    smcol = "S%s"%(year)

    print("*** Options chosen for the statistics ***")
    #log.msg("Year: %s"%year)
    log.msg(classFilterType[inlist[1]])
    log.msg(featureFilterType[inlist[2]]) 
    log.msg(deleteType[inlist[3]])
     
    classFilter = eval(inlist[1])   #False(default) Stat on al class. True: Only selected class
    featureFilter = eval(inlist[2]) #False(default) Keep all feature. True: Filter invalid feature.
    delete = eval(inlist[3])        #False(default) True: Delete invalid feature.

    driver = ogr.GetDriverByName('ESRI Shapefile')
    datasource = driver.Open(inputfile, 1)

    if datasource is None:
        log.msg("Could not open file","ERROR")
        sys.exit(1)

    # get the data layer
    layer = datasource.GetLayer()
    layer_defn = layer.GetLayerDefn()
    
    # Construct subclass set #
    print("Calculating statistics for %s field..."%(column)) 
    stat = {}
    arearecord = set([])
    c = 0
    for f in layer:
        try:
          fi = f[column]
          surfmax1 = f["S17"]
          surfmax2 = f["S17"]
          if classFilter:
            if fi not in subclasses: 
              fi = "OTH"
            else:
              fi = groupmap[fi]
        except ValueError:
          log.msg("The field %s does not exist."%(column),"ERROR")
          quit()
        geom = f.GetGeometryRef()
        try:
            area = float(geom.GetArea())
        except:
            area = 0.0
            c += 1

        #if area not in arearecord and (f["C16"] != None or f["C17"] != None):
        #if area not in arearecord and ((area < surfmax1) or (area < surfmax2)):
        #if ((surfmax1 != 0.0) and (surfmax2 != 0.0)) or not featureFilter :
        if (not featureFilter) or ((surfmax1 != 0.0) and (surfmax2 != 0.0)):
          #if featureFilter:
          #  arearecord.add(area)
          if fi not in stat:
              stat[fi] = np.array([1,area])
          else:
              stat[fi] = stat[fi] + np.array([1,area])
        elif delete:
          fid = f.GetFID() 
          layer.DeleteFeature(fid)

    for k in sorted (stat.keys()):
        print(" %s\t%d\t%f"%(k,stat[k][0],stat[k][1]))
	#print " %s\t%d\t%d"%(k,stat[k][0],stat[k][1])
    print("(%d polygons with null surface detected)"%(c))

def RemovePolygons(inputfile, removefile):
    """
    Remove feature in shapefile
    parameter -rm:
    - if -rm  a.txt: remove fid contain in file
    - if -rm tag: Remove features such that the field OK is equal to 0.0
    """
    if removefile == "tag":
      outputfile = inputfile[:-4] + "_filtered" + inputfile[-4:] 
      outname = inputfile[:-4].split("/")[-1] + "_filtered"
    else:
      outputfile = inputfile[:-4] + "_rm" + inputfile[-4:] 
      outname = inputfile[:-4].split("/")[-1] + "_rm"
      try:
        removeid = np.loadtxt(removefile)

      #except ValueError:
      #  print "Trying to read file with special formating..."
      #  removeid = np.loadtxt(removefile,delimiter = r" or $id = ")
      #  print "Reading succed"
      #  print removeid[:10]
      #  print removeid[:-10]
      #  print len(removeid)
      #  quit()
      except:
        raise
        print("The file %s does not exist or has an incorrect format."%(removefile))
        quit()

    resp = raw_input("Are you sure you want to delete the %d given polygons (y or n) ?"%(len(removeid)))  
    if resp == 'y':
      driver = ogr.GetDriverByName('ESRI Shapefile')
      datasource = driver.Open(inputfile, 1)
      dataout    = driver.CreateDataSource(outputfile) 
      if datasource is None:
          log.msg("Could not open file","ERROR")
          sys.exit(1)
  
      # get the data layer
      layer = datasource.GetLayer()
      proj =layer.GetSpatialRef()
      out_layer = dataout.CreateLayer(outname,proj, ogr.wkbPolygon )
      layer_defn = layer.GetLayerDefn()
      
      # Add Field in output shapefile #  
      for i in range(layer_defn.GetFieldCount()):
          out_layer.CreateField(layer_defn.GetFieldDefn(i) )

     # print ""
     # for f in layer:
     #   fid = f.GetFID()
     #   print "[BEF]",fid,f["ID"],f["C17"],f["S17"]
     #   
     # print ""        
      layer.ResetReading() 
      for f in layer:
        fid = f.GetFID()
        if removefile == "tag":
           if f["OK"]  != 0.0:
            out_layer.CreateFeature(f)
        else:    
          if fid not in removeid:
            out_layer.CreateFeature(f)
 

def FilterPolygons(inputfile, filterParameters):
    """
    Filter feature in shapefile
    parameter -rm:
    - if -rm  a.txt: remove fid contain in file
    - if -rm tag: Remove features such that the field OK is equal to 0.0
    """
    field = filterParameters[0]
    keepClasse = [int(x) for x in filterParameters[1:]]

    #print "Inputfile:",inputfile,
    #print "Field:",field
    #print "Keep classes: ", keepClasse

    outputfile = inputfile[:-4] + "_FilteredClasses" + inputfile[-4:] 
    outname = inputfile[:-4].split("/")[-1] + "_FilteredClasses"

    driver = ogr.GetDriverByName('ESRI Shapefile')
    datasource = driver.Open(inputfile, 1)
    dataout    = driver.CreateDataSource(outputfile) 
    if datasource is None:
        log.msg("Could not open file","ERROR")
        sys.exit(1)
  
    # get the data layer
    layer = datasource.GetLayer()
    proj =layer.GetSpatialRef()
    out_layer = dataout.CreateLayer(outname,proj, ogr.wkbPolygon )
    layer_defn = layer.GetLayerDefn()

    # Add Field in output shapefile #  
    for i in range(layer_defn.GetFieldCount()):
        out_layer.CreateField(layer_defn.GetFieldDefn(i) )


    layer.ResetReading() 
    for f in layer:
        fid = f.GetFID()
        if f[field] in keepClasse:
            out_layer.CreateFeature(f)

def ExecuteMean(inputfile):
    inputf = inputfile[0]
    log.msg("Shapefile  %s is going to be update"%(inputf))

    driver = ogr.GetDriverByName('ESRI Shapefile')
    datasource = driver.Open(inputf, 1)

    if datasource is None:
        log.msg("Could not open file","ERROR")
        sys.exit(1)

    # get the data layer
    layer = datasource.GetLayer()
    layer_defn = layer.GetLayerDefn()

    for f in layer:
        try:
            arithmetic_mean = int((f["PROP_15"] + f["PROP_16"] + f["PROP_17"])/3.0)  
            geometric_mean  = int((f["PROP_15"]*f["PROP_16"]*f["PROP_17"])**(1/3))

            f.SetField("PROP_A", arithmetic_mean)
            layer.SetFeature(f)
            f.SetField("PROP_G", geometric_mean)
            layer.SetFeature(f)
        except:
            pass

    datasource = None


def Execute(inputfile, param):
    """ Calculate shapefile statistic """
    inputf = inputfile[0]

    kin1 = param[0]
    kout = param[1]

    log.msg("Shapefile  %s is going to be update"%(inputf))
    log.msg("Conversion RPG from %s to %s"%(kin1,kout))

    driver = ogr.GetDriverByName('ESRI Shapefile')
    datasource = driver.Open(inputf, 1)

    if datasource is None:
        log.msg("Could not open file","ERROR")
        sys.exit(1)

    # get the data layer
    layer = datasource.GetLayer()
    layer_defn = layer.GetLayerDefn()
  
    total = 0
    type1 = 0
    type2 = 0
    type3 = 0
    for fi in layer:
        total += 1
        incolumn = fi[kin1]
        #layer.SetFeature(i)
        try:
            val = rpgClasses.index(incolumn) + 1
            type1 += 1
        except:
            try:
                val = derobesClasses.index(incolumn) + 1
                type2 += 1
            except:
                try:
                    incolumn = fi[kin2]
                    val = derobesClasses.index(incolumn) + 1
                    type3 += 1
                except:
                    val = 0

        fi.SetField(kout, val)
        layer.SetFeature(fi)
    log.msg("Total: %d"%(total))
    log.msg("Type Class RGP: %d"%(type1))
    log.msg("Type Derobe 1: %d"%(type2))
    log.msg("Type Derobe 2: %d"%(type3))


def Union(inputfiles, outputfile):
    in1 = inputfiles[0]
    in2 = inputfiles[1]
    print("%s UNION %s = %s"%(in1, in2, outputfile))
    print("TODO")
    #driver = ogr.GetDriverByName('ESRI Shapefile')
    #ds1 = driver.Open(in1, 1)
    #ds2 = driver.Open(in2, 1)

    #if ds1 is None or ds2 is None:
    #    print 'Could not open file'
    #    sys.exit(1)

    ## get the data layer
    #layer1 = ds1.GetLayer()
    #layer2 = ds2.GetLayer()
    #layer_defn_1 = layer1.GetLayerDefn()
    #layer_defn_2 = layer2.GetLayerDefn()
 
    ##for f in layer1:
    ##    geom = f.GetGeometryRef()



 

######################################################## MAIN #################################################################
if __name__ == "__main__":

    parser=argparse.ArgumentParser()
    parser.add_argument("-in", "--inputfile", nargs='+', help="Input shapefile")
    parser.add_argument("-re", "--rename", help="""Rename shapefile field. Syntax example:
./ShapefileEditor.py -in shapefile.shp -re "{'Old1':'New1','Old2':'New2'}"
""")
    parser.add_argument("-cr", "--create", nargs='+', help="""Create new fields of give type, width and precision
 Syntax:
./ShapefileEditor.py -in shapefile.shp -cr ColomnName Type (Width Precision) 
 Example:
./ShapefileEditor.py -in shapefile.shp -cr Value Int 11 3 
    """)
    parser.add_argument("-ar", "--area", help="Create new field that contains polygon area.")
    parser.add_argument("-ad", "--adapt", nargs="+",help="Adapt shapefile to numerical form.")
    parser.add_argument("-de", "--delete", nargs="+", help="Delete the field field_name.")
    parser.add_argument("-gs", "--genstat", nargs='+',help="""Calculate general statistics for a given field.
Syntax:
./ShapefileEditor.py -in shapefile.shp -gs field sortby (sortby = field (default), area or polygon)
""")

    parser.add_argument("-st", "--statistics", nargs='+',help="""Calculate statistics for a given field.
Syntax:
./ShapefileEditor.py -in shapefile.shp -st field classfilter featurefilter
""")

    parser.add_argument("-le", "--legend", nargs="+",help="Create legend look-up table")
    parser.add_argument("-un", "--union", help="Create the geometric union between two shapefiles.")
    parser.add_argument("-rm", "--remove", help="Remove polygons with id contain in given file.")
    parser.add_argument("-fi", "--filter", nargs="+",help="Only keep listed classes polygons.")
    parser.add_argument("-ex", "--execute", nargs="+",help="Execute hardcoded algorithm. See source code")
    args=parser.parse_args()
 
    if (args.inputfile==None and 
        args.rename==None and
        args.create==None and
        args.area==None and
        args.delete==None and
        args.genstat==None and
        args.statistics==None and
        args.legend==None and
        args.filter==None and
        args.union==None):
      # Handle help message because mutual exclusive option required it.
      print("usage: ShapefileEditor [-h] [-re] namelist [-cr] namelist [-ar] column_name [-de] field_name [-gs] column_name [-st] column_name [-le] field legend_file [-un] output_shapefile [-rm] remove.csv [-ex] parameters [-fi] parameters [-in] SHAPEFILES")
      print("ShapefileEditor: error: too few arguments")
      quit()

    if args.inputfile!=None:
      DisplayField(args.inputfile)

    if args.inputfile!=None and args.rename!=None:
      RenameField(args.inputfile[0],args.rename)
      quit()

    if args.inputfile!=None and args.create!=None:
      CreateField(args.inputfile,args.create)
      quit()

    if args.inputfile!=None and args.area!=None:
      AddSurface(args.inputfile[0],args.area)
      quit()

    if args.inputfile!=None and args.delete!=None:
      DeleteField(args.inputfile[0],args.delete)
      quit()

    if args.inputfile!=None and args.genstat!=None:
      GenStatField(args.inputfile[0],args.genstat)
      quit()

    if args.inputfile!=None and args.statistics!=None:
      StatField(args.inputfile[0],args.statistics)
      quit()

    if args.inputfile!=None and args.legend!=None:
      GenerateLegend(args.inputfile, args.legend)
      quit()

    if args.inputfile!=None and args.adapt!=None:
      AdaptShapefile(args.inputfile[0], args.adapt)
      quit()

    if args.inputfile!=None and args.remove!=None:
      RemovePolygons(args.inputfile[0],args.remove)
      quit()

    if args.inputfile!=None and args.filter!=None:
      FilterPolygons(args.inputfile[0],args.filter)
      quit()

    if args.inputfile!=None and args.union!=None:
      Union(args.inputfile,args.union)
      quit()

    if args.inputfile!=None and args.execute!=None:
      ExecuteMean(args.inputfile)
      quit()

