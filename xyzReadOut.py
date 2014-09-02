from ij import WindowManager


class fr:
    def __init__(self, frame, distance, ch0Dotlist, ch1Dotlist):
        self.frame = int(float(frame))
        self.distance = float(distance)
        self.ch0Dotlist = ch0Dotlist
        self.ch1DotList = ch1Dotlist

    def __repr__(self): # defines the print output.
        return "Frame " + str(self.frame)

    #def __cmp__(self): # defines sorting criterium
        #return self.frame


    def getFrame(self):
        return self.frame

class dot(object):
    def __init__(self, ch, frame, dotID, vol, x, y, z, intden):
        self.ch = ch
        self.frame = int(float(frame))
        self.dotID = int(float(dotID))
        self.vol = int(float(vol))
        self.pos = (float(x), float(y), float(z))

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

def dotListToSingle(dotList):
    if len(dotList) == 1:
       return dotList.pop()
    if len(dotList) == 0:
       return None


# M A I N --------------------
distance_lines = WindowManager.getFrame("Statistics_Distance").getTextPanel().getText().split("\n")
ch0_dots = tableToDots(WindowManager.getFrame("Statistics_Ch0").getTextPanel().getText().split("\n"), 0)
ch1_dots = tableToDots(WindowManager.getFrame("Statistics_Ch1").getTextPanel().getText().split("\n"), 1)

frameList = []
for l in distance_lines[1:len(distance_lines)-1]:
    index, frame, distance, ch0dist, ch1dist, ch0vol, ch1vol = l.split("\t")
    # find respective frame in ch0 and ch1 dot list. Problem, if both dots have same volume.
    dotCh0 = dotListToSingle( [d for d in ch0_dots if (d.getFrame() == frame and d.getVol() == ch0vol)] )
    dotCh1 = dotListToSingle( [d for d in ch1_dots if (d.getFrame() == frame and d.getVol() == ch1vol)] )
    
    frameList.append(fr(frame, distance, dotCh0, dotCh1))

# fill up table with unsegmented frames.
presentFrames = [f.getFrame() for f in frameList]
missingFrames = [f for f in range(max(presentFrames)) if f not in presentFrames]

for f in missingFrames:
    frameList.append(fr(f, None, None, None))
    
print frameList
#sort by frame

# write to file.




