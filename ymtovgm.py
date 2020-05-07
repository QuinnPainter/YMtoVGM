import sys
from lhafile import LhaFile, BadLhafile
from enum import Enum

# http://leonard.oxg.free.fr/ymformat.html
# https://github.com/skeezix/zikzak/blob/master/zik80/audio-gen/ym-file-format.txt
class fileTypes(Enum):
    Unsupported = 0 # YMT, MIX, YM4, and YM1.
    YM5_6 = 1
    YM2_3 = 2
    YM3b = 3
    Garbage = 4 # Either some totally wrong file, or one that is still compressed
    
def checkFileHeader(fileData):
    char1 = chr(fileData[0])
    char2 = chr(fileData[1])
    char3 = chr(fileData[2])
    char4 = chr(fileData[3])
    if char1 == "Y" and char2 == "M":
        if char3 == "1" or char3 == "4":
            print ("YM" + char3 + " files are not yet supported")
            return fileTypes.Unsupported
        elif char3 == "2":
            return fileTypes.YM2_3
        elif char3 == "3":
            if (char4 == "b"):
                return fileTypes.YM3b
            else:
                return fileTypes.YM2_3
        elif char3 == "5" or char3 == "6":
            return fileTypes.YM5_6
        elif char3 == "T":
            print ("YMT (YM Tracker) files are not supported")
            return fileTypes.Unsupported
    elif char1 == "M" and char2 == "I" and char3 == "X":
        print ("MIX files are not supported")
        return fileTypes.Unsupported
    return fileTypes.Garbage

if (len(sys.argv) < 2):
    print("Not enough arguments!")
    sys.exit()

try:
    f = open(sys.argv[1], 'rb')
except FileNotFoundError:
    print("File not found: " + sys.argv[1])
    sys.exit()
data = f.read()
f.close()
fileHeader = checkFileHeader(data)
if fileHeader == fileTypes.Garbage: # File isn't already decompressed
    try:
        archive = LhaFile(sys.argv[1])
    except BadLhafile:
        print ("Unable to decompress the file. Try decompressing it in 7Zip or another archive tool")
        sys.exit()
    # Read first file out of archive (they only ever have 1 file)
    data = archive.read(archive.infolist()[0].filename)
    fileHeader = checkFileHeader(data)
    if fileHeader == fileTypes.Garbage:
        print ("File was a valid LHA archive, but it didn't contain a valid YM file")
        sys.exit()
    elif fileHeader == fileTypes.Unsupported:
        print ("Error: Unsupported file type")
        sys.exit()
elif fileHeader == fileTypes.Unsupported:
    print ("Error: Unsupported file type")
    sys.exit()
if fileHeader == fileTypes.YM2_3:
    print ("File type is YM2 or YM3")
    sys.exit()
elif fileHeader == fileTypes.YM3b:
    print ("File type is YM3b")
    sys.exit()
elif fileHeader == fileTypes.YM5_6:
    print ("File type is YM5 or YM6")
        
# NOTE: YM uses big-endian, for some reason.
numberOfFrames = (data[12] << 24) | (data[13] << 16) | (data[14] << 8) | data[15]
songAttributes = (data[16] << 24) | (data[17] << 16) | (data[18] << 8) | data[19]
numDigidrumSamples = (data[20] << 8) | data[21]
YMClockspeed = (data[22] << 24) | (data[23] << 16) | (data[24] << 8) | data[25]
framerate = (data[26] << 8) | data[27]
loopFrame = (data[28] << 24) | (data[29] << 16) | (data[30] << 8) | data[31]
additionalData = (data[32] << 8) | data[33]

if numDigidrumSamples > 0:
    print ("WARNING: This file contains digidrum samples that won't be reproduced in the VGM")
if not (framerate == 50 or framerate == 60):
    print ("Framerate isn't 50 or 60. This should never happen? (it's " + str(framerate) + ")")
    sys.exit()

# Skip over the digidrum data
songOffset = 34
for i in range(0, numDigidrumSamples):
    sampleSize = (data[songOffset] << 24) | (data[songOffset + 1] << 16) | (data[songOffset + 2] << 8) | data[songOffset + 3]
    songOffset += 4 + sampleSize
    
songName = ""
while not data[songOffset] == 0:
    songName += chr(data[songOffset])
    songOffset += 1
songOffset += 1
    
authorName = ""
while not data[songOffset] == 0:
    authorName += chr(data[songOffset])
    songOffset += 1
songOffset += 1
    
songComment = ""
while not data[songOffset] == 0:
    songComment += chr(data[songOffset])
    songOffset += 1
songOffset += 1
    
#vgmOutput = []
#vgmOutput[256] = 0
#print (vgmOutput)