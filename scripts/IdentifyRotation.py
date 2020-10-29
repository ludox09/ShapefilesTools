#!/usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt

def IdRotation(inputfile, class1, class2):

     # Construct index convertor
     c2i = {}
     for i,s in enumerate(externalclass):
         c2i[s] = i

     # Fast duplication of input shapefile
     outputfile = updatename(inputfile,"PREV")
     for ext in ["shp","cpg","dbf","shx","prj"]:
         before = inputfile.replace("shp",ext) 
         after  = updatename(before,"PREV")
         os.system("cp %s %s"%(before,after))

     driver = ogr.GetDriverByName('ESRI Shapefile')
     datasource = driver.Open(outputfile, 1)

     if datasource is None:
         log.msg("Could not open file","ERROR")
         sys.exit(1)

     # get the data layer
     layer = datasource.GetLayer()
     layer_defn = layer.GetLayerDefn()
 
     # Add a new field
     new_class = ogr.FieldDefn("CULT_P", ogr.OFTString)
     new_class.SetWidth(3)
     new_class.SetPrecision(0)
     layer.CreateField(new_class)

     new_code = ogr.FieldDefn("CODE_P", ogr.OFTInteger)
     new_code.SetWidth(3)
     new_code.SetPrecision(0)
     layer.CreateField(new_code)

     new_prop = ogr.FieldDefn("PROP_P", ogr.OFTInteger)
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

             f.SetField("CULT_P", maxclass_c)
             layer.SetFeature(f)

             f.SetField("CODE_P", maxidx_c)
             layer.SetFeature(f)

             f.SetField("PROP_P", maxprop_c)
             layer.SetFeature(f)
             ok += 1
         except:
             #ignore idex not find
             ko += 1

     log.msg("# of Polygons recorded: %d"%(ok),"DEBUG")
     log.msg("# of Polygons discared: %d"%(ko),"DEBUG")

          
 
     datasource = None


if __name__ == "__main__":


