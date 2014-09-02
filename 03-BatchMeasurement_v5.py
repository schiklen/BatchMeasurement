# Batch extension for Kotas dot segmenting script
# by Christoph Schiklenk (schiklen@embl.de)
# with help of Kota Miura, CMCI (miura@embl.de)

from os import listdir as LD
from os import makedirs as mkdir
from os import path as pth
import os
import re
from ij.plugin.filter import Filler as CO
from emblcmci.foci3Dtracker import PreprocessChromosomeDots as PPC
from ij.plugin import ChannelSplitter as CS
from ij.plugin import RGBStackMerge as StackMerge
from emblcmci.foci3Dtracker import AutoThresholdAdjuster3D as ATA
from ij.io import DirectoryChooser, Opener
from ij.process import ImageConverter
from ij import WindowManager
from ij.text import TextWindow
from ij import IJ

# class timePoint should be in a separate file at some point.
class timePoint(object):

    def __init__(self, string):
        print string





G_saveSubFold = "meas"   # name of the subfolder that is suppodes to contain the result values and images

def readResults(windowTitle):
   textPanel = WindowManager.getFrame(windowTitle).getTextPanel()
   headings = textPanel.getColumnHeadings()
   
   "get results from TextWindow with java.lang.string title"
   resolver = re.compile('\d+\t(?P<frame>\d+\.0+)\t(?P<fsDistance>\d+\.\d+)\t(?P<ffDistance>\d+\.\d+)\t(?P<ssDistance>\d+\.\d+)\t(?P<fVol>\d+\.\d+)\t(?P<sVol>\d+\.\d+)')
   frameA = []
   distA = []
   volFcA = []
   volScA = []
   #xFcA, yFcA, zFcA, xScA, yScA, zScA
   resPnl = WindowManager.getFrame(windowTitle).getTextPanel()
   for row in range(resPnl.getLineCount()):
      mo = resolver.match(resPnl.getLine(row))
      frameA.append(int(float(mo.group('frame'))))
      distA.append(mo.group("fsDistance"))
      volFcA.append(mo.group("fVol"))
      volScA.append(mo.group("sVol"))
   return frameA, distA, volFcA, volScA
   

def fillUpFrames(frameA, distA, volFcA, volScA): # xFcA, yFcA, zFcA, xScA, yScA, zScA  # xFcA: x first channel array...
   "All frames that are not present are added and NA is written in measurements"
   for frame in range(max(frameA)):
      if frame not in frameA:
         if frame == 0:
           insPos = 0
         else:
           insPos = frameA.index(frame-1)+1
         frameA.insert(insPos, frame)
         distA.insert(insPos, "NA")
         volFcA.insert(insPos, "NA")
         volScA.insert(insPos, "NA")
         #xFcA, yFcA, zFcA, xScA, yScA, zScA
   return frameA, distA, volFcA, volScA

def makeTw(imp, FrameA, DistA, volFcA, volScA): #xFcA, yFcA, zFcA, xScA, yScA, zScA
   tw = TextWindow("Summary", "Frame \t Time \t Distance \t volChI \t volChII", "", 400, 700) #xFcA, yFcA, zFcA, xScA, yScA, zScA
   cal = imp.getCalibration()
   pxWidth = cal.pixelWidth
   timeInterval = round(cal.frameInterval) # test!!
   for row in range(len(FrameA)):
      try:
         product = cal.pixelWidth * float(DistA[row]) # distance in microns
         DistMy = "%.5f" % product   # round
      except ValueError:             # if is "NA"
         DistMy = "NA"
      time = "%.1f" % (timeInterval * float(FrameA[row]))
      tw.append(str(int(FrameA[row])+1)+"\t"+time+"\t"+DistMy+"\t"+volFcA[row]+"\t"+volScA[row])
      timePoint("test-tp")
   return tw

#- - -   M A I N   - - -
path = DirectoryChooser("DotSeg Preprocess Batch Extension - Please choose directory containing the images").getDirectory()
saveFolder = pth.join(pth.split(pth.dirname(path))[0], G_saveSubFold)
print saveFolder

regEx = re.compile('ppcd_(?P<name>p\d+_c\d+).tif$', re.IGNORECASE)   # create list of match objects of .tiff files in directory
moFileList = []                                               # match object File list
for fileName in LD(path):
   if regEx.match(fileName):                                  # if matches RE, add to list
      moFileList.append(regEx.match(fileName))
print moFileList

if moFileList == []:
   IJ.showMessage("Input Exception", "Directory does not contain any preprocessed images.")
   raise IOError("Input Exception: Directory does not contain any preprocessed images.")

if not pth.exists(saveFolder):   # check if directory for analysis-files is present 
   mkdir(saveFolder)

for image in moFileList:
   print "starting with cell " + image.group() + " " + "("+ str(moFileList.index(image)) + "/" + str(len(moFileList)) + ")"
   imp = Opener().openImage(path + image.group()) # open Image
   cal = imp.getCalibration()
   splitCh = CS.split(imp)                        # split channels
   #try:
   ATA().segAndMeasure(splitCh[0], splitCh[1])    # perform segmentation and measurement 
   #else: go to next element in moFileList
   
   WindowManager.getImage("binProjMerged").close()
   WindowManager.getImage("DUP_C1-"+image.group()).close()
   WindowManager.getImage("DUP_C2-"+image.group()).close()
   frameA, distA, volFcA, volScA = readResults("Statistics_Distance")   # get results from "Statistics_Distance" window
   WindowManager.getFrame("Statistics_Distance").close(False)


   

   frameA, distA, volFcA, volScA = fillUpFrames(frameA, distA, volFcA, volScA)
   tw = makeTw(imp, frameA, distA, volFcA, volScA)
   tw.getTextPanel().saveAs(saveFolder +"/val_" + image.group('name') + ".tsv") # save filledup results as text
   WindowManager.getFrame("Summary").close(False)
   WindowManager.getFrame("Statistics_Ch0").close(False)
   WindowManager.getFrame("Statistics_Ch1").close(False)
   
   detDots = WindowManager.getImage("DetectedDots")
   detDots.copyScale(imp)
   IJ.saveAs(detDots, ".tiff", saveFolder + "/zi_"+image.group('name')) # save the overlay with connecting line
   print "Saving as " +  image.group('name')
   detDots.close()

IJ.log("Finished")