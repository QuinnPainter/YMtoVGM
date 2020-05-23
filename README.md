# YMtoVGM
Converts YM2149 files to the standard [VGM](https://vgmrips.net/wiki/VGM_Specification) format.
The .YM format is most commonly used for Atari ST chiptunes.
It's also sometimes used for Amstrad CPC tunes, and theoretically it can hold music from any computer with a YM2149 / AY-3-8910 soundchip.

## Requirements
- Python 3
- [lhafile](https://github.com/FrodeSolheim/python-lhafile) (`pip install lhafile`)

## Usage
```
usage: ymtovgm.py [-h] [-o <output>] [-c <clock>] [-r <rate>] input

positional arguments:
  input                 YM source file

optional arguments:
  -h, --help            show this help message and exit
  -o <output>, --output <output>
                        VGM output file (default is [input].vgm)
  -c <clock>, --clock <clock>
                        Clockspeed for files where it isn't specified (default
                        is 2000000Hz [Atari ST])
  -r <rate>, --rate <rate>
                        Sample rate for files where it isn't specified
                        (default is 50Hz)
```

## Supported YM file types
- YM2
- YM3
- YM3b
- YM5
- YM6

## Unsupported YM file types
- YM1, YM4 - Wouldn't be hard to add, but I can't find any files of these types.
- YMT - YM Tracker file. Entirely sample based, and I can't find info on it. Also pretty rare.
- MIX - Also sample based. No info available. Rather uncommon.

## Possible future improvements
- Doesn't support Atari ST specific sound effects e.g. digidrums