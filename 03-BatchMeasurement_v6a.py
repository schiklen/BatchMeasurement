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

class cell(object):
    def __init__(self, frameList): # should be constructed based on path.
        self.frameList = frameList # here: sort by framenumber!
        #self.position =
        #self.index =

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

    # delete this function later!
    def export(self, exportFilePath):
        "just for checking x y z and distances"
        f = open(exportFilePath, "w")
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
        
        if distance == None:  # No distance -> at least one dot is missing.
            self.distance = "NA"
            if ch0DotList == None:
                self.ch0Dot = dot(0, self.frame, "NA", "NA", "NA", "NA", "NA", "NA")
            else: # not the case yet since reading is based on distance table
                self.ch0Dot = ch0DotList
            if ch1DotList == None:
                self.ch1Dot = dot(1, self.frame, "NA", "NA", "NA", "NA", "NA", "NA")
            else: # not the case yet since reading is based on distance table
                self.ch1Dot = ch1DotList
        else:
            # the distance from the distance table (kota)
            self.distance_kota_m = round((calibration.pixelWidth * float(distance)), 5)
            self.distance_kota_p = float(distance)

            # own distance calculation: first x y z lengths to microns (made isotropic), then distance
            self.ch0Dot = ch0DotList
            self.ch1Dot = ch1DotList
            self.m_distance = self.calculateDistance(self.ch0Dot, self.ch1Dot)
            self.m_distance_p = self.m_distance/calibration.pixelWidth   # my/(my/px) = px

            # own distance calculation: first make isotropic in px, then calculate distance in px, then to microns
            x_ch0px, y_ch0px, z_ch0px = self.ch0Dot.getXYZpx()
            x_ch1px, y_ch1px, z_ch1px = self.ch1Dot.getXYZpx()
            zFactor = calibration.pixelDepth/calibration.pixelWidth # 0.4/0.13 = 3.017... each px in z should be multiplied by this.
            z_ch0pxCorr = zFactor * z_ch0px
            z_ch1pxCorr = zFactor * z_ch1px

            self.p_distance = math.sqrt( math.pow((x_ch0px-x_ch1px),2.0)
                                   + math.pow((y_ch0px-y_ch1px),2.0)
                                   + math.pow((z_ch0pxCorr-z_ch1pxCorr),2.0) )
            self.p_distance_m = self.p_distance * calibration.pixelWidth

            # calculation with next timepoint
            
            
            print "frame:", str(self.frame)
            print "kota_m    : " + str(self.distance_kota_m) + "  kota_p      : " + str(self.distance_kota_p)
            print "m_distance: " + str(round(self.m_distance, 5)) + "  m_distance_p: " + str(round(self.m_distance_p, 5))
            print "p_distance: " + str(round(self.p_distance, 5)) + "  p_distance_m: " + str(round(self.p_distance_m, 5))    


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

    def getDistances(self):
        return self.distance_kota_p, self.distance_kota_m, self.m_distance_p, self.m_distance, self.p_distance, self.p_distance_m

    def getTime(self):
        return self.time

        # static method to calculate distance between two dot objects. where should that be put? frame?
    @staticmethod
    def calculateDistance(dot1, dot2):
        x1, y1, z1 = dot1.getXYZ()
        x2, y2, z2 = dot2.getXYZ()
        if ((dot1.getXYZ() != ("NA", "NA", "NA")) or dot2.getXYZ() != ("NA", "NA", "NA")):
            distance = math.sqrt( math.pow((x1-x2),2.0) +
                                  math.pow((y1-y2),2.0) + 
                                  math.pow((z1-z2),2.0) )
            return distance
        else:
            return "NA"


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

for image in [moFileList[0]]: # get rid of 0!
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

    #WindowManager.getFrame("Statistics_Distance").close(False)
    #WindowManager.getFrame("Statistics_Ch0").close(False)
    #WindowManager.getFrame("Statistics_Ch1").close(False)

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
    frameList.sort(key=lambda x: x.getFrameNo())  

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
