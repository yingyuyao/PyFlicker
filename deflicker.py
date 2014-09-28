#!/usr/bin/env python

from multiprocessing import cpu_count
import Queue, time, os, subprocess, shlex, StringIO, threading

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

 
"""
get the exposure value for specific percentile
filter can be used to mask part of image
"""
def find_exp(imgf, percentile = 0.5, filter=None):
    import os
    from math import log
    import numpy as np
    import matplotlib.pyplot as plt
    
    img = plt.imread(imgf, format='tiff').flatten()
    total_size = len(img)
    if filter != None:
        filter = filter.flatten()
        img = np.multiply(img, filter)
        total_size = np.sum(filter)

    hist = np.histogram(img, bins=range(65536))[0]
    
    cum_sum = np.cumsum(hist[1:])/float(total_size)
    
    cum_sum = np.abs(cum_sum - percentile)

    
    return log(np.argmin(cum_sum)+1,2)-16

"""
get image filter
"""
def get_filter():
    import os
    import numpy as np
    import matplotlib.pyplot as plt
    if not os.path.isfile("filter.tiff"):
        return None
    img = plt.imread("filter.tiff").flatten()
    cut = np.max(img)/2+1
    img2 = img/cut
    return img2
def apply_cut(x,cut):
    if x > cut:
        return 1
    else:
        return 0

"""
write xmp for adobe
"""
def write_xmp(filename, expo, desired):
    fname = filename[:filename.rfind(".")]+".XMP"
    f = open(fname,'w')
    f.write('<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="pyLapse">\n')
    f.write(' <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n')
    f.write('  <rdf:Description rdf:about=""\n')
    f.write('    xmlns:dc="http://purl.org/dc/elements/1.1/"\n')
    f.write('    xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/"\n')
    f.write('    xmlns:crs="http://ns.adobe.com/camera-raw-settings/1.0/"\n')
    f.write('    photoshop:DateCreated="2050-01-01T00:00:00:00"\n')
    f.write('    photoshop:EmbeddedXMPDigest=""\n')
    f.write('    crs:ProcessVersion="6.7"\n')
    f.write('    crs:Exposure2012="%.4f">\n' % (desired-expo))
    f.write('    <dc:subject>\n')
    f.write('    <rdf:Bag>\n')
    f.write('     <rdf:li>pyLapse Deflicker</rdf:li>\n')
    f.write('    </rdf:Bag>\n')
    f.write('   </dc:subject>\n')
    f.write('  </rdf:Description>\n')
    f.write(' </rdf:RDF>\n')
    f.write('</x:xmpmeta>\n')




#Worker for threading


def worker():
    while True:
        rawname = request_queue.get()
        print "working with " + rawname
        command = ['dcraw', '-6', '-W', '-g', '1', '1', '-d', '-T', '-c', rawname]
        p1 = subprocess.Popen(command, stdout=subprocess.PIPE)
        imgbr = p1.communicate()[0]
        imgf = StringIO.StringIO(imgbr)
        
        exp = find_exp(imgf,
                       percentile=percentile,
                       filter = filter)
        write_xmp(rawname, exp, target_exp)
        request_queue.task_done()
            
extension = raw_input("Please enter raw extension\ndefault CR2\n   ").strip()
if len(extension) < 1:
    extension = "CR2"
print(">>Using *."+extension)

target_exp = raw_input("Please target EV\ndefault -3 \n0 is overexposure\n   ").strip()
if len(target_exp) <1:
    target_exp = -3
target_exp = float(target_exp)
print(">>Using " + str(target_exp) + " EV")


percentile = raw_input("Please target percentile\ndefault 50 \ni.e. midtones \n   ").strip()
if len(percentile) <1:
    percentile = 50
percentile = float(percentile)/100
print(">>Using " + str(percentile) + " percentile")



filter = get_filter()
if not filter==None:
    print(">>Using filter.tiff")
filenames = get_raws(extension)
#print filenames


nworker = cpu_count()
request_queue = Queue.Queue()
worker_list = []

for i in range(nworker):
    t = threading.Thread(target=worker)
    t.daemon = True
    t.start()
    
stime = time.clock()

for fname in filenames:
    request_queue.put( fname )

    
request_queue.join()

ftime = time.clock()

print("Spent a total of %.2f seconds on processing" % float(ftime-stime))
print("An average of %.4f sec per image(total of %d)" % (float(ftime-stime)/len(filenames),len(filenames)))

