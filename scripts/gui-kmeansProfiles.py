#!/usr/local/ANACONDA-PY34-v510/bin/python
#############################################
# Profile Viever - En cours de developement #
#       Ludovic Arnaud - CesBIO (2019)      #
#           larnaudl@cesbio.cnes.fr         #
#           Creation:    20/02/19           #
#           Last update: 22/02/19           #
#############################################

from __future__ import unicode_literals
import sys
import os
from datetime import datetime
import locale

import random
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import gridspec
from numpy import arange, sin, pi
import numpy as np
import pandas as pd
import collections
from scipy.cluster.vq import vq,kmeans2,whiten

# Make sure that we are using QT5
matplotlib.use('Qt5Agg')
from PyQt5 import QtGui,QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QLabel, QPushButton, QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog,QTableWidget,QTableWidgetItem,QColorDialog,QCheckBox,QListWidget,QListWidgetItem,QPlainTextEdit,QDialog,QComboBox
from PyQt5.QtGui import QIcon, QColor,QCursor
from PyQt5.QtCore import QDate, QTime, QDateTime, Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import parameters as param


progname = os.path.basename(sys.argv[0])
progversion = "0.2"

rpgClasses = param.rpgClasses
derobesClasses = param.derobesClasses
rpg2code = {c:(i+1) for i,c in enumerate(rpgClasses)}
code2rpg = {(i+1):c for i,c in enumerate(rpgClasses)}
der2code = {c:(i+1) for i,c in enumerate(derobesClasses)}
code2der = {(i+1):c for i,c in enumerate(derobesClasses)}

class MyMplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=20, height=10, dpi=100):
        #self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig = plt.figure(figsize=(20,10),num='kmeansProfiles')
        gs = gridspec.GridSpec(3, 3) 
        self.ax1 = plt.subplot(gs[:,0:2])
        self.ax2 = plt.subplot(gs[1,2])
        self.ax3 = plt.subplot(gs[2,2])

        self.compute_initial_figure()
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        #self.fig.canvas.mpl_connect('button_press_event', onclick)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass
        #t = np.arange(0.0, 3.0, 0.01)
        #s1 = np.sin(2*np.pi*t)
        #s2 = np.sin(2*np.pi*t)*np.exp(-0.1*t)
        #self.ax1.plot(t, s1,'r')
        #self.ax2.plot(t, s2,'b')
        #self.ax1.set_ylim([-1,1])
        #self.ax2.set_ylim([-1,1])

class PrintConsole(QDialog):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        #self.message = ""
        self.text = QPlainTextEdit(self)
        self.text.setStyleSheet(
        """QPlainTextEdit {background-color: #333;
                           color: #00FF00;
                           font-family: Courier;}""")
        self.text.setReadOnly(True)
        self.text.setWindowTitle("Console");
        #self.text.setGeometry(20,20,500,400);
        self.text.insertPlainText("*** Profile  Viewer - Console ***\n")
        self.text.insertPlainText("*** L. Arnaud - CesBIO (2019) ***\n")
       

        clearButton = QPushButton('Clear Console', self)
        #clearButton.setToolTip('To load profile from database')
        clearButton.clicked.connect(self.clear)

        vbox = QtWidgets.QVBoxLayout(self)
        vbox.addWidget(self.text,80)
        vbox.addWidget(clearButton,20)

    def clear(self):
        self.text.clear()
        self.text.insertPlainText("*** Profile  Viewer - Console ***\n")
        self.text.insertPlainText("*** L. Arnaud - CesBIO (2019) ***\n")
        #self.text.insertPlainText(">Initialization\n")


        #box.updateText(Qt::red, "Red text");


class ApplicationWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self,parent=None)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")
        self.setWindowIcon(QIcon('pv2.png'))
       
        self.file_menu = QtWidgets.QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.console = PrintConsole()
        self.console_menu = QtWidgets.QMenu('&Console', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.console_menu)
        self.console_menu.addAction('&Console', self.displayConsole)

        self.help_menu = QtWidgets.QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)
        self.help_menu.addAction('&About', self.about)

        self.main_widget = QtWidgets.QWidget(self)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        #ProfileWindow1 = TestButton() 
        self.ProfileWindow1 = ProfileWindow(self,"solid",True,"#AAAA00") 
        #dc = MyDynamicMplCanvas(self.main_widget, width=5, height=4, dpi=100)
        self.screen = MyMplCanvas(self, width=5, height=4, dpi=100)
        self.cprint("Initialization graphic")
        self.nav = NavigationToolbar(self.screen,self)
        #self.ClearButton = QPushButton('Clear', self)
        #self.ClearButton.setToolTip('To clear the screen of all displayed profiles')
        #self.ClearButton.clicked.connect(self.ClearScreen)

        hbox = QtWidgets.QHBoxLayout(self.main_widget)
        hbox.addWidget(self.ProfileWindow1,5)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.nav)
        vbox.addWidget(self.screen)
        #vbox.addWidget(self.ClearButton)

        hbox.addLayout(vbox,90)

    #    vbox = QtWidgets.QVBoxLayout(self.main_widget)
    #    vbox.addLayout(hbox)
    #    vbox.addWidget(self.screen)
    #    vbox.addWidget(self.ClearButton)

    #    self.setLayout(hbox)

        #self.Qbutton

        #self.statusBar().showMessage("Vive le punk", 2000)

    def ClearScreen(self):
        self.screen.axes.cla()  
        self.screen.draw()

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def displayConsole(self):
        self.console.show() 

    def about(self):
        QtWidgets.QMessageBox.about(self, "About",
                                    """Allow the plot of extracted profiles

Ludovic Arnaud - CesBIO (2019)""")

    def cprint(self,message):
        now = QDateTime.currentDateTime()
        timeString = now.toString("yyyy-MM-dd-HH:mm:ss")
        self.console.text.insertPlainText(timeString + ">" + message + "\n")
 

class TestButton(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        l = QtWidgets.QHBoxLayout(self)
        self.bouton1 = QPushButton('Button1', self)
        self.bouton1.setToolTip('This is button 1')
        self.bouton2 = QPushButton('Button2', self)
        self.bouton2.setToolTip('This is button 2')
        l.addWidget(self.bouton1)
        l.addWidget(self.bouton2)


class ProfileWindow(QtWidgets.QWidget):
    def __init__(self, window, style, IsSync, colString): 
        super().__init__()
        self.window = window
        self.style = style
        self.IsSync = IsSync
        l = QtWidgets.QVBoxLayout(self)
        self.col = QColor(colString)

        # Label
        self.label = QLabel("No database loaded yet")
        l.addWidget(self.label)

        # Load button
        load = QPushButton('Load Profiles', self)
        load.setToolTip('To load profile from database')
        load.clicked.connect(self.click_to_load)
        #load.move(500,0)
        #load.resize(40,30)
        l.addWidget(load)

        self.labelKClassNumber = QLabel("Kmeans classw Number")
        l.addWidget(self.labelKClassNumber)
        self.KClassNumber= QComboBox()
        self.KClassNumber.addItem("2")       
        self.KClassNumber.addItem("3")       
        self.KClassNumber.addItem("4")       
        self.KClassNumber.addItem("5")       
        self.KClassNumber.addItem("6")       
        l.addWidget(self.KClassNumber)

        self.labelBefore = QLabel("Class Before")
        l.addWidget(self.labelBefore)
        self.ClassBefore = QComboBox()
        l.addWidget(self.ClassBefore)

        self.labelAfter = QLabel("Class After")
        l.addWidget(self.labelAfter)
        self.ClassAfter = QComboBox()
        l.addWidget(self.ClassAfter)

        self.ClassBefore.currentIndexChanged.connect(self.selectionchange)
        self.ClassAfter.currentIndexChanged.connect(self.selectionchange)
        self.KClassNumber.currentIndexChanged.connect(self.selectionchange)
        # Primitive picker

        self.BandsList = QListWidget()
        ls = ['B2', 'B3', 'B4','B5','B6','B7','B8','B8A','B11','B12','NDVI','Green NDWI','Swir NDWI','Brightness']
        defaultItem = QListWidgetItem('NDVI')
        self.BandsList.addItems(ls)
        self.BandsList.setCurrentRow(10)
        self.BandsList.clicked.connect(self.UpdatePrimitive)
        self.BandsList.setVisible(False)
        l.addWidget(self.BandsList)

        # load last use profiles


    def selectionchange(self,i):
        combo = self.sender()
        if combo == self.ClassBefore:
            self.tclass1 = combo.currentText()
        if combo == self.ClassAfter:
            self.tclass2 = combo.currentText()
        if combo == self.KClassNumber:
            self.nclass = int(combo.currentText())

        self.cprint("Class 1: %s"%(self.tclass1))
        self.cprint("Class 2: %s"%(self.tclass2))
        try:
            self.PlotUpdate()
        except:
            self.cprint("Data Error - ignore change")
            #aw.Up         
            pass

   
    #def color_click(self):
    #   self.col = QColorDialog.getColor()

    def UpdatePrimitive(self):
      self.cprint("Update start")
      bandDic = {'B2':"b2_%d",
                  'B3':"b3_%d",
                  'B4':"b4_%d",
                  'B5':"b5_%d",
                  'B6':"b6_%d",
                  'B7':"b7_%d",
                  'B8':"b8_%d",
                  'B8A':"b8a_%d",
                  'B11':"b11_%d",
                  'B12':"b12_%d",
                  'NDVI':"(b8_%d - b4_%d)/(b8_%d + b4_%d + 0.00000001)",
                  'Green NDWI':"(b3_%d - b8_%d)/(b3_%d + b8_%d + 0.00000001)",
                  'Swir NDWI':"(b8a_%d - b11_%d)/(b8a_%d + b11_%d + 0.00000001)",
                  'Brightness':"b2_%d*b2_%d+b3_%d*b3_%d+b4_%d*b4_%d"}
      pickedBand = self.BandsList.currentItem().text()
      self.bandPatern = bandDic[pickedBand]
      self.bands = self.generatePrimitives()

      QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
      self.label.setText("Loading... please wait.")
      QtGui.QGuiApplication.processEvents()  
      self.LoadProfile()
      self.label.setText(pickedBand+"\n"+self.fileName.split("/")[-1])
      QApplication.restoreOverrideCursor()
      self.cprint("Update end")
 

    def click_to_load(self):
        self.openFileNameDialog()

    #def CreateTable(self,data,table,header):
    #    Nrow = len(data)
    #    Ncol = len(data[0])
    #    table.setRowCount(Nrow)
    #    table.setColumnCount(Ncol)
    #    table.setHorizontalHeaderLabels(header)

    #    for i in range(Nrow):
    #        for j in range(Ncol):
    #            table.setItem(i,j, QTableWidgetItem("%s"%(data[i][j])))

    #    table.resizeColumnsToContents()
    #    table.setCurrentCell(0,0)                   

 
    def openFileNameDialog(self,fileName = None):
        if fileName == None:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            #self.fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","qlite3 database (*.sqlite);;All Files (*)", options=options)
            self.fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","pickle dataframe (*.pkl);;All Files (*)", options=options)
        else:
            self.fileName = fileName

        if self.fileName:
            try:
                # Manage dates

                dates = np.loadtxt("/datalocal1/home/arnaudl/ColzaDigital/kmeans/S1-S2_2018_ColzaDigital.txt")
                print(dates)
                #locale.setlocale(locale.lc_time, "en_us")
                dt  = [datetime.strptime(str(int(d)), '%Y%m%d') for d in dates]
                self.doy = [d.strftime('%d-%b') for d in dt]
                self.days = np.array([(d - dt[0]).days for d in dt])
                self.dstart = 0
                self.dend = len(self.days) - 1
                self.cprint("Dates loaded")

                self.nclass = 4
                self.tclass1 = "CZH"
                self.tclass2 = "CZH"

                #self.window.console.text.insertPlainText(">Test\n")
                #self.bandPatern = "(b8_%d - b4_%d)/(b8_%d + b4_%d + 0.00000001)"
                self.profiles = pd.read_pickle(self.fileName)
                self.columns = list(self.profiles.columns)               
                self.ListClassesCol1  = self.columns[1:2] 
                self.ListClassesCol2 = self.columns[2:3] 
                self.ListClasses1 = np.unique(self.profiles[self.ListClassesCol1].values)
                self.ListClasses2 = np.unique(self.profiles[self.ListClassesCol2].values)
                self.NameClasses1 = [code2rpg[x] for x in self.ListClasses1]
                self.NameClasses2 = [code2rpg[x] for x in self.ListClasses2]

                aw.ProfileWindow1.ClassBefore.addItem("None")
                for x in self.NameClasses1:
                    aw.ProfileWindow1.ClassBefore.addItem(x)

                for x in self.NameClasses2:
                    aw.ProfileWindow1.ClassAfter.addItem(x)

                self.cprint("Profiles loaded")
                self.PlotUpdate()
                #self.window.screen.ax2.cla()
                #self.window.screen.ax2.plot(t,s2,'g')
                #self.window.screen.fig.canvas.draw_idle()
                #self.UpdatePrimitive()
                #Nbr,self.Class,self.Parcel = self.summaryDB(self.fileName)
                #self.CreateTable(self.Class,self.ClassTable,["Code","Name"])
                #self.CreateTable(self.Parcel,self.ParcelTable,["Parcel ID","Code"])
                #self.BandsList.setVisible(True)
            except:
                raise
                self.label.setText("ERROR: database file is invalid")

    def PlotUpdate(self):
        # get class local variables 
        days = self.days
        dstart = self.dstart
        dend = self.dend
        profiles = self.profiles
        nclass = self.nclass
        tclass1 = self.tclass1
        tclass2 = self.tclass2

        # construc dataframe selection colums
        TableCol = self.columns[:6]  
        StatsCol = self.columns[6:]
        MeanCol = [s for s in StatsCol if "mean_ndvi" in s]
        StdvCol = [s for s in StatsCol if "stdv_ndvi" in s]
        SoilCol = [s for s in StatsCol if "soil" in s]
        [par,c1,c2,d1,d2,npix] = TableCol
        
        # Select specific time period
        MeanColPeriod = MeanCol[dstart:dend]
        StdvColPeriod = StdvCol[dstart:dend]
        
        if(tclass1 == "None"):
          ### DATASET CONSTRUCTION #####################################################
          # Only table
          AllTable = profiles[TableCol]
          
          # Only table for specific class
          
          ClassTable = AllTable[AllTable[c2] == rpg2code[tclass2]]
          
          # Only profiles for specific class with all date
          AllSoil = profiles[profiles[c2] == rpg2code[tclass2]][SoilCol]
          AllMeanProfiles = profiles[profiles[c2] == rpg2code[tclass2]][MeanCol]
          AllStdvProfiles = profiles[profiles[c2] == rpg2code[tclass2]][StdvCol]
          
          # Only profiles for specific class and specific period  = kmeans Features
          PerMeanProfiles = profiles[profiles[c2] == rpg2code[tclass2]][MeanColPeriod]
          PerStdvProfiles = profiles[profiles[c2] == rpg2code[tclass2]][StdvColPeriod]
        else:
          # Only table
          AllTable = profiles[TableCol]
          
          ClassTable = AllTable[(AllTable[c1] == rpg2code[tclass1]) & (AllTable[c2] == rpg2code[tclass2])] 
        
          # Only profiles for specific class with all date
          AllSoil = profiles[(AllTable[c1] == rpg2code[tclass1]) & (AllTable[c2] == rpg2code[tclass2])][SoilCol]
          AllMeanProfiles = profiles[(AllTable[c1] == rpg2code[tclass1]) & (AllTable[c2] == rpg2code[tclass2])][MeanCol]
          AllStdvProfiles = profiles[(AllTable[c1] == rpg2code[tclass1]) & (AllTable[c2] == rpg2code[tclass2])][StdvCol]
          
          # Only profiles for specific class and specific period  = kmeans Features
          PerMeanProfiles = profiles[(AllTable[c1] == rpg2code[tclass1]) & (AllTable[c2] == rpg2code[tclass2])][MeanColPeriod]
          PerStdvProfiles = profiles[(AllTable[c1] == rpg2code[tclass1]) & (AllTable[c2] == rpg2code[tclass2])][StdvColPeriod]
        
        ##############################################################################
       
        # Perform kmeans algo
        features = PerMeanProfiles.values
        whitened = whiten(features)
        codebook, labels = kmeans2(whitened,nclass)
        
        # Add kmeans class to profiles
        klim = 4
        self.KmeansMean = AllMeanProfiles
        self.KmeansMean['kmeans'] = labels
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
        npixels =  AllTable[npix]
        KmeansSoil = AllSoil
        KmeansSoil['npixels'] = npixels
        KmeansSoil['kmeans'] = labels
        npKmeansSoil = KmeansSoil.values
        
        ListSoil = []
        ListSoilMainClass = []
        ListSoilMaxVal    = []
        for i in range(nclass):
            #ListSoil.append((npKmeansSoil[npKmeansSoil[:,-1] == i][:,:-1]/npKmeansSoil[npKmeansSoil[:,-1] == i][:,-2,None])[:-1])
            SoilVector =  (npKmeansSoil[npKmeansSoil[:,-1] == i][:,:-1]/npKmeansSoil[npKmeansSoil[:,-1] == i][:,-2,None])[:,:-1]
            ListSoil.append(SoilVector)
            ListSoilMainClass.append(np.argmax(SoilVector, axis = 1))
            ListSoilMaxVal.append(np.max(SoilVector, axis = 1))
        
        SoilCounter = []
        for i in range(nclass):
            counter = collections.Counter(ListSoilMainClass[i])
            counterList = [ [int(SoilCol[int(w)][5:]), counter[w]] for w in sorted(counter, key=counter.get, reverse=True)]
            SoilCounter.append(counterList[:slim])
        
        SoilCountMatrix = np.array(SoilCounter)
        
        soilkey = SoilCountMatrix[:,:,0]
        soilval = SoilCountMatrix[:,:,1]

        fig =  aw.screen.fig
        ax1 = aw.screen.ax1
        ax2 = aw.screen.ax2
        ax3 = aw.screen.ax3

        ax1.cla()
        ax2.cla()
        ax3.cla()

        if tclass1 == "None":
            ax1.set_title("k-meams of the class %s with %d clusters (%s %s)"%(tclass2,nclass,"2018","T31TJC"))
        else:
            ax1.set_title("k-meams of the classes %s/%s with %d clusters (%s %s)"%(tclass1,tclass2,nclass,"2018","T31TJC"))

        ax1.set_xticks(days)
        ax1.set_xticklabels(self.doy,rotation = 90,fontsize = 8)
        ax1.set_ylim([0,1])
        ax1.set_xlabel('DOY', fontsize = 10)
        ax1.set_ylabel('<NDVI>', fontsize = 10)

        ax2.set_title("Profiles distributions on the %s"%(self.doy[0]))
        ax2.set_xlabel('<NDVI>', fontsize = 10)
        ax2.set_xlabel('P(<NDVI>)', fontsize = 10)
        
        ax3.set_xticks(range(nclass))
        ax3.set_xlabel('Previous year class', fontsize = 10)
        ax3.set_xlim([-0.5, nclass])

        # Draw zones
        period_col = 'g'
        self.zone = ax1.axvspan(days[dstart], days[dend], alpha=0.2, color = period_col)
        self.changezone = ax1.axhspan(0, 0.02, alpha=0.1, color = 'k')
        self.zonetext = ax1.text(days[dstart]+ 0.5, 0.97, "k-means period", fontsize = 10, color = period_col)


        # Plot averaged profile for each kmeans class on ax1
        ntotal = len(self.KmeansMean[MeanCol].values)
        nbin = 40
        self.meanList  = [None]*nclass
        pickList  = [None]*nclass
        for l in range(nclass):
            profs      = self.KmeansMean[self.KmeansMean['kmeans'] == l ][MeanCol]
            num = len(profs)
            MeanMean = profs.mean().values
            StdvMean = profs.std().values
            ErrMean = profs.std().values/np.sqrt(num)
            self.meanList[l] = ax1.plot(days,MeanMean, label = "Cluster %d [%d/%d][%d%%]"%(l,num,ntotal,100*num/ntotal), lw = 1.5, ls = "--")
            col = self.meanList[l][0].get_color()
        ax1.legend(bbox_to_anchor=(1.04,1), loc="upper left", facecolor='white')

        # Plot selection zones on ax1
        colList = []
        self.dline = ax1.axvline(days[dstart], ymin=0, ymax=1, color  = "k", alpha = 0.5, lw = 0.5)

        # Plot profile distributions on ax2
        for l in range(nclass):
            data = self.KmeansMean[self.KmeansMean['kmeans'] == l ]["mean_ndvi_%d"%(dstart)].values
            col = self.meanList[l][0].get_color()
            colList.append(col)
            ax2.hist(data, nbin, alpha=0.20, color = col)
            ax2.axvline(np.mean(data), ymin=0, ymax=100, color  = col, alpha = 0.5, lw = 0.5)
       
        #  previous class and soil histogram on ax3
        width = 0.1
        barsPrevious = ax3.bar(range(nclass), val[:,0], width, color = colList, edgecolor = 'k')
        barsSoil     = ax3.bar(np.array(range(nclass)) + 0.1, soilval[:,0], width, color = colList, edgecolor = 'k', alpha = 0.5)
        for i in range(1,klim):
            try:
                barsPrevious = barsPrevious + ax3.bar(range(nclass), val[:,i] , width, np.sum(val[:,:i],axis=1), color = colList, edgecolor = 'k')
            except:
                pass
        
        for i in range(1,slim):
            try:
                barsSoil = barsSoil + ax3.bar(np.array(range(nclass)) + 0.1, soilval[:,i] , width, np.sum(soilval[:,:i],axis=1), color = colList, edgecolor = 'k', alpha = 0.5)
            except:
                pass
        
        for x in range(nclass):
            for y,(k,v) in enumerate(zip(key[x],val[x])):
                ax3.text(x + 0.15, 100*y, "%s %d"%(code2rpg[int(k)],v) , fontsize = 8)
            for y,(k,v) in enumerate(zip(soilkey[x],soilval[x])):
                ax3.text(x + 0.15, 100*y + 600, "%s %d"%(k,v) , fontsize = 8)
                        
        fig.canvas.draw_idle()



    def cprint(self,message):
        now = QDateTime.currentDateTime()
        timeString = now.toString("yyyy-MM-dd-HH:mm:ss")
        self.window.console.text.insertPlainText(timeString + ">" + message + "\n")
      
def onclick(event):
    fig = aw.screen.fig
    ax1 = aw.screen.ax1
    ax2 = aw.screen.ax2
    ax3 = aw.screen.ax3
    dline = aw.ProfileWindow1.dline
    zone = aw.ProfileWindow1.zone
    zonetext = aw.ProfileWindow1.zonetext
    days = aw.ProfileWindow1.days
    doy = aw.ProfileWindow1.doy
    dstart = aw.ProfileWindow1.dstart
    dend = aw.ProfileWindow1.dend
    nclass = aw.ProfileWindow1.nclass
    KmeansMean = aw.ProfileWindow1.KmeansMean
    meanList = aw.ProfileWindow1.meanList
  
 

    # Even
    if event.inaxes == ax1:
        if(0.0 < event.ydata and event.ydata < 0.02):
            try:
                aw.ProfileWindow1.dstart,aw.ProfileWindow1.dend = updateZone(zone,zonetext,event,days)
                aw.ProfileWindow1.PlotUpdate()
            except:
                raise

        else:
            print("ICI")
            try:
                nbin = 40
                # Deal with profile histograms
                x0,y0,x1,y1 =  pickXY(event,days,dstart,dend)
                dline.set_xdata(days[x0])
                ax2.cla()
                ax2.set_title("Profiles distributions on the %s"%(doy[x0]))
                for l in range(nclass):
                    data = KmeansMean[KmeansMean['kmeans'] == l ]["mean_ndvi_%d"%(x0)].values
                    col = meanList[l][0].get_color()
                    ax2.hist(data, nbin, alpha=0.20, color = col)
                    ax2.axvline(np.mean(data), ymin=0, ymax=100, color  = col, alpha = 0.5, lw = 0.5)
            except:
                raise

    fig.canvas.draw_idle()


def pickXY(event, days, dstart, dend):
    """ pick x y and rescale to days """
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


def updateZone(zone,zonetext,event,days):
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





####i MAIN #######################################################################

 
        
qApp = QtWidgets.QApplication(sys.argv)

aw = ApplicationWindow()
aw.setWindowTitle("%s" % progname)
aw.screen.fig.canvas.mpl_connect('button_press_event',onclick)
aw.show()
try:
   #f = open('.save')
   #nclass = int(f.readline())
   #FileName = str(f.readline()).strip()
   #f.close()
   FileName =  "Profiles_NDVI_31TCJ_0_64_soil.pkl"
   aw.ProfileWindow1.openFileNameDialog(FileName)
except:
   raise
   aw.ProfileWindow1.openFileNameDialog()


sys.exit(qApp.exec_())
