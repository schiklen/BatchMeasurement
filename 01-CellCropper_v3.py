from javax.swing import (JButton, JFrame, JPanel, JLabel, JTextField, JScrollPane, SwingConstants, WindowConstants, BoxLayout)
from java.awt import Component, GridLayout, Color
import re
import copy
from os import path as pth
from os import makedirs as mkdir
from os import listdir
from java.awt.event import KeyEvent, KeyAdapter, MouseEvent, MouseAdapter
from ij.plugin import Zoom
from ij.gui import Overlay
from ij.io import OpenDialog, Opener


G_saveSubFold = "cutout"

def cut(event):
   roi = imp.getRoi()
   if roi != None:
      newRoi = roi.clone()
      Dup = Duplicator().run(imp, 1, imp.getNChannels(), 1, imp.getNSlices(), 1, imp.getNFrames())
      newRoi.setLocation(0,0)
      Dup.setRoi(newRoi)
      Dup.setTitle(Men.getTextField() + str(Men.getCounter()))
      Dup.show()
      Men.setCounter()
      Men.addOlay(roi)
      imp.setOverlay(Men.getOverlay())   #setOverlay(Roi roi, java.awt.Color strokeColor, int strokeWidth, java.awt.Color fillColor) 
      imp.getOverlay().drawLabels(True) # drawNumber
      imp.deleteRoi()
      saveFolder = pth.join(pth.split(pth.dirname(Men.getPath()))[0], G_saveSubFold)
      if not pth.exists(saveFolder):
         print "Making directory " + saveFolder
         mkdir(saveFolder)
      savePath = pth.join(saveFolder, (Dup.getTitle()+".tif"))
      print savePath
      IJ.saveAs(Dup, ".tiff", savePath)
      print "Saved as " + savePath
      Dup.close()

def delOverlay(event):
   IJ.run(imp, "Remove Overlay", "")
   print "clearOverlay"
   Men.clearOverlay()

def saveOverlay(event):
   if Men.getOverlay() != []:
      Men.saveOverlay()
      
def quit(event):
   Men.close()
   Men.getImp().close()

     
class Menue(object):
   def __init__(self):
      self.counter = 1
      self.olay = Overlay()
      
      self.od = OpenDialog("Open movie", "")
      self.path = self.od.getDirectory()

      self.filename = self.od.getFileName()
      self.position = self.getPosition(self.path, self.filename)
      regex = re.compile('(?P<prefix>.+)(?P<suffix>\.tif|\.dv)$')
      if regex.match(self.filename):  #on .dv, use LOCI
         if regex.match(self.filename).group('suffix') == ".tif":
            self.imp = Opener().openImage(self.path+self.filename)
            self.fnPrefix = regex.match(self.filename).group('prefix')
         if regex.match(self.filename).group('suffix') == ".dv":
            self.fnPrefix = regex.match(self.filename).group('prefix')
            IJ.run("Bio-Formats Importer", "open=["+self.path+self.filename+"] autoscale color_mode=Grayscale view=Hyperstack stack_order=XYCZT")
            self.imp = IJ.getImage()
      self.imp.show()

      # check if there is an existing overlay file and load it!
      olre = re.compile(self.fnPrefix+'.zip')
      self.filelist = listdir(self.path)
      for ol in self.filelist:
         if olre.match(ol):
            print olre.match(ol).group()
            try:
               rm = RoiManager.getInstance()
               rm.runCommand("reset")
               Opener().openZip(self.path + olre.match(ol).group())
               IJ.run("From ROI Manager", "")               
            except AttributeError:        
               Opener().openZip(self.path + olre.match(ol).group())
               IJ.run("From ROI Manager", "")
               rm = RoiManager.getInstance()
               rm.runCommand("Show All with labels")
               rm = RoiManager.getInstance()

      self.frame = JFrame("CellCropper", size=(200,200))
      self.frame.setLocation(20,120)
      self.Panel = JPanel(GridLayout(0,1))
      self.frame.add(self.Panel)
      self.nameField = JTextField("p" + str(self.position) + "_c",15)
      self.Panel.add(self.nameField)
      self.cutoutButton = JButton("Cut out cell",actionPerformed=cut)
      self.Panel.add(self.cutoutButton)
      self.delOlButton = JButton("Delete Overlay",actionPerformed=delOverlay)
      self.Panel.add(self.delOlButton)
      self.saveOlButton = JButton("Save Overlay",actionPerformed=saveOverlay)
      self.Panel.add(self.saveOlButton) 
      self.quitButton = JButton("Quit script",actionPerformed=quit)
      self.Panel.add(self.quitButton)
      self.frame.pack()
      WindowManager.addWindow(self.frame)
      self.show()
      IJ.setTool("freehand")

   def getPosition(self, path, filename):
      fileList = listdir(path)
      regex = re.compile('(?P<prefix>.+)(?P<suffix>\.tif|\.dv)$')
      imagesInFolder = [pth.splitext(f)[0] for f in fileList if regex.match(f)]
      unique = sorted(list(set(imagesInFolder)))
      
      if filename + ".zip" in fileList:
         openOl(path, filename)
      
      return unique.index(pth.splitext(filename)[0]) + 1

   def openOl(self, path, filename):
      print "aaaaah"

   def show(self):
      self.frame.visible = True

   def close(self):
      if self.olay != None:
         yncd = YesNoCancelDialog(self.frame, "Save overlay?", "Save overlay?") #frame, title, message
         if yncd.yesPressed():
            self.saveOverlay()
      WindowManager.removeWindow(self.frame)
      self.frame.dispose()
      
   def setCounter(self):
      self.counter += 1
      
   #'get' functions
   def getImp(self):
      return self.imp
   
   def getCounter(self):
      return self.counter
      
   def getFrame(self):
      return self.frame
      
   def getPath(self):
      return self.path

   def getTextField(self):
      return self.nameField.text
   # overlay functions
   def addOlay(self, roi):
      self.olay.add(roi)

   def getOverlay(self):
      return self.olay

   def clearOverlay(self):
      self.olay.clear()
      self.counter = 1

   def saveOverlay(self):
      self.rm = RoiManager.getInstance()
      if self.rm == None:
         rm = RoiManager()
      rm.runCommand("reset")
      IJ.run("To ROI Manager", "")
      print "Saving overlay as " + self.path+ self.fnPrefix+".zip"
      rm.runCommand("Save", self.path+self.fnPrefix+".zip") # too long?
      rm.runCommand("reset")
      rm.close()


#--- MAIN ---

Men = Menue()
imp = Men.getImp()
imp.show()
