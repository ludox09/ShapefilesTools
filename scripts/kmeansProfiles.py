#!/usr/local/ANACONDA-PY34-v510/bin/python
#    Python 2.7   #
# Ludo 2019-10-24 #

import os,sys

from datetime import datetime
import locale

import numpy as np
import pandas as pd
import collections

from scipy.cluster.vq import vq,kmeans2,whiten

import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.widgets import Slider

import infolog
import parameters as param


def inverse_mapping(f):
        return dict(zip(f.values(), f.keys()))

def formatTable(table):
    table = table.astype(int)
    if(table[3] == 0 and table[4] == 0):
        NewTable = [table[0],code2rpg[table[1]],code2rpg[table[2]],table[5]]
    else:
        NewTable = [table[0],code2rpg[table[1]],code2rpg[table[2]],code2der[table[3]],code2der[table[4]],table[5]]
    return NewTable

# Initialisation
log = infolog.infolog()
width = 0.1

# construct crop mapping
rpgClasses = param.rpgClasses
derobesClasses = param.derobesClasses
rpg2code = {c:(i+1) for i,c in enumerate(rpgClasses)}
code2rpg = {(i+1):c for i,c in enumerate(rpgClasses)}
der2code = {c:(i+1) for i,c in enumerate(derobesClasses)}
code2der = {(i+1):c for i,c in enumerate(derobesClasses)}

# Get inout parameters
try:
    profilesfile = sys.argv[1]
except:
    log.msg("Error syntax:","ERROR")
    log.msg("Syntax: kmeansProfiles.py profilesFile datesFile NbKmeansClasses (classTag1) classTag2","ERROR")
    quit()
datefile     = sys.argv[2]
nclass       = int(sys.argv[3])       
tclass2      = sys.argv[4]
try:
    tclass1       = sys.argv[4]
    tclass2       = sys.argv[5]
    mono = False
except:
    mono = True

# External param
# TODO: Get formated fashion
#tclass = 50 # Sunflower TRN
#tclass = 'MIS' # Maiz MIS
#tclass = 3  # Ble BDH
#tclass = 'CZH'  # Colza CZH

# Manage dates
dates = np.loadtxt(datefile)
locale.setlocale(locale.LC_TIME, "en_US")
dt  = [datetime.strptime(str(int(d)), '%Y%m%d') for d in dates]
doy = [d.strftime('%d-%b') for d in dt]
days = np.array([(d - dt[0]).days for d in dt])

dstart = 0
dend = len(days) - 1

log.msg("Load profiles files")
profiles = pd.read_pickle(profilesfile)

# Count classes


columns  = list(profiles.columns)
ListClassesCol1  = columns[1:2] 
ListClassesCol2 = columns[2:3] 
print(ListClassesCol1)
print(ListClassesCol2)
ListClasses1 = np.unique(profiles[ListClassesCol1].values)
ListClasses2 = np.unique(profiles[ListClassesCol2].values)

NameClasses1 = [code2rpg[x]  for x in ListClasses1]
NameClasses2 = [code2rpg[x]  for x in ListClasses2]


#print(ListClasses1)
#print(ListClasses2)
#print("")
#print(NameClasses1)
#print(NameClasses2)

# Construct filtering colums
TableCol = columns[:6]  
StatsCol = columns[6:]

MeanCol = [s for s in StatsCol if "mean_ndvi" in s]
StdvCol = [s for s in StatsCol if "stdv_ndvi" in s]
SoilCol = [s for s in StatsCol if "soil" in s]
[par,c1,c2,d1,d2,npix] = TableCol

# log
#log.msg("KMeans computed for the class %s = %s between the %s and the %s"%(c2,tclass2,doy[dstart],doy[dend]))

# Filter given class

# Select specific time period
MeanColPeriod = MeanCol[dstart:dend]
StdvColPeriod = StdvCol[dstart:dend]
log.msg(MeanColPeriod,"DEBUG")
log.msg(StdvColPeriod,"DEBUG")


if(mono):
  ### DATASET CONSTRUCTION #####################################################
  # Only table
  AllTable = profiles[TableCol]
  
  # Only table for specific class
  
  ClassTable = AllTable[AllTable[c2] == rpg2code[tclass2]]
  ###ClassTable = ClassTable[ClassTable[c1] == rpg2code["BTH"]] ##### ATTENTION
  
  
  # Only profiles for specific class with all date
  AllSoil = profiles[profiles[c2] == rpg2code[tclass2]][SoilCol]
  AllMeanProfiles = profiles[profiles[c2] == rpg2code[tclass2]][MeanCol]
  ###AllMeanProfiles = profiles[profiles[c2] == rpg2code[tclass2]]
  ###AllMeanProfiles = AllMeanProfiles[AllMeanProfiles[c1] == rpg2code["BTH"]][MeanCol]  ##### ATTENTION
  AllStdvProfiles = profiles[profiles[c2] == rpg2code[tclass2]][StdvCol]
  
  # Only profiles for specific class and specific period  = kmeans Features
  PerMeanProfiles = profiles[profiles[c2] == rpg2code[tclass2]][MeanColPeriod]
  ### PerMeanProfiles = profiles[profiles[c2] == rpg2code[tclass2]]
  ### PerMeanProfiles = PerMeanProfiles[PerMeanProfiles[c1] == rpg2code["BTH"]][MeanColPeriod]
  PerStdvProfiles = profiles[profiles[c2] == rpg2code[tclass2]][StdvColPeriod]
else:
  # Only table
  AllTable = profiles[TableCol]
  
  ClassTable = AllTable[(AllTable[c1] == rpg2code[tclass1]) & (AllTable[c2] == rpg2code[tclass2])] 
  ###ClassTable = ClassTable[ClassTable[c1] == rpg2code["BTH"]] ##### ATTENTION
  

  # Only profiles for specific class with all date
  AllSoil = profiles[(AllTable[c1] == rpg2code[tclass1]) & (AllTable[c2] == rpg2code[tclass2])][SoilCol]
  AllMeanProfiles = profiles[(AllTable[c1] == rpg2code[tclass1]) & (AllTable[c2] == rpg2code[tclass2])][MeanCol]
  ###AllMeanProfiles = profiles[profiles[c2] == rpg2code[tclass]]
  ###AllMeanProfiles = AllMeanProfiles[AllMeanProfiles[c1] == rpg2code["BTH"]][MeanCol]  ##### ATTENTION
  AllStdvProfiles = profiles[(AllTable[c1] == rpg2code[tclass1]) & (AllTable[c2] == rpg2code[tclass2])][StdvCol]
  
  # Only profiles for specific class and specific period  = kmeans Features
  PerMeanProfiles = profiles[(AllTable[c1] == rpg2code[tclass1]) & (AllTable[c2] == rpg2code[tclass2])][MeanColPeriod]
  ### PerMeanProfiles = profiles[profiles[c2] == rpg2code[tclass]]
  ### PerMeanProfiles = PerMeanProfiles[PerMeanProfiles[c1] == rpg2code["BTH"]][MeanColPeriod]
  PerStdvProfiles = profiles[(AllTable[c1] == rpg2code[tclass1]) & (AllTable[c2] == rpg2code[tclass2])][StdvColPeriod]

##############################################################################

features = PerMeanProfiles.values
#print(features.shape)

log.msg("whitening of features")
whitened = whiten(features)

log.msg("Executing KMeans with %d classes"%(nclass))
codebook, labels = kmeans2(whitened,nclass)
#print(codebook.shape)
#print(labels.shape)

# Sort profiles according to kmeans
log.msg("Sort profiles according to kmeans classes")

# Add kmeans class to profiles
klim = 4
KmeansMean = AllMeanProfiles
KmeansMean['kmeans'] = labels
KmeansTable = ClassTable
KmeansTable['kmeans'] = labels
KmeansPrevious = KmeansTable[[c1,"kmeans"]].values

KmeansMatrix = [ KmeansPrevious[KmeansPrevious[:,1] == i][:,0] for i in range(nclass)]

KmeansCounter = []
for i in range(nclass):
    counter = collections.Counter(KmeansMatrix[i])
    counterList = [ [w, counter[w]] for w in sorted(counter, key=counter.get, reverse=True)]
    KmeansCounter.append(counterList[:klim])

KmeansCounter = np.array(KmeansCounter)
key = KmeansCounter[:,:,0]
val = KmeansCounter[:,:,1]

# Kmeans soil
slim = 4
KmeansSoil = AllSoil
KmeansSoil['kmeans'] = labels
npKmeansSoil = KmeansSoil.values

MeansSoil = []
print(npKmeansSoil,npKmeansSoil.shape)
for i in range(nclass):
    MeansSoil.append(np.mean(npKmeansSoil[npKmeansSoil[:,-1] == i][:,:-1],axis=0))

print(SoilCol)
for x in MeansSoil:
    print(x.astype(np.int))
    print(SoilCol[np.argmax(x)][5:])



quit()


#print KmeansMean.values.shape
#print KmeansMean[KmeansMean['kmeans'] == 0 ][MeanCol].mean().values
#print KmeansMean[KmeansMean['kmeans'] == 1 ][MeanCol].mean().values
#print KmeansMean[KmeansMean['kmeans'] == 2 ][MeanCol].mean().values
#print KmeansMean[KmeansMean['kmeans'] == 3 ][MeanCol].mean().values


# Graphical output

fig = plt.figure(figsize=(20,10),num='kmeansProfiles')
#fig.patch.set_facecolor('#222222')
# Grid
gs = gridspec.GridSpec(3, 3) 
ax1 = plt.subplot(gs[:,0:2])
#ax1.set_facecolor("#000000")
if mono:
    ax1.set_title("k-meams of the class %s with %d clusters (%s %s)"%(tclass2,nclass,"2018","T31TJC"))
else:
    ax1.set_title("k-meams of the classes %s/%s with %d clusters (%s %s)"%(tclass1,tclass2,nclass,"2018","T31TJC"))
ax1.set_xticks(days)
ax1.set_xticklabels(doy,rotation = 90,fontsize = 8)
ax1.set_xlabel('DOY', fontsize = 10)
ax1.set_ylabel('<NDVI>', fontsize = 10)
ax1.set_ylim([0,1])
period_col = 'g'
zone = ax1.axvspan(days[dstart], days[dend], alpha=0.2, color = period_col)
changezone = ax1.axhspan(0, 0.02, alpha=0.1, color = 'k')
zonetext = ax1.text(days[dstart]+ 0.5, 0.97, "k-means period", fontsize = 10, color = period_col)

ax2 = plt.subplot(gs[1,2])
#ax2.set_facecolor("#CCCCCC")
ax2.set_title("Profiles distributions on the %s"%(doy[0]))


#ax2.set_xticks(days)
#ax2.set_xticklabels(doy,rotation = 90,fontsize = 12)
ax2.set_xlabel('<NDVI>', fontsize = 10)
ax2.set_xlabel('P(<NDVI>)', fontsize = 10)


ax3 = plt.subplot(gs[2,2])
#ax3.set_facecolor((0, 0, 0))
#ax3.set_xticklabels(doy,rotation = 90,fontsize = 12)
#ax3.set_xlabel('x', fontsize = 10)
ax3.set_xticks(range(nclass))
ax3.set_xlabel('Previous year class', fontsize = 10)
ax3.set_xlim([-0.5, nclass])


interrstClass = ["BTH","MIS","OTH"] 


#axcolor = 'lightgoldenrodyellow'
#axStart = plt.axes([0.125, 0.910, 0.501, 0.02], facecolor=axcolor) # x0,y0,wx,wy
#axEnd   = plt.axes([0.125, 0.885, 0.501, 0.02],  facecolor=axcolor)
#
#sStart = Slider(axStart, 'Start', 0, len(days)-1, valinit=len(days)/10, valstep=1,valfmt="%i")
#sEnd = Slider(axEnd, 'End', 0, len(days)-1, valinit=len(days)/5,valfmt="%i")

# Plot centroid
#for i,c in enumerate(codebook*np.std(features, 0)):
#    ax1.plot(days[dstart:dend],c,label = "Class %d"%(i+1))


ntotal = len(KmeansMean[MeanCol].values)

nbin = 40
log.msg("Save profiles")
meanList  = [None]*nclass
pickList  = [None]*nclass
for l in range(nclass):
    #print table.astype(int)
    #capsize=2,lw=0.5,ls=?
    profs      = KmeansMean[KmeansMean['kmeans'] == l ][MeanCol]
    num = len(profs)

    # TO DO in mportant
    #npprof = profs.values
    #print("ttt:",npprof.shape)
    #HistogramMean = np.histogram(npprof,np.arange(0,10,1.0/float(nbin)))
    #hvalues =  HistogramMean[0]
    #xvalues =  HistogramMean[1]
    #PickMean = HistogramMean[1][np.argmax(HistogramMean[0])]
    
    MeanMean = profs.mean().values
    StdvMean = profs.std().values
    ErrMean = profs.std().values/np.sqrt(num)

    meanList[l] = ax1.plot(days,MeanMean, label = "Cluster %d [%d/%d][%d%%]"%(l,num,ntotal,100*num/ntotal), lw = 1.5, ls = "--")
    col = meanList[l][0].get_color()
    #pickList[l] = ax1.plot(days,PickMean,col, lw = 1.5)
    #fillList[l] = ax1.fill_between(days, MeanMean - StdvMean, MeanMean + StdvMean, color = col, alpha = 0.1)
     

ax1.legend(bbox_to_anchor=(1.04,1), loc="upper left", facecolor='white')

#plt.savefig("kmeans_%s_%d.png"%(tclass,nclass),bbox_inches='tight')

colList = []
dline = ax1.axvline(days[dstart], ymin=0, ymax=1, color  = "k", alpha = 0.5, lw = 0.5)
for l in range(nclass):
    data = KmeansMean[KmeansMean['kmeans'] == l ]["mean_ndvi_%d"%(dstart)].values
    col = meanList[l][0].get_color()
    colList.append(col)
    ax2.hist(data, nbin, alpha=0.20, color = col)
    ax2.axvline(np.mean(data), ymin=0, ymax=100, color  = col, alpha = 0.5, lw = 0.5)

barsPrevious = ax3.bar(range(nclass), val[:,0], width, color = colList, edgecolor = 'k')
barsSoil     = ax3.bar(np.array(range(nclass)) + 0.1, val[:,0], width, color = colList, edgecolor = 'k', alpha = 0.5)
for i in range(1,klim):
    try:
        barsPrevious = barsPrevious + ax3.bar(range(nclass), val[:,i] , width, np.sum(val[:,:i],axis=1), color = colList, edgecolor = 'k')
    except:
        pass

for i in range(1,slim):
    try:
        barsSoil = barsPrevious + ax3.bar(np.array(range(nclass)) + 0.1, val[:,i] , width, np.sum(val[:,:i],axis=1), color = colList, edgecolor = 'k', alpha = 0.5)
    except:
        pass




for x in range(nclass):
    for y,(k,v) in enumerate(zip(key[x],val[x])):
        ax3.text(x + 0.15, 100*y, "%s %d"%(code2rpg[int(k)],v) , fontsize = 8)
                




#annot = ax3.annotate("", xy=(0,0), xytext=(0,120),textcoords="offset points",bbox=dict(boxstyle="round", fc="black", ec="b", lw=1))
#annot.set_visible(False)


#ax3.bar([0,1,2,3], [4,3,9], width, [0,4,3+4], label = "test",color = "r")
#ax3.bar([0,1,2,3], [4,3,9], width, [0,4,3+4], label = "test",color = "r")
#ax3.legend(bbox_to_anchor=(1.04,1), loc="upper left")


 

#for d in range(0,64,6):
#    data = KmeansMean[KmeansMean['kmeans'] == 2 ]["mean_ndvi_%d"%(d)].values
#    ax3.hist(data, 40, alpha=0.10)

def update(val):
    _ndarray = zone.get_xy()
    x0 = _ndarray[0,0]
    x1 = _ndarray[2,0]
    # Update according to sliders 
    x0 = days[int(sStart.val)]
    x1 = days[int(sEnd.val)]
    _ndarray[:, 0] = [x0, x0, x1, x1, x0]
    zone.set_xy(_ndarray)
    if (x0 > x1):
        zone.set_color('r')
    else:
        zone.set_color('g')
    fig.canvas.draw_idle()


def pickXY(event,days):
    """ pick x y and rescale to days """

    # Update according to sliders 
    [xcurrent,ycurrent]  = [int(event.xdata),int(event.ydata)]
    if(event.button == 1):
        x0 = xcurrent  
        y0 = ycurrent  
        x1 = dend
        y1 = 0  

    elif(event.button == 3):
        x0 = dstart  
        y0 = 0  
        x1 = xcurrent
        y1 = xcurrent

    # Adjus x0 and x1 to grid and get dstart and dend

    x0 = np.argmin(np.abs(days - x0))
    x1 = np.argmin(np.abs(days - x1))

    return [x0,y0,x1,y1]



def updateZone(zone,event,days):
    """ Update kmeans zone """
    ndarray = zone.get_xy()
    x0 = ndarray[0,0]
    x1 = ndarray[2,0]

    # Update according to sliders 
    xcurrent  = int(event.xdata)
    if(event.button == 1):
        x0 = xcurrent  
    
    elif(event.button == 3):
        x1 = xcurrent
    
    # Adjus x0 and x1 to grid and get dstart and dend
    dstart = np.argmin(np.abs(days-x0))
    dend  = np.argmin(np.abs(days- x1))

    x0 = days[dstart]
    x1 = days[dend]

    if (x0>x1):
        temp = x0
        x0 = x1
        x1 = temp

    if x0 < days[0]:x0 = days[0]
    if x1 < days[0]:x1 = days[0]
    if x0 > days[-1]:x0 = days[-1]
    if x1 < days[0]:x1 = days[-1]

    ndarray[:, 0] = [x0, x0, x1, x1, x0]
    if (x0 > x1):
        zone.set_color('r')
        zonetext.set_color('r')
        zonetext.set_x(x1 + 0.5)
    else:
        zone.set_color('g')
        zonetext.set_color('g')
        zonetext.set_x(x0 + 0.5)

    zone.set_xy(ndarray)
    return dstart,dend 

def onclick(event):
    global KmeansMean
    # Update kmeans temporal zone
    if event.inaxes == ax1:
        if(0.0 < event.ydata and event.ydata < 0.02):
            try:
                dstart,dend = updateZone(zone,event,days)

                MeanColPeriod = MeanCol[dstart:dend]
                StdvColPeriod = StdvCol[dstart:dend]
                
                if(mono):
                    PerMeanProfiles = profiles[AllTable[c2] == rpg2code[tclass2]][MeanColPeriod]
                    PerStdvProfiles = profiles[AllTable[c2] == rpg2code[tclass2]][StdvColPeriod]
                else:
                    PerMeanProfiles = profiles[(AllTable[c1] == rpg2code[tclass1]) & (AllTable[c2] == rpg2code[tclass2])][MeanColPeriod]
                    PerStdvProfiles = profiles[(AllTable[c1] == rpg2code[tclass1]) & (AllTable[c2] == rpg2code[tclass2])][StdvColPeriod]

            
                ## pdate k-means
                features = PerMeanProfiles.values
                whitened = whiten(features)
                codebook, labels = kmeans2(whitened,nclass)
            
                ## Add kmeans class to profiles
                KmeansMean = AllMeanProfiles
                print("ICI",labels)
                KmeansMean['kmeans'] = labels
                ntotal = len(KmeansMean[MeanCol].values)
            
                for l in range(nclass):
                    profs = KmeansMean[KmeansMean['kmeans'] == l ][MeanCol]
                    num = len(profs)
                    MeanMean = profs.mean().values
                    StdvMean = profs.std().values
                    ErrMean = profs.std().values/np.sqrt(num)
            
                    meanList[l][0].set_data(days,MeanMean)
                    col = meanList[l][0].get_color()
                    meanList[l][0].set_label("Cluster %d [%d/%d][%d%%]"%(l,num,ntotal,100*num/ntotal))
                    #pickList[l][0].set_data(days,0.65*MeanMean,col)
                    #ax1.errorbar(days,MeanMean,ErrMean,label = "Cluster %d (%d/%d)"%(l,num,ntotal), lw = 1.5)
                    #fillList[l] = ax1.fill_between(days, MeanMean - StdvMean, MeanMean + StdvMean, color = col, alpha = 0.1)
                    #fillList[l][0].set_data(days,MeanMean-StdvMean)

                ax1.legend(bbox_to_anchor=(1.04,1), loc="upper left")


                KmeansTable = ClassTable
                KmeansTable['kmeans'] = labels
                KmeansPrevious = KmeansTable[[c1,"kmeans"]].values
                
                KmeansMatrix = [ KmeansPrevious[KmeansPrevious[:,1] == i][:,0] for i in range(nclass)]
                
                KmeansCounter = []
                for i in range(nclass):
                    counter = collections.Counter(KmeansMatrix[i])
                    counterList = [ [w, counter[w]] for w in sorted(counter, key=counter.get, reverse=True)]
                    KmeansCounter.append(counterList[:klim])
                
                KmeansCounter = np.array(KmeansCounter)
                key = KmeansCounter[:,:,0]
                val = KmeansCounter[:,:,1]

                ax3.cla()
                ax3.set_xlim([-0.5, nclass])
                ax3.set_xticks(range(nclass))
                ax3.set_xlabel('Previous year class', fontsize = 10)

                barsPrevious = ax3.bar(range(nclass), val[:,0], width, label = "test", color = colList, edgecolor = 'k')
                for i in range(1,klim):
                    try:
                        barsPrevious = bars + ax3.bar(range(nclass), val[:,i] , width, np.sum(val[:,:i],axis=1), color = colList, edgecolor = 'k')
                    except:
                        pass

                for x in range(nclass):
                    for y,(k,v) in enumerate(zip(key[x],val[x])):
                        ax3.text(x + 0.15, 100*y, "%s %d"%(code2rpg[int(k)],v) , fontsize = 8)
                

                #annot = ax3.annotate("", xy=(0,0), xytext=(0,120),textcoords="offset points",bbox=dict(boxstyle="round", fc="black", ec="b", lw=2))

                fig.canvas.draw_idle()
            except:
                raise

        else:
           try:
               # Deal with profile histograms
               x0,y0,x1,y1 =  pickXY(event,days)
               dline.set_xdata(days[x0])
               ax2.cla()
               ax2.set_title("Profiles distributions on the %s"%(doy[x0]))
               for l in range(nclass):
                   data = KmeansMean[KmeansMean['kmeans'] == l ]["mean_ndvi_%d"%(x0)].values
                   col = meanList[l][0].get_color()
                   ax2.hist(data, nbin, alpha=0.20, color = col)
                   ax2.axvline(np.mean(data), ymin=0, ymax=100, color  = col, alpha = 0.5, lw = 0.5)
               fig.canvas.draw_idle()
           except:
               raise


#sStart.on_changed(update)
#sEnd.on_changed(update)
fig.canvas.mpl_connect('button_press_event', onclick)
#plt.tight_layout()
plt.show()
#plt.savefig("histogram_%s_%d.png"%(tclass,nclass),bbox_inches='tight')

log.msg("Done")
