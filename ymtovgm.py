import sys
import os
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
    
def appendGD3String(data, toAppend):
    stringBytes = toAppend.encode("utf-8")
    stringBytes += b"\0" # add terminating 0
    newStringBytes = [0] * (len(stringBytes) * 2)
    newStringBytes[::2] = stringBytes # nifty way to intersperse zeroes after every element
    data += list(newStringBytes)

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
vgmOutput = []
numFrames = 0
framerate = 50 # Defaults to 50 hz if it's not specified
chipClockspeed = 2000000 # Defaults to 2MHz (Atari ST) if it's not specified
loopFrame = 0 # 0 = No loop.
loopOffset = 0
songName = ""
authorName = ""
songComment = ""
if fileHeader == fileTypes.YM2_3: # Contains no header data, other than "YM3!". Interlaced, with no R14 or R15 data.
    print ("File type is YM2 or YM3")
    print ("WARNING: File lacks clockspeed/framerate data, assuming a 50Hz Atari ST")
    numFrames = (len(data) - 4) / 14
elif fileHeader == fileTypes.YM3b: # Same as YM3, but the last 32 bits of the file contain the loop point
    print ("File type is YM3b")
    print ("WARNING: File lacks clockspeed/framerate data, assuming a 50Hz Atari ST")
    # Header = 4 bytes, loop point = 4 bytes
    numFrames = int((len(data) - 4 - 4) / 14)
    # the loop frame in ym3b is little endian, for some reason???
    loopFrame = (data[len(data) - 1] << 24) | (data[len(data) - 2] << 16) | (data[len(data) - 3] << 8) | data[len(data) - 4]
if fileHeader == fileTypes.YM2_3 or fileHeader == fileTypes.YM3b:
    prevFrameData = [None, None, None, None, None, None, None, None, None, None, None, None, None, None]
    for i in range(0, numFrames):
        if (i == loopFrame) and (loopFrame != 0):
            loopOffset = len(vgmOutput)
        for r in range(0, 14):
            regData = data[int(i + 4 + (r * numFrames))]
            if not (r == 13 and regData == 0xFF): # If register 13 is FF, it remains unchanged
                # Don't bother changing a reg if it already has that value
                # Reg 13 is different, writing to it triggers something, I think?
                if (not r == 13) and (regData == prevFrameData[r]):
                    continue
                vgmOutput.append(0xA0) # AY-3-8910 register set
                vgmOutput.append(r) # register num
                vgmOutput.append(regData)
                prevFrameData[r] = regData
        if framerate == 50:
            vgmOutput.append(0x63) # 50Hz wait
        elif framerate == 60:
            vgmOutput.append(0x62) # 60Hz wait
    vgmOutput.append(0x66) # End of Sound Data
elif fileHeader == fileTypes.YM5_6: # Contains a much more extensive header.
    print ("File type is YM5 or YM6")
    # NOTE: YM uses big-endian, for some reason.
    numFrames = (data[12] << 24) | (data[13] << 16) | (data[14] << 8) | data[15]
    songAttributes = (data[16] << 24) | (data[17] << 16) | (data[18] << 8) | data[19]
    numDigidrumSamples = (data[20] << 8) | data[21]
    chipClockspeed = (data[22] << 24) | (data[23] << 16) | (data[24] << 8) | data[25]
    framerate = (data[26] << 8) | data[27]
    loopFrame = (data[28] << 24) | (data[29] << 16) | (data[30] << 8) | data[31]
    
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
    while not data[songOffset] == 0:
        songName += chr(data[songOffset])
        songOffset += 1
    songOffset += 1
    while not data[songOffset] == 0:
        authorName += chr(data[songOffset])
        songOffset += 1
    songOffset += 1
    while not data[songOffset] == 0:
        songComment += chr(data[songOffset])
        songOffset += 1
    songOffset += 1
    sys.exit()
    
# Add the GD3 footer
gd3Location = len(vgmOutput)
vgmOutput.append(ord("G"))
vgmOutput.append(ord("d"))
vgmOutput.append(ord("3"))
vgmOutput.append(ord(" "))
vgmOutput.append(0x00)
vgmOutput.append(0x01)
vgmOutput.append(0x00)
vgmOutput.append(0x00)
gd3SizeLocation = len(vgmOutput)
vgmOutput.append(0x00) # Placeholder for GD3 size
vgmOutput.append(0x00)
vgmOutput.append(0x00)
vgmOutput.append(0x00)
appendGD3String(vgmOutput, songName) # English song name
appendGD3String(vgmOutput, "") # Japanese song name
appendGD3String(vgmOutput, "") # English game name
appendGD3String(vgmOutput, "") # Japanese game name
appendGD3String(vgmOutput, "") # English system name
appendGD3String(vgmOutput, "") # Japanese system name
appendGD3String(vgmOutput, authorName) # English author name
appendGD3String(vgmOutput, "") # Japanese author name
appendGD3String(vgmOutput, "") # Game release date
appendGD3String(vgmOutput, "Quinn") # VGM creator name
appendGD3String(vgmOutput, songComment + "(Converted using Quinn's YMtoVGM converter)") # Notes
gd3Size = len(vgmOutput) - (gd3SizeLocation + 4)
vgmOutput[gd3SizeLocation] = gd3Size & 0xFF
vgmOutput[gd3SizeLocation + 1] = (gd3Size >> 8) & 0xFF
vgmOutput[gd3SizeLocation + 2] = (gd3Size >> 16) & 0xFF
vgmOutput[gd3SizeLocation + 3] = (gd3Size >> 24) & 0xFF
    
# Add the VGM header
samplesPerFrame = 0
if framerate == 50:
    samplesPerFrame = 882
elif framerate == 60:
    samplesPerFrame = 735
for i in range(0, 0x80):
    vgmOutput.insert(0, 0)
vgmOutput[0x0] = ord("V")
vgmOutput[0x1] = ord("g")
vgmOutput[0x2] = ord("m")
vgmOutput[0x3] = ord(" ")
eofOffset = len(vgmOutput) - 4
vgmOutput[0x4] = eofOffset & 0xFF
vgmOutput[0x5] = (eofOffset >> 8) & 0xFF
vgmOutput[0x6] = (eofOffset >> 16) & 0xFF
vgmOutput[0x7] = (eofOffset >> 24) & 0xFF
vgmOutput[0x8] = 0x51 # Saving as VGM version 1.51
vgmOutput[0x9] = 0x01
vgmOutput[0xA] = 0x00
vgmOutput[0xB] = 0x00
gd3Location = (gd3Location + 0x80) - 0x14
vgmOutput[0x14] = gd3Location & 0xFF
vgmOutput[0x15] = (gd3Location >> 8) & 0xFF
vgmOutput[0x16] = (gd3Location >> 16) & 0xFF
vgmOutput[0x17] = (gd3Location >> 24) & 0xFF
totalSamples = numFrames * samplesPerFrame
vgmOutput[0x18] = totalSamples & 0xFF
vgmOutput[0x19] = (totalSamples >> 8) & 0xFF
vgmOutput[0x1A] = (totalSamples >> 16) & 0xFF
vgmOutput[0x1B] = (totalSamples >> 24) & 0xFF
if loopFrame != 0:
    loopOffset = (loopOffset + 0x80) - 0x1C
    vgmOutput[0x1C] = loopOffset & 0xFF
    vgmOutput[0x1D] = (loopOffset >> 8) & 0xFF
    vgmOutput[0x1E] = (loopOffset >> 16) & 0xFF
    vgmOutput[0x1F] = (loopOffset >> 24) & 0xFF
    loopSamples = (numFrames - loopFrame) * samplesPerFrame
    vgmOutput[0x20] = loopSamples & 0xFF
    vgmOutput[0x21] = (loopSamples >> 8) & 0xFF
    vgmOutput[0x22] = (loopSamples >> 16) & 0xFF
    vgmOutput[0x23] = (loopSamples >> 24) & 0xFF
vgmDataOffset = 0x4C # Data starts at 0x80, 0x80 - 0x34 = 0x4C
vgmOutput[0x34] = vgmDataOffset & 0xFF
vgmOutput[0x35] = (vgmDataOffset >> 8) & 0xFF
vgmOutput[0x36] = (vgmDataOffset >> 16) & 0xFF
vgmOutput[0x37] = (vgmDataOffset >> 24) & 0xFF
vgmOutput[0x74] = chipClockspeed & 0xFF
vgmOutput[0x75] = (chipClockspeed >> 8) & 0xFF
vgmOutput[0x76] = (chipClockspeed >> 16) & 0xFF
vgmOutput[0x77] = (chipClockspeed >> 24) & 0xFF
vgmOutput[0x78] = 0x10 # AY-3-8910 Type = YM2149
vgmOutput[0x79] = 0x01 # AY-3-8910 Single Output (not sure what this means, but single output works)
f = open(os.path.splitext(sys.argv[1])[0] + ".vgm", "wb+")
f.write(bytearray(vgmOutput))
f.close()
print("Successfully converted")