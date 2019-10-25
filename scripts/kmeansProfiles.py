#!/usr/bin/python
#    Python 2.7   #
# Ludo 2019-10-24 #

import os,sys
import numpy as np
import pandas as pd
from datetime import datetime
import locale
from scipy.cluster.vq import vq,kmeans2,whiten
import matplotlib.pyplot as plt
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

# construct crop mapping
rpgClasses = param.rpgClasses
derobesClasses = param.derobesClasses
rpg2code = {c:(i+1) for i,c in enumerate(rpgClasses)}
code2rpg = {(i+1):c for i,c in enumerate(rpgClasses)}
der2code = {c:(i+1) for i,c in enumerate(derobesClasses)}
code2der = {(i+1):c for i,c in enumerate(derobesClasses)}

# Get inout parameters
tclass       = sys.argv[1]
nclass       = int(sys.argv[2])       
profilesfile = sys.argv[3]
datefile     = sys.argv[4]
dstart       = int(sys.argv[5])
dend         = int(sys.argv[6])


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
days = [(d - dt[0]).days for d in dt]

log.msg("Load profiles files")
profiles = pd.read_pickle(profilesfile)

# Construct filtering colums
columns  = list(profiles.columns)
TableCol = columns[:6]  
StatsCol = columns[6:]
MeanCol = StatsCol[::2]
StdvCol = StatsCol[1::2]
[par,c1,c2,d1,d2,npix] = TableCol

# log
log.msg("KMeans computed for the class %s = %s between the %s and the %s"%(c2,tclass,doy[dstart],doy[dend]))

# Filter given class
log.msg("Filter to class %s = %s"%(c2,tclass))

# Select specific time period
MeanColPeriod = MeanCol[dstart:dend]
StdvColPeriod = StdvCol[dstart:dend]
log.msg(MeanColPeriod,"DEBUG")
log.msg(StdvColPeriod,"DEBUG")

### DATASET CONSTRUCTION #####################################################
# Only table
AllTable = profiles[TableCol]

# Only table for specific class
ClassTable = AllTable[AllTable[c2] == rpg2code[tclass]]

# Only profiles for specific class with all date
AllMeanProfiles = profiles[profiles[c2] == rpg2code[tclass]][MeanCol]
AllStdvProfiles = profiles[profiles[c2] == rpg2code[tclass]][StdvCol]

# Only profiles for specific class and specific period  = kmeans Features
PerMeanProfiles = profiles[profiles[c2] == rpg2code[tclass]][MeanColPeriod]
PerStdvProfiles = profiles[profiles[c2] == rpg2code[tclass]][StdvColPeriod]

##############################################################################

features = PerMeanProfiles.values
print features.shape

log.msg("whitening of features")
whitened = whiten(features)

log.msg("Executing KMeans with %d classes"%(nclass))
codebook, labels = kmeans2(whitened,nclass)
print codebook.shape
print labels.shape

# Sort profiles according to kmeans
log.msg("Sort profiles according to kmeans classes")

# Add kmeans class to profiles
KmeansMean = AllMeanProfiles
KmeansMean['kmeans'] = labels

#print KmeansMean.values.shape
#print KmeansMean[KmeansMean['kmeans'] == 0 ][MeanCol].mean().values
#print KmeansMean[KmeansMean['kmeans'] == 1 ][MeanCol].mean().values
#print KmeansMean[KmeansMean['kmeans'] == 2 ][MeanCol].mean().values
#print KmeansMean[KmeansMean['kmeans'] == 3 ][MeanCol].mean().values

plt.figure(figsize=(20,10))
plt.title("k-meams of the class %s with %d clusters (%s %s)"%(tclass,nclass,"2018","T31TJC"))
ax1 = plt.subplot(1,1,1)
ax1.set_xticks(days)
ax1.set_xticklabels(doy,rotation = 90,fontsize = 12)
ax1.set_xlabel('DOY', fontsize = 10)
ax1.set_ylabel('<NDVI>', fontsize = 10)
period_col = 'g'
ax1.axvspan(days[dstart], days[dend], alpha=0.2, color =period_col)
ax1.text(days[dstart]+ 0.2, 0.95, "k-means period", fontsize = 20, color = period_col)
# Plot centroid
#for i,c in enumerate(codebook*np.std(features, 0)):
#    ax1.plot(days[dstart:dend],c,label = "Class %d"%(i+1))


ntotal = len(KmeansMean[MeanCol].values)

log.msg("Save profiles")
for l in range(nclass):
    print "Label = ",l
    #print table.astype(int)
    #capsize=2,lw=0.5,ls=?
    profs      = KmeansMean[KmeansMean['kmeans'] == l ][MeanCol]
    num = len(profs)
    print num
    MeanMean = profs.mean().values
    StdvMean = profs.std().values
    ErrMean = profs.std().values/np.sqrt(num)
    axp = ax1.errorbar(days,MeanMean,ErrMean,label = "Cluster %d (%d/%d)"%(l,num,ntotal), lw = 1.5)
    col = axp[0].get_color()
    ax1.fill_between(days, MeanMean - StdvMean, MeanMean + StdvMean, color = col, alpha = 0.1)

#ax1.legend(bbox_to_anchor=(1.33, 1))
plt.legend(bbox_to_anchor=(1.04,1), loc="upper left")
plt.savefig("kmeans_%s_%d.png"%(tclass,nclass),bbox_inches='tight')


log.msg("Save histogram")
data = KmeansMean[KmeansMean['kmeans'] == 2 ]["mean_ndvi_30"].values
print data
plt.figure(figsize=(20,10))
#plt.hist(data, 30, density=True, facecolor='g', alpha=0.75)
plt.hist(data, 30, facecolor='g', alpha=0.75)
plt.savefig("histogram_%s_%d.png"%(tclass,nclass),bbox_inches='tight')



log.msg("Done")
