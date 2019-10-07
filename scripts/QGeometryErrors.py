import numpy as np
from datetime import datetime

if(True):
    errorfile = open("/home/arnaudl/Documents/ColzaDigital/scripts/Qerrors2015.txt","w+")
    layer = iface.activeLayer()
    features = layer.getFeatures()
    
    interior = 0
    doublon = 0
    other = 0
    
    idset = set()
    errset = set()
    allset = set()
    for i,f in enumerate(features):
        st_id  = f["featureID"]
        st_err = f["ErrorDesc"]
        id = int(st_id)
        desc = st_err.split()
        errid = None
        
        for val in desc:
            try:
                errid = int(val)
            except:
                pass
        idset.add(id)
        errset.add(errid)
        
        if desc[0] == "A":
            interior += 1
        elif desc[0] == "Doublon":
            doublon +=1
            errorfile.write("%s\n"%(id))
        else:
            other += 1


        
        # Order couple of id to avoid double counting
        if id < errid:
            a = id
            b = errid
        else:
            b = id
            a = errid
        
        allset.add( (a,b))
    errorfile.close()
    print len(idset),len(errset)
    print interior,doublon,other
    print len(allset)
    
    print("DONE")
    