from javax.swing import JButton, JFrame, JPanel, JLabel, JTextArea, JScrollPane, JProgressBar, SwingConstants, WindowConstants, JRadioButton, ButtonGroup
from java.awt import Component, Dimension, GridLayout
import re, random, os, sys, glob
from java.awt.event import ActionListener, KeyEvent, KeyAdapter, MouseEvent, MouseAdapter, WindowFocusListener
from ij.plugin import Zoom
from ij import WindowManager, IJ, ImagePlus
from ij.text import TextWindow, TextPanel
from ij.io import DirectoryChooser

# go through frames with arrowleft ()
# 0: anaphase Onset
# q: delete measurement


G_SAVESUBDIR = "qc-meas"
G_OPENSUBDIR = "meas"

def bigRound(x, base):
    return int(base * round(float(x)/base))


# - - - - Eventlistener classes - - - -
# - - - - - - - - - - - - - - - - - - -
class ListenToKey(KeyAdapter):
    def keyPressed(self, event):
        eventSrc = event.getSource()
        cT = eventSrc.getParent() #panel is the parent, canvas being component.
        if event.getKeyCode() == 37 and cT.getSelectionEnd() > 0:    # KeyCode 37 : arrowLeft
            cT.setSelection(cT.getSelectionEnd()-1, cT.getSelectionEnd()-1)
        if event.getKeyCode() == 39 and cT.getSelectionEnd() < cT.getLineCount(): # KeyCode 39 : arrowRight
            cT.setSelection(cT.getSelectionEnd()+1, cT.getSelectionEnd()+1)
        cT.changeFrame()
        if event.getKeyCode() == 48:      # Anaphase Onset Def. KeyCode 48 : 0
            cT.setAnaphase()
        if event.getKeyCode() == 81:      # KeyCode 81: q
            cT.delVal()
        # Prevent further propagation of the key event:
        keyEvent.consume()


class ListenToMouse(MouseAdapter):
    def mouseClicked(self, event):
        event.getSource().getParent().changeFrame()


class twFocusListener(WindowFocusListener):
    def windowGainedFocus(self, e):
        tw = e.getWindow()
        #tw.getTextPanel().requestFocusInWindow()

    def windowLostFocus(self, e):
        print e.getWindow()



class cell(object):
    def __init__(self, csvPath):
        self.csvPath = csvPath
        self.openDir, self.filename = os.path.split(self.csvPath)
        csvRE = re.compile( os.path.join('(?P<mainDir>.*)', '(?P<strain>.*)', G_OPENSUBDIR ,'val_p(?P<position>\d+)_c(?P<cell>\d+).csv') )    
        pathMO = re.match(csvRE, csvPath)
        self.mainDir = pathMO.group('mainDir')
        self.strain = pathMO.group('strain')
        self.position = int(pathMO.group('position'))
        self.cellNo = int(pathMO.group('cell'))
        self.measTifPath = os.path.join(self.openDir, "zi_p%i_c%i.tif" %(self.position, self.cellNo))
        self.qcCsvPath = os.path.join(self.mainDir, self.strain, G_SAVESUBDIR, "qc_val_p%i_c%i.csv") %(self.position, self.cellNo)
        self.isProcessed()
        self.anaphaseOnset = None
        self.annotation = None

    def isProcessed(self):
        if os.path.exists(self.qcCsvPath):
            self.processed = True
        else:
            self.processed = False

    def hasTif(self):
        if os.path.exists(self.measTifPath):
            self.processed = True
        else:
            self.processed = False

    def getAnOn(self):
        return self.anaphaseOnset

    def setAnOn(self, anaphaseOnset):
        self.anaphaseOnset = anaphaseOnset

    def annotate(self, annotation):
        self.annotation = annotation

    def getAnnotation(self):
        return self.annotation

    def getMeasTifPath(self):
        return self.measTifPath

    def getQcCsvPath(self):
        return self.qcCsvPath

    def getCsvPath(self):
        return self.csvPath
      

class MenueFrame(JFrame, ActionListener, WindowFocusListener): # should extend JFrame
    def __init__(self):
        self.mainDir = ""

        self.setTitle("Dots Quality Check")
        self.setSize(250, 300)
        self.setLocation(20,120)
        self.addWindowFocusListener(self)
        
        self.Panel = JPanel(GridLayout(0,1))
        self.add(self.Panel)
        self.openNextButton = JButton("Open Next Random", actionPerformed=self.openRandom)
        self.Panel.add(self.openNextButton)
        self.saveButton = JButton("Save", actionPerformed=self.save, enabled=False)
        self.Panel.add(self.saveButton)
        self.cropButton = JButton("Crop values from here", actionPerformed=self.cropVals)
        self.Panel.add(self.cropButton)
        self.DiscardButton = JButton("Discard cell", actionPerformed=self.discardCell)
        self.Panel.add(self.DiscardButton)
        self.quitButton = JButton("Quit script",actionPerformed=self.quit)
        self.Panel.add(self.quitButton)

        annoPanel = JPanel()
        #add gridlayout
        wtRButton = JRadioButton("wt", actionCommand="wt")
        wtRButton.addActionListener(self)
        defectRButton = JRadioButton("Defect", actionCommand="defect")
        defectRButton.addActionListener(self)
        annoPanel.add(wtRButton)
        annoPanel.add(defectRButton)
        self.aButtonGroup = ButtonGroup()
        self.aButtonGroup.add(wtRButton)
        self.aButtonGroup.add(defectRButton)
      
        self.Panel.add(annoPanel)

        self.ProgBar = JProgressBar()
        self.ProgBar.setStringPainted(True)
        self.ProgBar.setValue(0)
        self.Panel.add(self.ProgBar)

        self.pathLabel = JLabel("-- No main directory chosen --")
        self.pathLabel.setHorizontalAlignment( SwingConstants.CENTER )
        self.Panel.add(self.pathLabel)
      
        WindowManager.addWindow(self)
        self.show()

    # - - - -   B U T T O N   M E T H O D S  - - - -
    # - - - - - -  - - - - - - - - - - - - - - - - -
    def openRandom(self, event):      # when click here: get random cell and meas.measure(csv, tif, savePath)
        if self.mainDir == "":
            self.mainDir = DirectoryChooser("Random QC - Please choose main directory containing ctrl and test folders").getDirectory()
        try:
            # should be complete disposal!
            self.cT.closeWindows()
        finally:
            inFiles = glob.glob(os.path.join(self.mainDir, "*", G_OPENSUBDIR, "val_*.csv"))  # glob.glob returns list of paths
            uncheckedCells = [cell(csvPath) for csvPath in inFiles if cell(csvPath).processed == False]
            if len(uncheckedCells) > 0:
                self.cell = random.choice(uncheckedCells)
                #update progressbar
                self.ProgBar.setMaximum(len(inFiles)-1)
                self.ProgBar.setValue(len(inFiles)-len(uncheckedCells))
                # open imp and resultstable
                self.cT = correctionTable(self.cell, self) #self, openPath_csv, mF
                self.RBActionListener.setCell(self.cell)
            else:
                print "All cells measured!"

    def save(self, event):
        savepath = self.cell.getQcCsvPath()
        anaphase = self.cell.getAnOn()
        timeInterval = self.cT.getImp().getCalibration().frameInterval
        annotation = self.getAnnotation()
        position = str(self.cell.position)
        cellIndex = str(self.cell.cellNo)
        if not os.path.exists(os.path.split(savepath)[0]): # check if save folder present.
            os.makedirs(os.path.split(savepath)[0]) # create save folder, if not present
        f = open(savepath, "w")
        # Position Cell Phenotype Frame Time AnOn Distance ch0x ch0y ch0z ch0vol ch1x ch1y ch1z ch1vol
        f.write("Position,Cell,Phenotype,Frame,Time,Anaphase,Distance,ch0x,ch0y,ch0z,ch0vol,ch1x,ch1y,ch1z,ch1vol\n")
        for i in range(self.cT.getLineCount()):
            frame, distance, a = self.cT.getLine(i).split("\t")
            corrFrame = str(int(frame)-int(anaphase))
            time = "%.f" % (round(timeInterval) * int(corrFrame))
            if distance == "NA":
                ch0x, ch0y, ch0z, ch0vol, ch1x, ch1y, ch1z, ch1vol = "NA," * 7 + "NA"
            else:
                ch0x, ch0y, ch0z, ch0vol, ch1x, ch1y, ch1z, ch1vol = self.cT.getXYZtable()[i]
            f.write(position+","+cellIndex+","+annotation+","+corrFrame+","+time+","+anaphase+","+distance+","+ch0x+","+ch0y+","+ch0z+","+ch0vol+","+ch1x+","+ch1y+","+ch1z+","+ch1vol)
        f.close()
        print "Successfully saved!"

    def cropVals(self, event): #"this function deletes all values with frame > current cursor"   
        for line in range(self.cT.getSelectionEnd(), self.cT.getLineCount(), 1):
            frame, distance, AOCol = self.cT.getLine(line).split("\t")
            self.cT.setLine(line, frame + "\tNA" + "\t" + AOCol)

    def discardCell(self, event):
        if not os.path.exists(os.path.split(self.cell.getQcCsvPath() )[0]): # check if save folder present.
            os.makedirs(os.path.split(self.cell.getQcCsvPath() )[0]) # create save folder, if not present.
        f = open(self.cell.getQcCsvPath() ,"w")
        # Write dummy header. Position Cell Phenotype Frame Time AnOn Distance ch0x ch0y ch0z ch0vol ch1x ch1y ch1z ch1vol
        f.write("Position,Cell,Phenotype,Frame,Time,AnOn,Distance,ch0x,ch0y,ch0z,ch0vol,ch1x,ch1y,ch1z,ch1vol\n")
        f.close()
        print "Discarded cell - saved dummy" 

    def quit(self, event):
        try:
            self.cT.closeWindows()
        finally:
            WindowManager.removeWindow(self)
            self.dispose()

    # Methods implementing ActionListener interfaces:
    def actionPerformed(self, e):
        # this function is called when RadioButtons are changed
        self.cell.annotate( e.getSource().getActionCommand() )
        self.setSaveActive()

    def windowGainedFocus(self, e):
        pass

    def windowLostFocus(self, e):
        pass
        

    # - - - - - - - - - - - - -
    # - get and set methods - -
    # - - - - - - - - - - - - -
    def getAnnotation(self):
        return self.aButtonGroup.getSelection().getActionCommand()

    def getMainDir(self):
        return self.mainDir

    def setSaveActive(self):
        if (self.cell.getAnnotation() != None and self.cell.getAnOn() != None):
            self.saveButton.setEnabled(True)
            self.show()

    def setSaveInactive(self):
        self.saveButton.setEnabled(False)
        self.show()

    def setMainDir(self, path):
        self.mainDir = path
        self.pathLabel.setText("MainDir: " + os.path.basename(os.path.split(self.mainDir)[0]))


class correctionTable(TextPanel):
    """A class that displays an imagePlus and a resultstable. Resultstable and imp are linked in such a 
     way that click on a table row shows the imps respective timeframe."""
    def __init__(self, cell, mF, title="Results"): # add mF?
        # Call constructor of superclass
        TextPanel.__init__(self)
        # pass menue for setting save active/inactive
        self.cell = cell
        self.mF = mF
        # Create a window to show the content in
        self.window = JFrame()
        self.window.add(self)
        self.window.setTitle(title)
        # Add event listeners for keyboard and mouse responsiveness
        
        self.addKeyListener(ListenToKey())
        self.addMouseListener(ListenToMouse())
        
        # TODO: unpacking info out of cell object should be done in cell object itself and accessible e. g. via getData()
        self.imp = self.openImp(self.cell.getMeasTifPath())
        csvFile = open(self.cell.getCsvPath())        
        lines = csvFile.readlines()
        heads = lines.pop(0)
        self.setColumnHeadings("Frame\tDistance\tAnaphase")
        self.XYZtable = []
        for line in lines:      # load file lines in textPanel.
            frame, timepoint, dist, ch0x, ch0y, ch0z, ch0vol, ch1x, ch1y, ch1z, ch1vol = line.split(",")
            self.append(frame + "\t" + dist + "\t" )
            self.XYZtable.append((ch0x, ch0y, ch0z, ch0vol, ch1x, ch1y, ch1z, ch1vol))
        self.setSelection(0,0) # int startline, int endline
        self.changeFrame()
        self.mF.setSaveInactive()
        self.requestFocus()

        self.window.setSize(Dimension(220, 600))
        x = int(self.imp.getWindow().getLocation().getX()) + int(self.imp.getWindow().getWidth()) + 10
        self.window.setLocation(x, int(self.imp.getWindow().getLocation().getY()) )
        self.window.show()

    # Methods implementing KeyAdapter and MouseListener
    #... no multiple inheritance for Java classes?
    

    # - - - - Event driven methods - - - -
    # ------------------------------------

    def changeFrame(self):
        if self.getSelectionEnd() >= 0:
            frame, dist, AOCol = self.getLine(self.getSelectionEnd()).split("\t")
            self.imp.setSlice(int(frame)+1)
    
    def setAnaphase(self):
        frame, Distance, x = self.getLine(self.getSelectionEnd()).split("\t")
        #set anaphase onset
        self.cell.setAnOn(frame)
        for i in range(self.getLineCount()):   # very unelegantly solved, but it works.
            blFr, blDist, blAOCol = self.getLine(i).split("\t")
            self.setLine(i, blFr + "\t" + blDist + "\t")
            frame, distance, AOCol = self.getLine(self.getSelectionEnd()).split("\t") # get old line
            self.setLine(self.getSelectionEnd(), frame + "\t" + distance + "\tX")
        # setFocus back to tw,tp
        self.mF.setSaveActive()
        print "Anaphase set to", self.cell.getAnOn()

    def delVal(self):
        frame, distance, AOCol = self.getLine(self.getSelectionEnd()).split("\t")
        self.setLine(self.getSelectionEnd(), frame + "\tNA" + "\t" + AOCol)

    # - other methods
    def openImp(self, path):
        imp = ImagePlus(path)  # open associated tif file
        imp.show()
        imp.getWindow().setLocationAndSize(280, 120, imp.getWidth()*4, imp.getHeight()*4) # int x, int y, int width, int height
        return imp

    def getImp(self):
        return self.imp

    def getXYZtable(self):
        return self.XYZtable
        
    def closeWindows(self):
        self.imp.close()
        WindowManager.removeWindow(self.window)
        self.window.dispose()


# - - - M A I N - - -
random.seed()
mF = MenueFrame()

