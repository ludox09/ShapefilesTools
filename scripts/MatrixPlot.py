#!/usr/bin/python
# Update        - 29/08/2019
# Ludo - CesBIO - 29/08/2019
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LogNorm
from matplotlib import cm 
import matplotlib as mpl
import matplotlib.backends.backend_pdf as mpdf
from matplotlib.colors import LinearSegmentedColormap

whitemap = LinearSegmentedColormap.from_list('mycmap',['white','white']) 

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
            print val 
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


def export(matList,cmlist,classnames,filepdf,title,year1,year2):
    # Colormap
    filename = filepdf
    pdfplot = mpdf.PdfPages(filename)
 
    for k,mat in enumerate(matList):
        cmap = cmlist[k]
        if cmlist[k] == "white":
            cmap = whitemap 

	# Adapt values shape
        Nmat = len(mat)

        Sum1 = np.sum(mat, axis=1)
        Sum2 = np.sum(mat, axis=0)
        diag1 = np.diag(mat)
        diag2 = np.diag(mat)

        epsilon = 1e-10
        diff = 200.0*(Sum2 - Sum1)/(Sum1+Sum2 + epsilon)

        Sum1 = Sum1.reshape(1,-1).T
        diag1 = diag1.reshape(1,-1).T

        diag1 = 100.0*diag1/(Sum1+epsilon)
        diag2 = 100.0*diag2/(Sum2+epsilon)

        diag2 = [diag2]
        Sum2 = [Sum2]
        diff = [diff]

    

        # Initialize plot
	#plottitle = "%s - Averages Confusion Matrix - %s - %s"%(title,method,date)
	plottitle = "%s"%(title[k])
        fig = plt.figure(figsize=(40,41))
        fig.suptitle(plottitle, size = 40) 
        #grid = plt.GridSpec(4, 3, wspace=-0.14, hspace=-0.175, width_ratios=[31, 2, 2], height_ratios=[3, 1, 1, 1])
        grid = plt.GridSpec(4, 3, wspace=0, hspace=0, width_ratios=[30, 3, 2], height_ratios=[30, 3, 2, 2])
        
        # Add axes
        ax1 = fig.add_subplot(grid[0,0])
        ax2 = fig.add_subplot(grid[0,1])
        ax3 = fig.add_subplot(grid[1,0])
        ax4 = fig.add_subplot(grid[0,2])
        ax5 = fig.add_subplot(grid[2,0])
        ax6 = fig.add_subplot(grid[3,0])
       
        # Add titles
        #ax1.set_title("Overall Accuracy = %.2f +/- %.2f %%"%(OA,Int),size=20)
        lsize = (50 - Nmat)
        ax2.set_title("Sum %d"%(year1), fontsize = lsize)
        ax3.set_title("Sum %d"%(year2), fontsize = lsize)

        ax4.set_title("Mono. %d"%(year1), fontsize = lsize)
        ax5.set_title("Mono. %d"%(year2), fontsize = lsize)
        ax6.set_title("$(S_j^{%d} - S_i^{%d})$"%(year1,year2), fontsize = lsize)

        #ax4.set_title("FScore (%)")
        
        lin = np.arange(Nmat)
        linsup = np.arange(Nmat+1) + 0.5
        
        # Major ticks
        ax1.set_xticks(lin);
        ax1.set_yticks(lin);
        ax2.set_yticks(lin);
        ax3.set_xticks(lin);

        ax4.set_yticks(lin);
        ax5.set_xticks(lin);
        ax6.set_xticks(lin);
        
        # Minor ticks
        ax1.set_xticks(linsup, minor=True);
        ax1.set_yticks(linsup, minor=True);
        ax2.set_yticks(linsup, minor=True);
        ax3.set_xticks(linsup, minor=True);
        ax4.set_yticks(linsup, minor=True);
        ax5.set_xticks(linsup, minor=True);
        ax6.set_xticks(linsup, minor=True);

        # Labels for major ticks
        ax1.set_xticklabels([]);
        ax1.set_yticklabels([]);
        ax2.set_xticklabels([]);
        ax2.set_yticklabels([]);
        
        # Labels for minor ticks
        ax1.set_xticklabels(classnames, rotation=0, minor = True, size = lsize);
        ax1.set_yticklabels(classnames, minor = True, size = lsize);
        
        ax2.set_xticklabels([], minor = False);
        ax2.set_yticklabels([], minor = False);
        ax2.set_yticklabels(classnames, minor = True, size = lsize);

        ax3.set_xticklabels([], minor = False);
        ax3.set_yticklabels([], minor = False);
        ax3.set_xticklabels(classnames, rotation=0, minor = True, size = lsize);

        ax4.set_xticklabels([], minor = False);
        ax4.set_yticklabels([], minor = False);
        ax4.set_yticklabels(classnames, rotation=0, minor = True, size = lsize);

        ax5.set_xticklabels([], minor = False);
        ax5.set_yticklabels([], minor = False);
        ax5.set_xticklabels(classnames, rotation=0, minor = True, size = lsize);

        ax6.set_xticklabels([], minor = False);
        ax6.set_yticklabels([], minor = False);
        ax6.set_xticklabels(classnames, rotation=0, minor = True, size = lsize);


        #ax4.set_yticklabels(classnames, minor = True);
        
        # Gridlines based on minor ticks
        ax1.grid(which='major', linestyle = '-', color = 'black', linewidth=1.5)
        ax2.grid(which='major', linestyle = '-', axis = 'y', color = 'black')
        ax3.grid(which='major', linestyle = '-', axis = 'x', color= 'black')
        ax4.grid(which='major', linestyle = '-', axis = 'y', color = 'black')
        
        ax5.grid(which='major', linestyle = '-', axis = 'x', color= 'black')
        ax6.grid(which='major', linestyle = '-', axis = 'x', color= 'black')
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
            ax1.text(i+0.5,j+0.5,fval, color=fcolor, ha='center', va='center', rotation=45, size = nsize)

        pl1 = ax1.imshow(mat, extent = extentMat, interpolation='none', aspect='equal',cmap = cmap, norm=LogNorm(vmin=MinVal, vmax=MaxVal)) 

        for j in range(Nmat):
            fval,fcolor =  scientific(Sum1[j][0], cmap,MinVal, MaxVal)
            ax2.text(0.5,j+0.5,fval, color=fcolor, ha='center', va='center', rotation = 45, size = nsize)

        for j in range(Nmat):
            fval,fcolor =  scientific(diag1[j][0], cmap, 0,100)
            ax4.text(0.5,j+0.5,fval, color=fcolor, ha='center', va='center', rotation = 45, size = nsize)


        for i in range(Nmat):
            fval,fcolor =  scientific(Sum2[0][i], cmap, MinVal, MaxVal)
            ax3.text(i+0.5,0.5,fval, color=fcolor, ha='center', va='center', rotation =45, size = nsize)


        for i in range(Nmat):
            fval,fcolor =  scientific(diag2[0][i], cmap, 0, 100)
            ax5.text(i+0.5,0.5,fval, color=fcolor, ha='center', va='center', rotation =45, size = nsize)

        for i in range(Nmat):
            fval,fcolor =  scientific(diff[0][i], cmap, 0, 100)
            ax6.text(i+0.5,0.5,fval, color=fcolor, ha='center', va='center', rotation =45, size = nsize)




        
        ax2.imshow(Sum1, extent = extentCol, interpolation='none', aspect='equal', cmap = cmap, norm=LogNorm(vmin=MinVal, vmax=MaxVal))
        ax3.imshow(Sum2, extent = extentRow, interpolation='none', aspect='equal', cmap = cmap, norm=LogNorm(vmin=MinVal, vmax=MaxVal))
        ax4.imshow(diag1,  extent = extentCol, interpolation='none', aspect='equal', cmap = cmap)
       
        ax5.imshow(diag2, extent = extentRow, interpolation='none', aspect='equal', cmap = cmap)
        ax6.imshow(diff, extent = extentRow, interpolation='none', aspect='equal', cmap = cmap)

 
        #fig.colorbar(pl1, ax = ax1, fraction=0.046, pad=0.04)
        #pdfplot.savefig(fig,bbox_inches='tight')
        pdfplot.savefig(fig)
    pdfplot.close()   

def exportNew(matList,cmlist,classnames,filepdf,title):
    # Colormap
    filename = filepdf
    pdfplot = mpdf.PdfPages(filename)

    classnamesX = classnames
    classnamesY = classnames
 
    for k,mat in enumerate(matList):
        cmap = cmlist[k]
        if cmlist[k] == "white":
            cmap = whitemap 

	# Adapt values shape
        Nmat = len(mat)

        Sum1 = np.sum(mat, axis=1)
        Sum2 = np.sum(mat, axis=0)
        diag1 = np.diag(mat)
        diag2 = np.diag(mat)

        epsilon = 1e-10
        diff = 200.0*(Sum2 - Sum1)/(Sum1+Sum2 + epsilon)

        Sum1 = Sum1.reshape(1,-1).T
        diag1 = diag1.reshape(1,-1).T

        diag1 = 100.0*diag1/(Sum1+epsilon)
        diag2 = 100.0*diag2/(Sum2+epsilon)

        diag2 = [diag2]
        Sum2 = [Sum2]
        diff = [diff]

    

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
        ax1.grid(which='major', linestyle = '-', color = 'black', linewidth=1.5)
        
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
            ax1.text(i+0.5,j+0.5,fval, color=fcolor, ha='center', va='center', rotation=45, size = nsize)

        pl1 = ax1.imshow(mat, extent = extentMat, interpolation='none', aspect='equal',cmap = cmap, norm=LogNorm(vmin=MinVal, vmax=MaxVal)) 

        #fig.colorbar(pl1, ax = ax1, fraction=0.046, pad=0.04)
        #pdfplot.savefig(fig,bbox_inches='tight')
        pdfplot.savefig(fig)
    pdfplot.close()   



#plt.tight_layout()
