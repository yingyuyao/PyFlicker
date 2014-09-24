#!/usr/bin/env python

from multiprocessing import Process,cpu_count
import Queue, time, os, subprocess, shlex, StringIO

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



"""
Worker class for threading
!multi-threading doesn't seem to help much here
!disk write has a bottleneck
!just normalloop instead
"""
class Worker(Process):
    def __init__(self, queue, filter, percentile, expval):
        super(Worker, self).__init__()
        self.queue= queue
        self.filter = filter
        self.percentile = percentile
        self.expval = expval

    def run(self):
        import os
        print "worker started"
        for fname in iter(self.queue.get, None ):
            print fname
            tiffname = "/tmp/"+fname+".tiff"
            command = "dcraw -6 -W -g 1 1 -d -T -c "+ fname +" > " + tiffname
            os.system(command)

            exp = find_exp(fname,
                           percentile=self.percentile,
                           filter = self.filter)
            write_xmp(fname, exp, self.expval)

            os.remove(tiffname)

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
    print ">>Using filter.tiff"
filenames = get_raws(extension)
#print filenames



for fname in filenames:
    print "working with " + fname
    command = "dcraw -6 -W -g 1 1 -d -T -c " + fname
    p1 = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    imgbr = p1.communicate()[0]
    imgf = StringIO.StringIO(imgbr)
    
    exp = find_exp(imgf,
                   percentile=percentile,
                   filter = filter)
    write_xmp(fname, exp, target_exp)
            
"""
old multi-thread stuff

nworker = cpu_count()
request_queue = Queue.Queue()
worker_list = []

for fname in filenames:
    request_queue.put( fname )
for i in range(nworker):
    request_queue.put( None ) 
for i in range(nworker):
    Worker(request_queue,filter,percentile, target_exp).start()
    time.sleep(2.0)

"""
