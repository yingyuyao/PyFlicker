#!/usr/bin/env python

from multiprocessing import Process

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
Convert specific file to linear 16bit tiff
using dcraw
"""
def convert_file(filename):
    import os
    command = "dcraw -6 -W -g 1 1 -d -T -c "+ filename +" > /tmp/"+filename+".tiff"
    os.system(command)

"""
get the exposure value for specific percentile
filter can be used to mask part of image
"""
def find_percentile(file, percentile = 0.5, filter=None):
    import os
    from math import log
    import numpy as np
    import matplotlib.pyplot as plt
    fname = file
    if not file.endswith(".tiff"):
        fname = file + ".tiff"
    fname = "/tmp/"+fname
    img = plt.imread(fname).flatten()
    total_size = len(img)
    if filter != None:
        filter = filter.flatten()
        img = np.multiply(img, filter)
        total_size = np.sum(filter)

    hist = np.histogram(img, bins=range(65536))[0]
    
    running_sum = 0

    for (i, pcount) in enumerate(hist[1:]):
        running_sum += pcount
        if float(running_sum)/float(total_size) > percentile:
            break

    i += 1
    
    os.remove(fname)
    return log(i,2)-16

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
    f.write('   photoshop:DateCreated="2050-01-01T00:00:00:00"\n')
    f.write('   photoshop:EmbeddedXMPDigest=""\n')
    f.write('   crs:ProcessVersion="6.7"\n')
    f.write('   crs:Exposure2012="%f.4">\n' % (desired-expo))
    f.write('   <dc:subject>\n')
    f.write('    <rdf:Bag>\n')
    f.write('     <rdf:li>pyLapse Deflicker</rdf:li>\n')
    f.write('    </rdf:Bag>\n')
    f.write('   </dc:subject>\n')
    f.write('  </rdf:Description>\n')
    f.write(' </rdf:RDF>\n')
    f.write('</x:xmpmeta>\n')



"""
Worker class for threading
"""
class Worker(Process):
    def __init__(self, queue):
        super(Worker, self).__init__()
        self.queue= queue

    def run(self):
        print 'Worker started'
        # do some initialization here

        print 'Computing things!'
        for data in iter( self.queue.get, None ):
            # Use data



filter = get_filter()
filename = get_raws("CR2")[0]
convert_file(filename)
write_xmp(filename, find_percentile(filename,filter = filter), -3)
