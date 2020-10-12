#!/usr/bin/env python3
# Update        - 29/08/2019
# Ludo - CesBIO - 29/08/2019
import os,sys
import glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LogNorm
from matplotlib import cm 
import matplotlib as mpl
import matplotlib.backends.backend_pdf as mpdf
from matplotlib.colors import LinearSegmentedColormap
import infolog
import importlib

log = infolog.infolog()
whitemap = LinearSegmentedColormap.from_list('mycmap',['white','white'])


def export_to_csv(filename,data,legend):
    """
       Sortcut to export to csv with header legend
    """
    header = ""
    for l in legend:
        header=header+"%s,"%(l)
    header = header[:-1]
    np.savetxt(filename, data, fmt = "%d",delimiter=",", header=header)


def adaptToLegend(data,groups):
    # Load data structure
    legend = list(data["legend"])

    #parcels = data["parcels"]
    # Only load surface because it willbe easier to recaculate condproba and invproba than callaping them
    surface = data["surface"]

    # Construct new legend list
    old_keys = []
    new_keys = []
    collapse_indices = {}
    keep_indices = []
    for i,x in enumerate(legend):
        if x in groups.keys():
            mapping = groups[x]
            if mapping != None:
                if(mapping not in new_keys):
                    new_keys.append(mapping)
                    collapse_indices[mapping] = [i]
                else:
                    collapse_indices[mapping].append(i)

        else:
            mapping = x
            keep_indices.append(i)
            if(mapping not in old_keys):
                old_keys.append(mapping)
    new_legend = old_keys + new_keys


    # Reduce surfaces matrices 
    #new_surface = surface[keep_indices][:,keep_indices]

    # Add collapsed data
    mcol = [np.sum(surface[:,collapse_indices[k]], axis = 1, keepdims = True) for k in collapse_indices.keys()]
    mcol.insert(0,surface[:,keep_indices])
    mtemp = np.hstack(tuple(mcol))
    mrow  = [np.sum(mtemp[collapse_indices[k],:], axis = 0, keepdims = True) for k in collapse_indices.keys()]
    mrow.insert(0,mtemp[keep_indices,:])
    new_surface = np.vstack(tuple(mrow))

    # Sort by pj - Bigger to smallest
    pi = np.sum(new_surface, axis=1)
    sidx = np.argsort(pi)[::-1]
    new_surface = (new_surface[sidx])[:,sidx]
    new_legend = list(np.array(new_legend)[sidx])

    # Recalculate pi, pj , CondPro and InvPro
    pi = np.sum(new_surface, axis=1)
    pj = np.sum(new_surface, axis=0)


    CondPro  = 0.0*new_surface
    InvPro   = 0.0*new_surface
    for i,x in enumerate(pi):
        if(x != 0.0):
            CondPro[i] = new_surface[i]/x
        else:
            CondPro[i] = new_surface[i]*0

    for i,y in enumerate(pj):
        if(y != 0.0):
            InvPro[:,i]  = new_surface[:,i]/y
        else:
            InvPro[:,i]  = new_surface[:,i]*0
    
    CondPro = 100.0*CondPro
    InvPro  = 100.0*InvPro


    # Gather in data structure
    new_data = {} 
    new_data["legend"] = new_legend
    #new_data["parcels"] = data["parcels"]
    new_data["surface"] = new_surface
    new_data["condproba"] = CondPro
    new_data["invproba"] = InvPro
    
    return new_data


def scientific(val,cmap,vmin,vmax):
    if(vmin != 0 and vmax != 100):
        norm = LogNorm(vmin=vmin, vmax=vmax)
    else:
        norm = mpl.colors.Normalize(vmin=0,vmax=100)
    # String #
    if (val != 0):
        try:
            e = int(np.floor(np.log10(abs(val))))
            m = val/10**e
        except ValueError:
            print(val) 
            e = 0
            m = 0
    else:
        m = val
        e = 0

    #print m,e
    #if(round(m) >= 10):
    #  m = m/10.0
    #  e = e+1
    #print m,e

 
    if( (-1 < e) and (e < 4) ):
      fval = "%d"%(m)
    elif (e<0):
      fval = "%.fe%d"%(m,e)
    else:
      fval = "%.1fe%d"%(m,e)
   
    # Color #
    #fcol = cmap(norm(val)) 
    fcol = cm.rainbow(norm(val)) 
    r = 2*fcol[0] 
    g = fcol[1]
    b = fcol[2]
    v = (r+g+b)/3.0
 
    if(cmap == "rainbow"):
      if( v > 0.7 ):
        fcol =  'black' 
      else:
        fcol =  'black'

      fval = "%d"%(val)
    else:
      if( v > 0.7 ):
        fcol =  'black' 
      else:
        fcol =  'black'
      fval = "%3.1f"%(val)

    return fval,fcol


def exportNew(matList,cmlist,classnames,filepdf,title,year1,year2):
    # Colormap
    filename = filepdf
    pdfplot = mpdf.PdfPages(filename)

    classnamesX = classnames.copy()
    classnamesY = classnames.copy()

    classnamesX.append("sum%d"%(year1))
    classnamesY.append("sum%d"%(year2))

    for k,mat in enumerate(matList):
        cmap = cmlist[k]
        if cmlist[k] == "white":
            cmap = whitemap 

	# Adapt values shape


        diag1 = np.diag(mat)
        diag2 = np.diag(mat)
        Sum1 = np.sum(mat, axis=1)
        # Glue row sum as new column
        mat = np.hstack((mat,Sum1.reshape(len(Sum1),1)))

        # Glue column sum as new row
        Sum2 = np.sum(mat, axis=0)
        mat = np.vstack((mat,Sum2))
        Nmat = len(mat)

        epsilon = 1e-10
        ##diff = 200.0*(Sum2 - Sum1)/(Sum1+Sum2 + epsilon)

        Sum1 = Sum1.reshape(1,-1).T
        diag1 = diag1.reshape(1,-1).T

        #diag1 = 100.0*diag1/(Sum1+epsilon)
        #diag2 = 100.0*diag2/(Sum2+epsilon)

        #diag2 = [diag2]
        #Sum2 = [Sum2]
        #diff = [diff]

        # Initialize plot
	#plottitle = "%s - Averages Confusion Matrix - %s - %s"%(title,method,date)
        plottitle = "%s"%(title[k])
        fig = plt.figure(figsize=(40,41))
        fig.suptitle(plottitle, size = 40) 

        #ax1 = fig.add_subplot(grid[0,0])
        ax1 = fig.add_subplot(1,1,1)
      
        # Add titles
        #ax1.set_title("Overall Accuracy = %.2f +/- %.2f %%"%(OA,Int),size=20)
        lsize = (50 - Nmat)
        #ax4.set_title("FScore (%)")
        
        lin = np.arange(Nmat)
        linsup = np.arange(Nmat+1) + 0.5
        
        # Major ticks
        ax1.set_xticks(lin);
        ax1.set_yticks(lin);

        # Minor ticks
        ax1.set_xticks(linsup, minor=True);
        ax1.set_yticks(linsup, minor=True);

        # Labels for major ticks
        ax1.set_xticklabels([]);
        ax1.set_yticklabels([]);
       
        # Labels for minor ticks
        ax1.set_xticklabels(classnamesX, rotation=0, minor = True, size = lsize);
        ax1.set_yticklabels(classnamesY, minor = True, size = lsize);
        
        # Gridlines based on minor ticks
        ax1.grid(which='major', linestyle = '-', color = 'black', linewidth=1)
        ax1.axhline(len(mat)-1, linestyle='-', linewidth=5, color='k')
        ax1.axvline(len(mat)-1, linestyle='-', linewidth=5, color='k')
        
        # col and row plot size
        extentMat = [0,len(mat[0]),len(mat[0]),0]
        extentCol = [0,1,len(mat[0]),0]
        extentRow = [0,len(mat[0]),1,0]

	#MinVal = np.max(np.sum(mat,axis = 1))
        MinVal = np.min(mat[np.nonzero(mat)])
        MaxVal = np.max(np.sum(mat,axis = 1))
        #nsize = 22
        nsize = (50 - Nmat) 
        for i in range(Nmat):
          for j in range(Nmat):
            #ax1.text(i+0.5,j+0.5,"%.1E"%(mat[i,j]), color='black', ha='center', va='center', rotation=45, size = 5)
            fval,fcolor = scientific(mat[j,i],cmap,MinVal,MaxVal)
            if i == j:
                # Hilight diagonal
                fcolor = "#800000"
                # Do not print
            if ( not(i==(Nmat-1) and j==(Nmat-1))):
                ax1.text(i+0.5,j+0.5,fval, color=fcolor, ha='center', va='center', rotation=45, size = nsize)

        pl1 = ax1.imshow(mat, extent = extentMat, interpolation='none', aspect='equal',cmap = cmap, norm=LogNorm(vmin=MinVal, vmax=MaxVal)) 

        #fig.colorbar(pl1, ax = ax1, fraction=0.046, pad=0.04)
        #pdfplot.savefig(fig,bbox_inches='tight')
        pdfplot.savefig(fig)
    pdfplot.close()   

#plt.tight_layout()


if __name__ == "__main__":

    sys.path.insert(0,os.getcwd())
    # Import test files #
    #data = np.load("StatStructure-%d-%d-%s"%(year1,year2,name), legend = npsc, groupmap = groupmap, parcels=mat, surface=sur,condproba=CondPro,invproba=InvPro)

    try:
        rep   =  sys.argv[1]
        year1 = int(sys.argv[2])
        year2 = int(sys.argv[3])
        GroupFile = sys.argv[4]
        nmax = int(sys.argv[5])
        GroupName = (GroupFile.split("/")[-1].split(".")[:-1])[0]
    except:
        print("Syntax: StatStructureDirectory year1 year2 group_file num_max_class")
        quit()

    #groups = {'NAN':None,'VRT':'OTH', 'XFE':'OTH','TRN':'SUM','MIS':'SUM'}

    # Create pdf directory
    os.makedirs(rep + "/pdf-%s"%(GroupName), exist_ok=True)
    os.makedirs(rep + "/csv-%s"%(GroupName), exist_ok=True)
    files = glob.glob(rep + "/npz/*.npz")
    GroupsDict = importlib.import_module(GroupName)
    groups = GroupsDict.AllToNew

    try:
        nan = sys.argv[6]
    except:
        groups['NAN'] = None

    for f in files:
        data = np.load(f)
        legend = data["legend"]
        surface = data["surface"]

        # Sum up grouped classes
        data = adaptToLegend(data,groups)

        # Desactivate parcel stat for simplicity with the raster approach
        #parcels = (data["parcels"])[:nmax,:nmax]

        legend = list(data["legend"])
        Cutlegend = list(data["legend"])[:nmax]

        surface       = data["surface"]
        Cutsurface    = data["surface"][:nmax,:nmax]

        condproba     = data["condproba"]
        Cutcondproba  = data["condproba"][:nmax,:nmax]

        invproba      = data["invproba"]
        Cutinvproba   = data["invproba"][:nmax,:nmax]

        # Desactivate parcel stat for simplicity with the raster approach
        #matList = [parcels,surface,condproba,invproba]
        #colormapList = ["rainbow","rainbow","white","white"] 
        #titles = ["Parcels","surface","Cond. Proba.","Inv. Proba."]

        
        pdfname = f.split("/")[-1].replace("StatStructure","Rotation-%s"%(GroupName))
        csvname = f.split("/")[-1].replace("StatStructure","Rotation-%s"%(GroupName))
        #NoNanSum = np.sum(surface[1:,1:])
        #pdfname = rep + "/pdf-%s/"%(GroupName) + pdfname.replace(".npz","-%dha.pdf"%(NoNanSum))
        pdfname = rep + "/pdf-%s/"%(GroupName) + pdfname.replace("npz","pdf",)
        csvname = rep + "/csv-%s/"%(GroupName) + csvname.replace("npz","csv")
        gentitle = pdfname.split("/")[-1].split(".")[0]

        matList = [Cutsurface,Cutcondproba,Cutinvproba]
        colormapList = ["rainbow","white","white"] 
        titles = ["%s -  Surface (ha)"%(gentitle),"%s - Probability of year N knowing year N-1 (%%)."%(gentitle),"%s - Probability of year N-1 knowing year N (%%)."%(gentitle)]

        # Export to pdf
        if(np.sum(Cutsurface)>0):
            log.msg("Exporting to %s file"%(pdfname),"INFO")
            exportNew(matList,colormapList,Cutlegend,pdfname,titles,year1,year2)

        # Export to csv 
        if(np.sum(surface)>0):
            log.msg("Exporting to %s file"%(csvname),"INFO")
            export_to_csv(csvname,surface,legend)

