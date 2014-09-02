# Batch extension for Kotas dot segmenting script
# by Christoph Schiklenk (schiklen@embl.de)

from os import listdir, makedirs
from os import path as pth
import os, re, math
from ij.plugin.filter import Filler as CO
from emblcmci.foci3Dtracker import PreprocessChromosomeDots as PPC
from ij.plugin import ChannelSplitter as CS
from ij.plugin import RGBStackMerge as StackMerge
from emblcmci.foci3Dtracker import AutoThresholdAdjuster3D as ATA
from ij.io import DirectoryChooser, Opener
from ij.process import ImageConverter
from ij.text import TextWindow
from ij import IJ, WindowManager

# GLOBALS
G_saveSubFold = "meas"   # name of the subfolder that is suppodes to contain the result values and images


class fr:
    def __init__(self, frame, distance, ch0DotList, ch1DotList):
        self.frame = int(float(frame))
        self.time = "%.1f" % (timeInterval * float(frame))
        try:
            self.distance = round((calibration.pixelWidth * float(distance)), 5)
            self.ch0Dot = ch0DotList
            self.ch1Dot = ch1DotList
            
            x_ch0, y_ch0, z_ch0 = self.ch0Dot.getXYZ()
            x_ch1, y_ch1, z_ch1 = self.ch1Dot.getXYZ()
            if (self.ch0Dot.getXYZ() != ("NA", "NA", "NA")) or (self.ch0Dot.getXYZ() != ("NA", "NA", "NA")):
                calDist = math.sqrt( math.pow((x_ch0-x_ch1),2)
                                   + math.pow((y_ch0-y_ch1),2)
                                   + math.pow((z_ch0-z_ch1),2) )
            print "Frame "+ str(self.frame), ": Calc dist " + str(calDist)
                                 
            # calculate distances from points themselves and compare
            # sqrt(x^2 + y^2 + z^2)
        # in case no dot was found
        except ValueError:
            self.distance = None
            self.ch0Dotlist = None
            self.ch1DotList = None

    def __repr__(self): # defines the print output.
        return "Frametime " + str(self.time)

    #def __cmp__(self): # defines sorting criterium
        #return self.frame

    def getFrame(self):
        return self.frame


class dot(object):
    def __init__(self, ch, frame, dotID, vol, x, y, z, intden):
        self.ch = ch
        self.frame = int(float(frame))

        try:
            self.dotID = int(float(dotID))
            self.vol = int(float(vol))
            self.x = round((calibration.pixelWidth * float(x)), 5)
            self.y = round((calibration.pixelWidth * float(y)), 5)
            self.z = round((calibration.pixelHeight * float(z)), 5) # "%.5f" %
        except ValueError:  # if is "NA"
            self.dotID = "NA"
            self.vol = "NA"
            self.x = "NA"
            self.y = "NA"
            self.z = "NA"

    def getFrame(self):
        return self.frame
        
    def getVol(self):
        return self.vol

    def getXYZ(self):
        return self.x, self.y, self.z


def tableToDots(lines, ch):
    dotList = []
    for l in lines[1:len(lines)-1]: #skip first line because its the col headings
        i, frame, dotID, vol, x, y, z, intden = l.split("\t")
        dotList.append(dot(ch, frame, dotID, vol, x, y, z, intden))
    return dotList

def dotListToSingle(dotList):
    if len(dotList) == 1:
       return dotList.pop()
    if len(dotList) == 0:
       return None


def makeTw( FrameA, DistA, volFcA, volScA): #xFcA, yFcA, zFcA, xScA, yScA, zScA
    tw = TextWindow("Summary", "Frame \t Time \t Distance \t volChI \t volChII", "", 400, 700) #xFcA, yFcA, zFcA, xScA, yScA, zScA
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

#- - -   M A I N   - - - --------------------------------------------------------------------------------------------------
inputDir = DirectoryChooser("DotSeg Preprocess Batch Extension - Please choose directory containing the images").getDirectory()
saveFolder = pth.join(pth.split(pth.dirname(inputDir))[0], G_saveSubFold)
print "Will save results in folder ", saveFolder

regEx = re.compile('ppcd_(?P<name>p\d+_c\d+).tif$', re.IGNORECASE)   # create list of match objects of .tiff files in directory
moFileList = []                                               # match object File list
for fileName in listdir(inputDir):
    if regEx.match(fileName):                                  # if matches RE, add to list
        moFileList.append(regEx.match(fileName))
print "Will process files ", moFileList

if moFileList == []:
    IJ.showMessage("Input Exception", "Directory does not contain any preprocessed images.")
    raise IOError("Input Exception: Directory does not contain any preprocessed images.")

if not pth.exists(saveFolder):   # check if directory for analysis-files is present 
    makedirs(saveFolder)

for image in moFileList: # get rid of 0!
    print "starting with cell " + image.group() + " " + "("+ str(moFileList.index(image)) + "/" + str(len(moFileList)) + ")"
    imp = Opener().openImage(inputDir + image.group()) # open Image
    # read calibration for later calculation of distances in um.
    calibration = imp.getCalibration()
    pxWidth = calibration.pixelWidth
    timeInterval = round(calibration.frameInterval)

    #start measurement
    splitCh = CS.split(imp)                        # split channels
    #try:
    ATA().segAndMeasure(splitCh[0], splitCh[1])    # perform segmentation and measurement 
    #else: go to next element in moFileList
    # move image to "segProblem" folder
    # continue

    #WindowManager.getImage("binProjMerged").close()
    #WindowManager.getImage("DUP_C1-"+image.group()).close()
    #WindowManager.getImage("DUP_C2-"+image.group()).close()

    # read the measurements from results tables.
    distance_lines = WindowManager.getFrame("Statistics_Distance").getTextPanel().getText().split("\n")
    ch0_dots = tableToDots(WindowManager.getFrame("Statistics_Ch0").getTextPanel().getText().split("\n"), 0)
    ch1_dots = tableToDots(WindowManager.getFrame("Statistics_Ch1").getTextPanel().getText().split("\n"), 1)

    #WindowManager.getFrame("Statistics_Distance").close(False)
    #WindowManager.getFrame("Statistics_Ch0").close(False)
    #WindowManager.getFrame("Statistics_Ch1").close(False)

    frameList = []
    for l in distance_lines[1:len(distance_lines)-1]:
        index, frame, distance, ch0dist, ch1dist, ch0vol, ch1vol = l.split("\t")
        # find respective frame in ch0 and ch1 dot list. Problem, if both dots have same volume.        
        ch0DotList = dotListToSingle( [d for d in ch0_dots if (d.getFrame() == int(float(frame)) and d.getVol() == int(float(ch0vol)) )] )
        ch1DotList = dotListToSingle( [d for d in ch1_dots if (d.getFrame() == int(float(frame)) and d.getVol() == int(float(ch1vol)) )] )
        frameList.append(fr(frame, distance, ch0DotList, ch1DotList))

    # fill up table with unsegmented frames.
    presentFrames = [f.getFrame() for f in frameList]
    missingFrames = [f for f in range(max(presentFrames)) if f not in presentFrames]

    for f in missingFrames:
        frameList.append(fr(f, None, None, None))

    print "FrameList", frameList
    #sort by frame

    # write to file.

    #------------ OLD
    #tw = makeTw(frameA, distA, volFcA, volScA)
    #tw.getTextPanel().saveAs(saveFolder +"/val_" + image.group('name') + ".tsv") # save filledup results as text
    #WindowManager.getFrame("Summary").close(False)

    # save Z-projection image with marked dots
    detDots = WindowManager.getImage("DetectedDots")
    detDots.copyScale(imp)
    IJ.saveAs(detDots, ".tiff", saveFolder + "/zi_"+image.group('name')) # save the overlay with connecting line
    print "Saving as " +  image.group('name')
    detDots.close()

IJ.log("Finished")
