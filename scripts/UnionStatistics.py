#!/usr/bin/python

""" Ludo 25/09/2019 """

import ogr, os, sys
import string
import argparse
import json
import ast
import numpy as np
import parameters as param
import infolog
dirname = os.path.dirname(__file__)
tolatexpath = os.path.join(dirname, '/tolatex')
sys.path.insert(1,tolatexpath)
#sys.path.insert(1, '/tolatex')
import tolatex.tolatex as latex

log = infolog.infolog()
#log.set_level("WARNING")
#log.msg("Test for debug message1","DEBUG")
#log.msg("Test for debug message2","DEBUG")
#log.msg("Test for debug message3","DEBUG")
#log.msg("Test for info message (default)")
#log.msg("Test for warning message","WARNING")
#log.msg("Test for debug message4","DEBUG")
#log.msg("Test for error message","ERROR")
#log.msg("Test for fatal message","FATAL")


subclasses = param.subclasses
groupmap1   = param.groupmap1bis


# Add new type if needed
code2type = {ogr.OFTInteger:  "Int   ",
             ogr.OFTReal:     "Real  ",
             #ogr.OFTInteger64:"Int64 ",
             ogr.OFTString:   "String"}

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
           
        print line
        print sfield
        print line
        print stype
        print swidth
        print sprec
        print line
        print ""

def StatField(inputfile, statistics):
    """ Calculate shapefile statistic """

    inputfile.append(inputfile[-1]) # Consider last input file twice.

    classFilterType   = {"False":"All classes considered in the statistics","True":"Only selected classes considered in the statistics."}
    featureFilterType = {"False":"All polygons considered in the statistics","True":"Invalid polygon discarded from the statistics."}
    deleteType        = {"False":"All polygons kept in the input shapefile","True":"Invalid polygons removed from the input shapefile"}

    classFilterID   = {"False":"AllCla","True":"SelCla"}
    featureFilterID = {"False":"","True":"_Filtered"}

    inlist = ["","","False","False",""]
    
    for i,x in enumerate(statistics):
      inlist[i] = x

    year1 = int(inlist[0])
    year2 = int(inlist[1])


    log.msg("Options chosen for the statistics:")
    log.msg("    - Year1: %s"%year1)
    log.msg("    - Year2: %s"%year2)
    log.msg("    - " + classFilterType[inlist[2]])
    log.msg("    - " + featureFilterType[inlist[3]]) 
    #log.msg(deleteType[inlist[3]])
     
    classFilter = inlist[2]   #False(default) Stat on al class. True: Only selected class
    featureFilter = inlist[3] #False(default) Keep all feature. True: Filter invalid feature.
    OutputName = inlist[4]     #delete = eval(inlist[3])        #False(default) True: Delete invalid feature.

    #colList = ["C16","C17","C16","C17"]
    colList = ["C%d"%(year1),"C%d"%(year2),"C%d"%(year1),"C%d"%(year2)]
    
    stat = {}
    for i,infile in enumerate(inputfile):
        column = colList[i]
        log.msg("Reading column %s in file %s"%(column,infile))
        driver = ogr.GetDriverByName('ESRI Shapefile')
        datasource = driver.Open(infile, 1)

        if datasource is None:
            log.msg("Could not open file %"%(infile),"ERROR")
            sys.exit(1)

        # get the data layer
        layer = datasource.GetLayer()
        layer_defn = layer.GetLayerDefn()
       
        surfset = set() 
        layer.ResetReading()
        for f in layer:
            fi = f[column]
            if fi not in subclasses:
                fi = "OTH"
            else:
                fi = groupmap1[fi]
            geom = f.GetGeometryRef()
            try:
                area = float(geom.GetArea())
            except:
                area = 0.0

            # Get surface only on Overled files 
            if(i>1):
                surfmax1 = (f["S" + colList[2][1:]])
                surfmax2 = (f["S" + colList[3][1:]])
            else:
                surfmax1 = 2.0
                surfmax2 = 2.0
            if i>1:
                f.SetField("OK", 0)
                layer.SetFeature(f)

            if (not eval(featureFilter)) or ((surfmax1 != 0.0) and (surfmax2 != 0.0)):
                if i>1: 
                    surfset.add(f["AREA"])
                    f.SetField("OK", 1)
                    layer.SetFeature(f)

                if fi not in stat:
                    stat[fi] = np.array([[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]])
                    
                    stat[fi][i][0] = 1
                    stat[fi][i][1] = area

                    if i>1:
                        farea = f['AREA']
                        if( ((np.abs(surfmax1-farea)/(farea+1e-10)) < 0.02) and ((np.abs(surfmax2-farea)/(farea+1e-10)) < 0.02) ):
                            stat[fi][i+2][0] = 1
                            stat[fi][i+2][1] = area

                else:

                    stat[fi][i][0] += 1
                    stat[fi][i][1] = stat[fi][i][1] + area

                    if i>1:
                        farea = f['AREA']
                        if( ((np.abs(surfmax1-farea)/(farea+1e-10)) < 0.02) and ((np.abs(surfmax2-farea)/(farea+1e-10)) < 0.02) ):
                            stat[fi][i+2][0] += 1
                            stat[fi][i+2][1] = stat[fi][i][1] + area



        if eval(featureFilter) and i>1:
            layer.ResetReading()
            for f in layer:
                fi = f[column]
                if fi not in subclasses:
                    fi = "OTH"
                else:
                    fi = groupmap1[fi]
                geom = f.GetGeometryRef()
                try:
                    area = float(geom.GetArea())
                except:
                    area = 0.0

                # Get surface only on Overled files 
                if(i>1):
                    surfmax = (f["S" + column[1:]])
                    surfmax1 = (f["S" + colList[2][1:]])
                    surfmax2 = (f["S" + colList[3][1:]])
                else:
                    surfmax = 2.0
                    surfmax1 = 2.0
                    surfmax2 = 2.0

                if f['AREA'] not in surfset and (surfmax != 0.0):
                    surfset.add(f["AREA"]) 
                    f.SetField("OK", 2)
                    layer.SetFeature(f)

                    if fi not in stat:
                        stat[fi] = np.array([[0,0],[0,0],[0,0],[0,0]])
                        stat[fi][i][0] = 1
                        stat[fi][i][1] = area
                    else:
                        stat[fi][i][0] += 1
                        stat[fi][i][1] = stat[fi][i][1] + area
 
 #       if eval(featureFilter) and i>1:
 #           layer.ResetReading()
 #           for f in layer:
 #               fi = f[column]
 #               if fi not in subclasses:
 #                   fi = "OTH"
 #               else:
 #                   fi = groupmap1[fi]
 #               geom = f.GetGeometryRef()
 #               try:
 #                   area = float(geom.GetArea())
 #               except:
 #                   area = 0.0

 #               # Get surface only on Overled files 
 #               if(i>1):
 #                   surfmax1 = (f["S" + colList[2][1:]])
 #                   surfmax2 = (f["S" + colList[3][1:]])
 #               else:
 #                   surfmax1 = 2.0
 #                   surfmax2 = 2.0

 #               if f['AREA'] not in surfset and (surfmax2 != 0.0):
 #                   surfset.add(f["AREA"]) 
 #                   f.SetField("OK", 3)
 #                   layer.SetFeature(f)

 #                   if fi not in stat:
 #                       stat[fi] = np.array([[0,0],[0,0],[0,0],[0,0]])
 #                       stat[fi][i][0] = 1
 #                       stat[fi][i][1] = area
 #                   else:
 #                       stat[fi][i][0] += 1
 #                       stat[fi][i][1] = stat[fi][i][1] + area
 #
   #         #if area not in arearecord and (f["C16"] != None or f["C17"] != None):
   #         #if area not in arearecord and ((area < surfmax1) or (area < surfmax2)):
   #         #if ((surfmax1 != 0.0) and (surfmax2 != 0.0)) or not featureFilter :
   #         if (not featureFilter) or ((surfmax1 != 0.0) and (surfmax2 != 0.0)):
   #           #if featureFilter:
   #           #  arearecord.add(area)
   #           if fi not in stat:
   #               stat[fi] = np.array([1,area])
   #           else:
   #               stat[fi] = stat[fi] + np.array([1,area])
   #         elif delete:
   #           fid = f.GetFID() 
   #           layer.DeleteFeature(fid)

    tf = "|l||r|r||r|r||r|r||r|r||r|r||r|r||r|r||r|r|"
    #head = [["Class","P%d"%(year1),"S%d"%(year1),"P%d"%(year2),"S%d"%(year2),"UP%d"%(year1),"US%d"%(year1),"UP%d"%(year2),"US%d"%(year2),"DS%d"%(year1),"DS%d"%(year2)]]
    head = [["Class","P%d"%(year1),"S%d"%(year1),"P%d"%(year2),"S%d"%(year2),"UP%d"%(year1),"US%d"%(year1),"UP%d"%(year2),"US%d"%(year2),"IP%d"%(year1),"IS%d"%(year1),"IP%d"%(year2),"IS%d"%(year2),"DUS%d"%(year1),"DUS%d"%(year2),"DIS%d"%(year1),"DIS%d"%(year2)]]
    mat = []
    rsum = 0.0
    for k in sorted (stat.keys()):
        rsum = rsum + stat[k].flatten()
        row = stat[k].flatten().tolist()
        rowstring  = []
        for i,x in enumerate(row):
            rowstring.append("\\numprint{%d}"%(x))

        diff1 = 200.0*(row[5]-row[1])/(row[5] + row[1] + 0.0000000001)
        diff2 = 200.0*(row[7]-row[3])/(row[7] + row[3] + 0.0000000001)
        diff3 = 200.0*(row[9]-row[1])/(row[9] + row[1] + 0.0000000001)
        diff4 = 200.0*(row[11]-row[3])/(row[11] + row[3] + 0.0000000001)
        rowstring.append("%.1f"%diff1)
        rowstring.append("%.1f"%diff2)
        rowstring.append("%.1f"%diff3)
        rowstring.append("%.1f"%diff4)


        rowstring.insert(0,k)
        mat.append(rowstring)

    rsum = rsum.tolist()
    sumstring = []
    for i,x in enumerate(rsum):
        sumstring.append("\\numprint{%d}"%(x))

    diff1 = 200.0*(rsum[5]-rsum[1])/(rsum[5] + rsum[1] + 0.0000000001)
    diff2 = 200.0*(rsum[7]-rsum[3])/(rsum[7] + rsum[3] + 0.0000000001)
    diff3 = 200.0*(rsum[9]-rsum[1])/(rsum[9] + rsum[1] + 0.0000000001)
    diff4 = 200.0*(rsum[11]-rsum[3])/(rsum[11] + rsum[3] + 0.0000000001)
    sumstring.append("%.1f"%diff1)
    sumstring.append("%.1f"%diff2)
    sumstring.append("%.1f"%diff3)
    sumstring.append("%.1f"%diff4)


    sumstring.insert(0,"TOT")
    #sumstring.append("x")
    #sumstring.append("x")
    sumstring = [sumstring]

    log.msg("Export to pdf...")

    doc = latex.latexdoc(OutputName+"_%s%s"%(classFilterID[classFilter],featureFilterID[featureFilter]))
    doc.write("\\begin{landscape}")
    doc.title("Comparaison shapefiles")
    doc.write("\\section{Files used}")
    doc.write("\\begin{itemize}")
    doc.write("\\item \\begin{verbatim} %s \\end{verbatim}"%inputfile[0])
    doc.write("\\item \\begin{verbatim} %s \\end{verbatim}"%inputfile[1])
    doc.write("\\item \\begin{verbatim} %s \\end{verbatim}"%inputfile[2])
    doc.write("\\end{itemize}")

    doc.write("\\section{Parameters used}")
    doc.write("\\begin{itemize}")
    doc.write("\\item %s"%classFilterType[classFilter])  
    doc.write("\\item %s"%featureFilterType[featureFilter])
    doc.write("\\end{itemize}")

    # change order




    #doc.tableau([head,mat,sumstring],tf,caption="%d - %d - %s - %s"%(year1, year2, classFilterID[classFilter], featureFilterID[featureFilter][1:]))
    doc.tableau([head,mat,sumstring],tf,caption="%d - %d - %s - %s"%(year1, year2, classFilterID[classFilter], featureFilterID[featureFilter][1:]))
    doc.write("\\end{landscape}")
    doc.close()

    log.msg("Done")
    quit()




######################################################## MAIN #################################################################
if __name__ == "__main__":

    parser=argparse.ArgumentParser()
    parser.add_argument("-in", "--inputfile", nargs='+', help="Input shapefile")
    parser.add_argument("-st", "--statistics", nargs='+',help="""Calculate statistics for a given field.
Syntax:
./ShapefileEditor.py -in shapefile.shp -st field classfilter featurefilter"
""")
    args=parser.parse_args()
 
    if (args.inputfile==None and  args.statistics==None):
      # Handle help message because mutual exclusive option required it.
      print "usage: ShapefileEditor [-h] [-st] column_name [-in] SHAPEFILES"
      print "ShapefileEditor: error: too few arguments"
      quit()

    if args.inputfile!=None:
      DisplayField(args.inputfile)

    if args.inputfile!=None and args.statistics!=None:
      StatField(args.inputfile,args.statistics)
      quit()

