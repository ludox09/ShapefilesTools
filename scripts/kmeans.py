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
profilesfile = sys.argv[1]
datefile     = sys.argv[2]

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
print TableCol
quit()
StatsCol = columns[6:]
MeanCol = StatsCol[::2]
StdvCol = StatsCol[1::2]

[par,c1,c2,d1,d2,npix] = StatsCol

# TODO: Get formated fashion
#tclass = 50 # Sunflower TRN
#tclass = 11 # Maiz MIS
#tclass = 3  # Ble BDH
tclass = 'CHZ'  # Colza CZH

# Select specific time period
if(False):
    MeanColPeriod = MeanCol[dstart:dend]
    StdvColPeriod = StdvCol[dstart:dend]
    log.msg(MeanColPeriod)
    log.msg(StdvColPeriod)

    AllTable = profiles[TableCol]
    AllMeanProfiles = profiles[MeanColPeriod]
    AllStdvProfiles = profiles[StdvColPeriod]
else:
    AllMeanProfiles = profiles[MeanCol]
    AllStdvProfiles = profiles[StdvCol]


plt.figure()
ax1 = plt.subplot(1,1,1)
ax1.set_xticks(days)
ax1.set_xticklabels(doy,rotation = 90,fontsize = 8)

for i in range(10):
    prof = AllMeanProfiles.values[i]
    #print prof
    t = range(len(prof))
    ax1.plot(days,prof)
plt.savefig("plot_%s.png"%(tclass))



log.msg("Done")
