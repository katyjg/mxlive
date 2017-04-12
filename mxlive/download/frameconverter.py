# -*- coding: UTF8 -*-
import os
import pickle
import numpy
from PIL import Image
from imageio import read_image, read_header
from imageio.utils import stretch

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data') 
COLORMAPS = pickle.load(file(os.path.join(DATA_DIR, 'colormaps.data')))

# Modify default colormap to add overloaded pixel effect
COLORMAPS['gist_yarg'][-1] = 0
COLORMAPS['gist_yarg'][-2] = 0
COLORMAPS['gist_yarg'][-3] = 255
GAMMA_SHIFT = 3.5        


def load_image(filename, gamma_offset = 0.0, resolution=(1024,1024)):
    # Read file and return an PIL image of desired resolution histogram stretched by the 
    # requested gamma_offset

    image_obj = read_image(filename)
    gamma = image_obj.header['gamma']
    disp_gamma = gamma * numpy.exp(-gamma_offset + GAMMA_SHIFT)/30.0
    raw_img = image_obj.image.convert('I')
    lut = stretch(disp_gamma)
    raw_img = raw_img.point(list(lut),'L')
    raw_img.putpalette(COLORMAPS['gist_yarg'])
    return raw_img.resize(resolution, Image.ANTIALIAS) # slow but nice Image.NEAREST is very fast but ugly


def create_png(filename, output, brightness, resolution=(1024,1024)):
    # generate png in output using filename as input with specified brightness
    # and resolution. default resolution is 1024x1024
    # creates a directory for output if none exists

    img_info = load_image(filename, brightness, resolution)

    dir_name = os.path.dirname(output)
    if not os.path.exists(dir_name) and dir_name != '':
        os.makedirs(dir_name)
    img_info.save(output, 'PNG')


