# -*- coding: UTF8 -*-
import os
import sys
import struct
import pickle
from PIL import Image 
import numpy
from scipy.misc import toimage, fromimage

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data') 
COLORMAPS = pickle.load(file(os.path.join(DATA_DIR, 'colormaps.data')))

# Modify default colormap to add overloaded pixel effect
COLORMAPS['gist_yarg'][-1] = 0
COLORMAPS['gist_yarg'][-2] = 0
COLORMAPS['gist_yarg'][-3] = 255
GAMMA_SHIFT = 3.5        

def stretch(gamma):
    # histogram stretching
    lut = numpy.zeros(65536, dtype=numpy.uint)
    lut[65280:] = 255
    for i in xrange(65280):
        v = int(i*gamma)
        if v >= 255:
            lut[i] = 254
        else:
            lut[i] = v
    return lut
        
def _read_marccd_header(filename):
    # Read MarCCD header and calculate gamma
    
    header_format = 'I16s39I80x' # 256 bytes
    statistics_format = '3Q7I9I40x128H' #128 + 256 bytes
    goniostat_format = '28i16x' #128 bytes
    detector_format = '5i9i9i9i' #128 bytes
    source_format = '10i16x10i32x' #128 bytes
    file_format = '128s128s64s32s32s32s512s96x' # 1024 bytes
    dataset_format = '512s' # 512 bytes
    image_format = '9437184H'
    
    marccd_header_format = header_format + statistics_format 
    marccd_header_format +=  goniostat_format + detector_format + source_format 
    marccd_header_format +=  file_format + dataset_format + '512x'
    myfile = open(filename,'rb')
    
    tiff_header = myfile.read(1024)
    header_pars = struct.unpack(header_format, myfile.read(256))
    statistics_pars = struct.unpack(statistics_format,myfile.read(128+256))
    goniostat_pars  = struct.unpack(goniostat_format,myfile.read(128))
    detector_pars = struct.unpack(detector_format, myfile.read(128))
    source_pars = struct.unpack(source_format, myfile.read(128))
    file_pars = struct.unpack(file_format, myfile.read(1024))
    dataset_pars = struct.unpack(dataset_format, myfile.read(512))
    
    # extract some values from the header and calculate gamma
    average_intensity = statistics_pars[5] / 1e3
    if average_intensity < 0.1:
        gamma = 1.0
    else:
        gamma = 29.378 * average_intensity**-0.86
    myfile.close()
    return gamma
       
def _read_marccd_image(filename, gamma_offset = 0.0, resolution=(1024,1024)):
    # Read file and return an PIL image of desired resolution histogram stretched by the 
    # requested gamma_offset

    raw_img = Image.open(filename)    
    gamma = _read_marccd_header(filename)
    disp_gamma = gamma * numpy.exp(-gamma_offset + GAMMA_SHIFT)/30.0
    raw_img = raw_img.convert('I')
    lut = stretch(disp_gamma)
    raw_img = raw_img.point(lut,'L')
    raw_img.putpalette(COLORMAPS['gist_yarg'])
    return raw_img.resize(resolution, Image.ANTIALIAS) # slow but nice Image.NEAREST is very fast but ugly
         
def create_png(filename, output, brightness, resolution=(1024,1024)):
    # generate png in output using filename as input with specified brightness
    # and resolution. default resolution is 1024x1024
    # creates a directory for output if none exists

    try:   
        img_info = _read_marccd_image(filename, brightness, resolution)
    except:
        raise OSError
    dir_name = os.path.dirname(output)
    if not os.path.exists(dir_name) and dir_name != '':
        os.makedirs(dir_name)
    img_info.save(output, 'PNG')
    
if __name__ == '__main__':
    if os.path.exists('test_001.img'):
        create_png('test_001.img', 'test_001-nm.png', 0.0)
    else:
        print "Requires a 16bit Tiff diffraction image file called 'test_001.img'."
