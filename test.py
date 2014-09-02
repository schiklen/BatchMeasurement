from ij import WindowManager


class fr:
    def __init__(self, frame, distance, ch0Dotlist, ch1Dotlist):
       self.frame = frame
       self.distance = distance
       self.ch0Dotlist = ch0Dotlist
       self.ch1DotList = ch1Dotlist

class dot(object):
    def __init__(self, ch, frame, dotID, vol, x, y, z, intden):
        self.ch = ch
        self.frame = frame
        self.dotID = dotID
        self.vol = vol
        self.pos = (x, y, z)

    def getFrame(self):
        return self.frame
        
    def getVol(self):
        return self.vol

def tableToDots(lines, ch):
    dotList = []
    for l in lines[1:len(lines)-1]: #skip first line because its the col headings
        i, frame, dotID, vol, x, y, z, intden = l.split("\t")
        dotList.append(dot(ch, frame, dotID, vol, x, y, z, intden))
    return dotList


distance_lines = WindowManager.getFrame("Statistics_Distance").getTextPanel().getText().split("\n")
ch0_dots = tableToDots(WindowManager.getFrame("Statistics_Ch0").getTextPanel().getText().split("\n"), 0)
ch1_dots = tableToDots(WindowManager.getFrame("Statistics_Ch1").getTextPanel().getText().split("\n"), 1)

mainTable = []

for l in distance_lines[1:len(distance_lines)-1]:
    index, frame, distance, ch0dist, ch1dist, ch0vol, ch1vol = l.split("\t")
    # find respective frame in ch0 dot list
    dotCh0 = [d for d in ch0_dots if (d.getFrame() == frame and d.getVol() == ch0vol)][0]
    dotCh1 = [d for d in ch1_dots if (d.getFrame() == frame and d.getVol() == ch1vol)][0]
    
    mainTable.append(fr(frame, distance, dotCh0, dotCh1))

# write it to file.




