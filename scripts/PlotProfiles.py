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
dstart = 0
dend   = 10

# construct crop mapping
rpgClasses = param.rpgClasses
derobesClasses = param.derobesClasses
rpg2code = {c:(i+1) for i,c in enumerate(rpgClasses)}
code2rpg = {(i+1):c for i,c in enumerate(rpgClasses)}
der2code = {c:(i+1) for i,c in enumerate(derobesClasses)}
code2der = {(i+1):c for i,c in enumerate(derobesClasses)}

# Get inout parameters
tclass =       sys.argv[1]
profilesfile = sys.argv[2]
datefile     = sys.argv[3]

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


# Filter given class
log.msg("filter to class %s = %s"%(c2,tclass))
AllTable = profiles[TableCol]
ClassTable = AllTable[AllTable[c2] == rpg2code[tclass]]

# Select specific time period
if(False):
    MeanColPeriod = MeanCol[dstart:dend]
    StdvColPeriod = StdvCol[dstart:dend]
    log.msg(MeanColPeriod)
    log.msg(StdvColPeriod)

    AllMeanProfiles = profiles[profiles[c2] == rpg2code[tclass]][MeanColPeriod]
    AllStdvProfiles = profiles[profiles[c2] == rpg2code[tclass]][StdvColPeriod]
else:
    AllMeanProfiles = profiles[profiles[c2] == rpg2code[tclass]][MeanCol]
    AllStdvProfiles = profiles[profiles[c2] == rpg2code[tclass]][StdvCol]

plt.figure(figsize=(20,10))
ax1 = plt.subplot(1,1,1)
ax1.set_xticks(days)
ax1.set_xticklabels(doy,rotation = 90,fontsize = 12)
ax1.set_xlabel('DOY', fontsize = 10)
ax1.set_ylabel('<NDVI>', fontsize = 10)

for i in range(10):
    prof = AllMeanProfiles.values[i]
    err = AllStdvProfiles.values[i]
    table = ClassTable.values[i]
    print table.astype(int)
    #capsize=2,lw=0.5,ls=?
    ax1.errorbar(days,prof,err,label = formatTable(table))

#ax1.legend(bbox_to_anchor=(1.33, 1))
plt.legend(bbox_to_anchor=(1.04,1), loc="upper left")
plt.savefig("plot_%s.png"%(tclass),bbox_inches='tight')

log.msg("Done")
