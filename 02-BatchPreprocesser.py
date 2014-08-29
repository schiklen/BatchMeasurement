# Batch extension for Kotas dot segmenting script PreProcessing!
# by Christoph Schiklenk (schiklen@embl.de)
# with help of Kota Miura, CMCI (miura@embl.de)

from os import listdir, makedirs
from os import path as pth
import re
from ij.plugin.filter import Filler as CO
from emblcmci.foci3Dtracker import PreprocessChromosomeDots as PPC
from ij.plugin import ChannelSplitter as CS
from ij.plugin import RGBStackMerge as StackMerge
from ij.io import DirectoryChooser
from ij.process import ImageConverter

G_saveSubFold = "ppcd"
G_saveFilePrefix = "ppcd_"

#- - -   M A I N   - - -
# select directory that is to be processed
path = DirectoryChooser("DotSeg Preprocess Batch Extension - Please choose directory containing the images").getDirectory()
saveFolder = pth.join(pth.split(pth.dirname(path))[0], G_saveSubFold)


# create list of match objects of .tiff files in directory
regEx = re.compile('(?!ppcd_)(?P<prefix>.+).tiff?$', re.IGNORECASE)
moFileList = []    # match object File list
for fileName in listdir(path):
   if regEx.match(fileName):   # if matches RE, add to list
      moFileList.append(regEx.match(fileName))

if moFileList == []:
   IJ.showMessage("Input Exception", "No unprocessed images found in the directory you selected.")
   raise IOError("No unpocessed TIFFs found in this folder.")

for image in moFileList:
   print "Processing cell " + image.group() + " (" + str(moFileList.index(image)+1) + "/" + str(len(moFileList)) + ")"
   IJ.log("Processing cell " + image.group() + " (" + str(moFileList.index(image)+1) + "/" + str(len(moFileList)) + ")")
   imp = Opener().openImage(path + image.group()) # open Image
   #if imp.getBitDepth() != 8:  # converting to 8 bit if 
   #   ImageConverter(imp).convertToGray8()
   roi = imp.roi
   imps = CS.split(imp)
   ppc = PPC()
   for aimp in imps:
      ppc.setImp(aimp)
      ppc.run()
      if roi != None:
         aimp.setRoi(roi)
         for n in range(1, aimp.getImageStackSize()+1):
            aimp.getImageStack().getProcessor(n).fillOutside(roi)
         aimp.killRoi()
   final = StackMerge.mergeChannels(imps, False)
   final.copyScale(imp) # copyscale from .copyscale
   if not pth.exists(saveFolder):
      makedirs(saveFolder)
   fileName = G_saveFilePrefix + image.group('prefix')
   IJ.saveAs(final, ".tiff", pth.join(saveFolder, fileName) )  # saveAs(ImagePlus imp, java.lang.String format, java.lang.String path) 
   print "Successfully saved", G_saveFilePrefix + image.group('prefix')
   IJ.log("Successfully saved " + G_saveFilePrefix + image.group('prefix') + ".tif")
   for win in WindowManager.getIDList():
      imp = WindowManager.getImage(win)
      imp.close()
print "Finished."
IJ.log("Finished pre-processing.")