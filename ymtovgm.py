# Requirements : Python 3, lhafile
# Arg 1 = File to convert

import sys
from lhafile import LhaFile, BadLhafile

def invalidFile():
    print ("Invalid input file: " + sys.argv[1])
    sys.exit()

if (len(sys.argv) < 2):
    print("Not enough arguments!");
    sys.exit()

try:
    f = open(sys.argv[1], 'rb')
except FileNotFoundError:
    invalidFile()
data = f.read()
f.close()
if not (data[0] == b'Y' and data[1] == b'M'): # File isn't already decompressed
    # Read first file out of archive (they only ever have 1 file)
    try:
        archive = LhaFile(sys.argv[1])
    except BadLhafile:
        invalidFile()
    data = archive.read(archive.infolist()[0].filename)
    if not (data[0] == b'Y' and data[1] == b'M'):
        invalidFile()