from javax.swing import JButton, JFrame, JPanel, JLabel, JTextArea, JScrollPane, JProgressBar, SwingConstants, WindowConstants, JRadioButton, ButtonGroup
from java.awt import Component, GridLayout
from java.awt.event import ActionListener
import re, random, os, sys, glob
from java.awt.event import KeyEvent, KeyAdapter, MouseEvent, MouseAdapter
from ij.plugin import Zoom
from ij import WindowManager, IJ, ImagePlus
from ij.text import TextWindow, TextPanel
from ij.io import DirectoryChooser



# go through frames with arrowleft ()
# 0: anaphase Onset
# q: delete measurement


G_SAVESUBDIR = "qc-meas"
G_OPENSUBDIR = "meas"
PositionsTable = []

def bigRound(x, base):
    return int(base * round(float(x)/base))


def quit(event):
    try:
       meas.closeWindows()
    finally:
       WindowManager.removeWindow(mF.frame)
       mF.frame.dispose()
   
def openE(event):
    meas.closeWindows()
    meas.measure()

def openRandom(event):      # when click here: get random cell and meas.measure(tsv, tif, savePath)
    if mF.getMainDir() == "":
        mainDir = DirectoryChooser("Random QC - Please choose main directory containing ctrl and test folders").getDirectory()
        mF.setMainDir(mainDir)
        print "Setting new main dir to", mainDir
    try:
        meas.closeWindows()
    finally:
        inFiles = glob.glob(os.path.join(mF.getMainDir(),"*", G_OPENSUBDIR ,"val_*.csv"))  # glob.glob returns list of paths
        uncheckedCells = [cell(tsvPath) for tsvPath in inFiles if cell(tsvPath).processed == False]
        if len(uncheckedCells) > 0:
            randomCell = random.choice(uncheckedCells)
            mF.setProgBarMax(len(inFiles)-1)
            mF.setProgBarVal(len(inFiles)-len(uncheckedCells))
            meas.measure(randomCell)
        else:
            print "All cells measured!"

def changeFrame(tp):
    imp = IJ.getImage()     # wrong. how can I propagate the imp of meas?
    if tp.getSelectionEnd() >= 0:
        frame, dist, AOCol = tp.getLine(tp.getSelectionEnd()).split("\t")
        imp.setSlice(int(frame))


class ListenToKey(KeyAdapter):
    def keyPressed(this, event):
        eventSrc = event.getSource()
        tp = eventSrc.getParent() #panel is the parent, canvas being component.
        if event.getKeyCode() == 37 and tp.getSelectionEnd() > 0:    # KeyCode 37 : arrowLeft
            tp.setSelection(tp.getSelectionEnd()-1, tp.getSelectionEnd()-1)
        if event.getKeyCode() == 39 and tp.getSelectionEnd() < tp.getLineCount(): # KeyCode 39 : arrowRight
            tp.setSelection(tp.getSelectionEnd()+1, tp.getSelectionEnd()+1)
        changeFrame(tp)
        if event.getKeyCode() == 48:      # Anaphase Onset Def. KeyCode 48 : 0
            setAnaphase(tp, event)
            meas.tw.toFront()
        if event.getKeyCode() == 81:                # KeyCode 81: q
            delVal(tp, event)
        # Prevent further propagation of the key event:
        keyEvent.consume()

class ListenToMouse(MouseAdapter):
    def mouseClicked(this, event):
        tp = event.getSource().getParent()
        changeFrame(tp)

class Rbal(ActionListener):
    def actionPerformed(self, e):
        mF.setSaveActive()


class cell(object):
    def __init__(self, tsvPath):
        self.tsvPath = tsvPath
        self.openDir, self.filename = os.path.split(self.tsvPath)
        tsvRE = re.compile( os.path.join('(?P<mainDir>.*)', '(?P<strain>.*)', G_OPENSUBDIR ,'val_p(?P<position>\d+)_c(?P<cell>\d+).csv') )    
        pathMO = re.match(tsvRE, tsvPath)
        self.mainDir = pathMO.group('mainDir')
        self.strain = pathMO.group('strain')
        self.position = int(pathMO.group('position'))
        self.cellNo = int(pathMO.group('cell'))
        self.tifPath = os.path.join(self.openDir, "zi_p%i_c%i.tif" %(self.position, self.cellNo))
        self.savePath = os.path.join(self.mainDir, self.strain, G_SAVESUBDIR, "qc_val_p%i_c%i.csv") %(self.position, self.cellNo)
        self.isProcessed()
        self.anOn = None
        self.annotation = None

    def isProcessed(self):
        if os.path.exists(self.savePath):
            self.processed = True
        else:
            self.processed = False

    def hasTif(self):
        if os.path.exists(self.tifPath):
            self.processed = True
        else:
            self.processed = False

    def setAnOn(self, anOn):
        self.anOn = anOn
      

class MenueFrame(object): # should extend JFrame
    def __init__(self):
        self.mainDir = ""
   
        self.frame = JFrame("Dots Quality Check", size=(250,300))
        self.frame.setLocation(20,120)
        self.Panel = JPanel(GridLayout(0,1))
        self.frame.add(self.Panel)

        self.openNextButton = JButton('Open Next Random', actionPerformed=openRandom)
        self.Panel.add(self.openNextButton)
      
        self.saveButton = JButton('Save', actionPerformed=save, enabled=False)
        self.Panel.add(self.saveButton)

        self.cropButton = JButton('Crop values from here', actionPerformed=cropVals)
        self.Panel.add(self.cropButton)

        self.DiscardButton = JButton('Discard cell', actionPerformed=discardCell, enabled=True)
        self.Panel.add(self.DiscardButton)

        self.quitButton = JButton('Quit script',actionPerformed=quit)
        self.Panel.add(self.quitButton)

        annoPanel = JPanel()
        #add gridlayout
        wtRButton = JRadioButton("wt", actionCommand="wt")
        wtRButton.addActionListener(Rbal())
        defectRButton = JRadioButton("Defect", actionCommand="defect", actionPerformed=self.setSaveActive)
        defectRButton.addActionListener(Rbal())
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
      
        WindowManager.addWindow(self.frame)
        self.show()

    def getAnnotation(self):
        return self.aButtonGroup.getSelection().getActionCommand()

    def show(self):
        self.frame.visible = True

    def getFrame(self):
        return self.frame

    def setSaveActive(self):
        if (self.getAnnotation() != None and meas.getAnOn() != None):
            self.saveButton.setEnabled(True)
            self.show()

    def setSaveInactive(self):
        self.saveButton.setEnabled(False)
        self.show()

    def setMainDir(self, path):
        self.mainDir = path
        self.pathLabel.setText("MainDir: " + os.path.basename(os.path.split(self.mainDir)[0]))

    def getMainDir(self):
        return self.mainDir

    def setProgBarMax(self, maximum):
        self.ProgBar.setMaximum(maximum)

    def setProgBarVal(self, value):
        self.ProgBar.setValue(value)

    def close():
        WindowManager.removeWindow(self.frame)
        self.frame.dispose()     

class Measurer:
    "class contains the table (TextWindow and TextPanel) and imp for"
    def __init__(self):
        self.anOn = None
      
    def measure(self, cell):
        self.cell = cell
        self.imp = self.openImp(cell.tifPath)
        self.tw = self.openTW(cell.tsvPath)
        self.tp = self.tw.getTextPanel()
        self.tp.addKeyListener(ListenToKey())
        self.tp.addMouseListener(ListenToMouse())
        self.tp.setSelection(0,0) # int startLine, int endLine
        frame, distance, AO = self.tp.getLine(self.tp.getSelectionEnd()).split("\t")
        self.imp.setSlice(int(frame))
        mF.setSaveInactive()
        # here: putFocus on tw
        # arrange Windows properly!

    def openImp(self, path):
        imp = ImagePlus(path)  # open associated tif file
        imp.show()
        imp.getWindow().setLocationAndSize(280, 120, imp.getWidth()*4, imp.getHeight()*4) # int x, int y, int width, int height
        return imp

    def openTW(self, openPath_tsv):
        txtfile = open(openPath_tsv)
        heads = txtfile.readlines(1)[0].split(",")
        tw = TextWindow("Results", heads[0]+"\t"+heads[2]+"\t Anaphase", "", 50, 500)
        for line in txtfile.readlines():      # load file lines in textPanel.
            frame, timepoint, dist, ch0x, ch0y, ch0z, ch0vol, ch1x, ch1y, ch1z, ch1vol = line.split(",")
            tw.append(frame + "\t" + dist + "\t" )
            PositionsTable.append((ch0x, ch0y, ch0z, ch0vol, ch1x, ch1y, ch1z, ch1vol))
        return tw

    def getCell(self):
        return self.cell

    def getImp(self):
        return self.imp

    def getTw(self):
        return self.tw

    def setAnOn(self, anOn):
        self.anOn = anOn

    def getAnOn(self):
        return self.anOn

    def closeWindows(self):
        self.imp.close()
        self.tw.close()


def setAnaphase(tp, event):
    anOn, anOnDistance, AOCol = tp.getLine(tp.getSelectionEnd()).split("\t")
    print "Setting anaphase onset to frame " + anOn
    meas.setAnOn(anOn)
   
    for i in range(tp.getLineCount()):   # very unelegantly solved, I admit. but it works.
        blFr, blDist, blAOCol = tp.getLine(i).split("\t")
        tp.setLine(i, blFr + "\t" + blDist + "\t")
        frame, distance, AOCol = tp.getLine(tp.getSelectionEnd()).split("\t") # get old line
        tp.setLine(tp.getSelectionEnd(), frame + "\t" + distance + "\tX")
    # setFocus back to tw,tp
    
    mF.setSaveActive()

def delVal(tp, event):
    frame, distance, AOCol = tp.getLine(tp.getSelectionEnd()).split("\t")
    tp.setLine(tp.getSelectionEnd(), frame + "\tNA" + "\t" + AOCol)

def cropVals(event): #"this function deletes all values with frame > current cursor"   
    print meas.tp.getLineCount()
    for line in range(meas.tp.getSelectionEnd(), meas.tp.getLineCount(), 1):
        frame, distance, AOCol = meas.tp.getLine(line).split("\t")
        #print line
        meas.tp.setLine(line, frame + "\tNA" + "\t" + AOCol)

def save(event):
    anaphase = meas.getAnOn()
    timeInterval = meas.getImp().getCalibration().frameInterval
    annotation = mF.getAnnotation()
    position = str(meas.cell.position)
    cellIndex = str(meas.cell.cellNo)
    print anaphase, timeInterval, annotation, position, cellIndex
    if not os.path.exists(os.path.split(meas.cell.savePath)[0]): # check if save folder present.
        os.makedirs(os.path.split(meas.cell.savePath)[0]) # create save folder, if not present
    f = open(meas.cell.savePath ,"w")
    # Position Cell Phenotype Frame Time AnOn Distance ch0x ch0y ch0z ch0vol ch1x ch1y ch1z ch1vol
    f.write("Position,Cell,Phenotype,Frame,Time,Anaphase,Distance,ch0x,ch0y,ch0z,ch0vol,ch1x,ch1y,ch1z,ch1vol\n")
    for i in range(meas.tp.getLineCount()):
        frame, distance, a = meas.tp.getLine(i).split("\t")
        corrFrame = str(int(frame)-int(anaphase))
        time = "%.f" % (round(timeInterval) * int(corrFrame))
        if distance == "NA":
            ch0x, ch0y, ch0z, ch0vol, ch1x, ch1y, ch1z, ch1vol = "NA," * 7 + "NA"
        else:
            ch0x, ch0y, ch0z, ch0vol, ch1x, ch1y, ch1z, ch1vol = PositionsTable[i]
        f.write(position+","+cellIndex+","+annotation+","+corrFrame+","+time+","+anaphase+","+distance+","+ch0x+","+ch0y+","+ch0z+","+ch0vol+","+ch1x+","+ch1y+","+ch1z+","+ch1vol)
    f.close()
    print "Successfully saved ", meas.cell.savePath

def discardCell(event):
    if not os.path.exists(os.path.split(meas.cell.savePath)[0]): # check if save folder present.
        os.makedirs(os.path.split(meas.cell.savePath)[0]) # create save folder, if not present.
    f = open(meas.cell.savePath ,"w")
    # Position Cell Phenotype Frame Time AnOn Distance ch0x ch0y ch0z ch0vol ch1x ch1y ch1z ch1vol
    f.write("Position,Cell,Phenotype,Frame,Time,AnOn,Distance,ch0x,ch0y,ch0z,ch0vol,ch1x,ch1y,ch1z,ch1vol\n")
    f.close()
    print "Discarded cell - saved dummy" 

# - - - M A I N - - -
random.seed()
mF = MenueFrame()
meas = Measurer()

