#!/usr/bin/env python

from multiprocessing import Process,cpu_count
import Queue, time,os

"""
Get a list of raw files ending with ext
"""
def get_raws(ext):
    import os
    files = []
    for file in os.listdir("."):
        if file.endswith("."+ext):
            files.append(file)
    return files
extension = raw_input("Please enter raw extension\ndefault CR2\n   ").strip()
if len(extension) < 1:
    extension = "CR2"
filenames = get_raws(extension)
fname = filenames[0]
command = "dcraw -6 -W -g 1 1 -d -T -c "+ fname +" > " + "filter.tiff"
os.system(command)
