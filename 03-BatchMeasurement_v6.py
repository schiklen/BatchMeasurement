# Batch extension for Kotas dot segmenting script
# by Christoph Schiklenk (schiklen@embl.de)

from os import listdir, makedirs
from os import path as pth
import pickle
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

def calc3DDistance(x_ch0, y_ch0, z_ch0, x_ch1, y_ch1, z_ch1):
    return math.sqrt( math.pow((x_ch0-x_ch1),2.0) + math.pow((y_ch0-y_ch1),2.0) + math.pow((z_ch0-z_ch1),2.0) )

class cell(object):
    def __init__(self, frameList): # should be constructed based on path.
        self.frameList = frameList # here: sort by framenumber!
        self.position =
        self.index =

    def exportData(self, exportFilePath):
        "A method to export xyz coordinates in microns, distances and all as .csv file"
        f = open(exportFilePath, "w")
        # Write a header
        # Date, strain, position, cell, separator sign "!"
        #write column names
        f.write("Frame,Timepoint,Distance,ch0x,ch0y,ch0z,ch0vol,ch1x,ch1y,ch1z,ch1vol\n")
        for frame in self.frameList:
            frameNumber = str(frame.getFrameNo())
            timepoint = str(frame.getTime())
            distance = str(frame.getDistance())# is always z-corrected distance in microns
            ch0Dot, ch1Dot = frame.getDots()
            ch0x, ch0y, ch0z = ch0Dot.getXYZ()
            ch0vol = str(ch0Dot.getVol())
            ch1x, ch1y, ch1z = ch1Dot.getXYZ()
            ch1vol = str(ch1Dot.getVol())
            line = frameNumber+","+timepoint+","+distance+","+str(ch0x)+","+str(ch0y)+","+str(ch0z)+","+ch0vol+","+str(ch1x)+","+str(ch1y)+","+str(ch1z)+","+ch1vol+"\n"
            f.write(line)
        f.close()

    def serialize(self, filePath):
        #pickle it
        print "serizalization in progress"

            

class fr:
    def __init__(self, frame, distance, ch0DotList, ch1DotList):
        self.frame = int(float(frame))
        self.time = round((timeInterval * float(frame)), 1) # "%.1f" % 
        try:
            self.distance = round((calibration.pixelWidth * float(distance)), 5)
            self.ch0Dot = ch0DotList
            self.ch1Dot = ch1DotList
            
            x_ch0, y_ch0, z_ch0 = self.ch0Dot.getXYZ()
            x_ch1, y_ch1, z_ch1 = self.ch1Dot.getXYZ()
            # this part is for processing of px-based values.
            zFactor = calibration.pixelHeight/calibration.pixelDepth
            x_ch0px, y_ch0px, z_ch0px = self.ch0Dot.getXYZpx()
            x_ch1px, y_ch1px, z_ch1px = self.ch1Dot.getXYZpx()
            z_ch0pxCorr = zFactor * z_ch0px
            z_ch1pxCorr = zFactor * z_ch1px
            
            if (self.ch0Dot.getXYZ() != ("NA", "NA", "NA")) or (self.ch0Dot.getXYZ() != ("NA", "NA", "NA")):
                self.micronDist = math.sqrt( math.pow((x_ch0-x_ch1),2.0)
                                   + math.pow((y_ch0-y_ch1),2.0)
                                   + math.pow((z_ch0-z_ch1),2.0) )
                nonZ_pxDist = calc3DDistance(x_ch0px, y_ch0px, z_ch0px, x_ch1px, y_ch1px, z_ch1pxCorr)
                Zcorr_pxDist = calc3DDistance(x_ch0px, y_ch0px, z_ch0pxCorr, x_ch1px, y_ch1px, z_ch1pxCorr)
        # in case no dot was found
        except ValueError:
            self.distance = None
            self.ch0Dotlist = None
            self.ch1DotList = None

    def __repr__(self): # defines the print output.
        return "Frametime " + str(self.time)

    #def __cmp__(self): # defines sorting criterium
        #return self.frame

    def getFrameNo(self):
        return self.frame

    def getDots(self):
        return self.ch0Dot, self.ch1Dot

    def getDistance(self):
        return self.distance

    def getTime(self):
        return self.time


class dot(object):
    def __init__(self, ch, frame, dotID, vol, x, y, z, intden):
        self.ch = ch
        self.frame = int(float(frame))

        try:
            self.dotID = int(float(dotID))
            self.vol = int(float(vol))
            self.xPx = x
            self.yPx = y
            self.zPx = z
            self.x = round((calibration.pixelWidth * float(x)), 5)
            self.y = round((calibration.pixelHeight * float(y)), 5)
            self.z = round((calibration.pixelDepth * float(z)), 5) # "%.5f" %
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
        
    def getXYZpx(self):
        return float(self.xPx), float(self.yPx), float(self.zPx)


def tableToDots(lines, ch):
    dotList = []
    for l in lines[1:len(lines)-1]: #skip first line because its the col headings
        i, frame, dotID, vol, x, y, z, intden = l.split("\t")
        dotList.append(dot(ch, frame, dotID, vol, x, y, z, intden))
    return dotList

def dotListToSingle(dotList):
    if len(dotList) > 1:
       return dotList.pop()
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

regEx = re.compile('ppcd_(?P<name>p\d+_c\d+).tif$', re.IGNORECASE)   # create list of match objects of .tif files in directory
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
    print "px depth", calibration.pixelDepth
    timeInterval = round(calibration.frameInterval)

    #start measurement
    splitCh = CS.split(imp)                        # split channels
    #try:
    ATA().segAndMeasure(splitCh[0], splitCh[1])    # perform segmentation and measurement 
    #else: go to next element in moFileList
    # move image to "segProblem" folder
    # continue

    WindowManager.getImage("binProjMerged").close()
    WindowManager.getImage("DUP_C1-"+image.group()).close()
    WindowManager.getImage("DUP_C2-"+image.group()).close()

    # read the measurements from results tables.
    distance_lines = WindowManager.getFrame("Statistics_Distance").getTextPanel().getText().split("\n")
    ch0_dots = tableToDots(WindowManager.getFrame("Statistics_Ch0").getTextPanel().getText().split("\n"), 0)
    ch1_dots = tableToDots(WindowManager.getFrame("Statistics_Ch1").getTextPanel().getText().split("\n"), 1)

    WindowManager.getFrame("Statistics_Distance").close(False)
    WindowManager.getFrame("Statistics_Ch0").close(False)
    WindowManager.getFrame("Statistics_Ch1").close(False)

    frameList = []
    for l in distance_lines[1:len(distance_lines)-1]:
        index, frame, distance, ch0dist, ch1dist, ch0vol, ch1vol = l.split("\t")
        # find respective frame in ch0 and ch1 dot list. Problem, if both dots have same volume. Vol can be identical!       
        ch0DotList = dotListToSingle( [d for d in ch0_dots if (d.getFrame() == int(float(frame)) and d.getVol() == int(float(ch0vol)) )] )
        ch1DotList = dotListToSingle( [d for d in ch1_dots if (d.getFrame() == int(float(frame)) and d.getVol() == int(float(ch1vol)) )] )

        frameList.append(fr(frame, distance, ch0DotList, ch1DotList))

    # fill up table with unsegmented frames.
    presentFrames = [f.getFrameNo() for f in frameList]
    missingFrames = [f for f in range(max(presentFrames)) if f not in presentFrames]

    for f in missingFrames:
        frameList.append(fr(f, None, None, None))
 
    #sort by frame   

    c = cell(frameList)
    # write to file.
    c.exportData(saveFolder +"/val_" + image.group('name') + ".csv")

    # save Z-projection image with marked dots
    detDots = WindowManager.getImage("DetectedDots")
    detDots.copyScale(imp)
    IJ.saveAs(detDots, ".tiff", saveFolder + "/zi_"+image.group('name')) # save the overlay with connecting line
    print "Saving as " +  image.group('name')
    detDots.close()

IJ.log("Finished")
