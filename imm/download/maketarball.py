import os
import tarfile
import re

def create_tar(path, tar_file, data_dir=False):
    # make a gzipped tar archive of path in file specified by the full path 'tar_file'
    dir_name = os.path.dirname(tar_file)
    root = os.path.dirname(path)
    base = os.path.splitext(os.path.splitext(os.path.basename(tar_file))[0])[0]
    data_file_re = '(%s)_\d{3,4}.img$' % base
    #os.chdir(root)
    if not os.path.exists(dir_name) and dir_name != '':
        os.makedirs(dir_name)

    def get_data_files(filename):
        ''' If this function returns True, the filename will not 
            be included in the tar file. 
        '''
        if filename is path:
            return False
        return not re.search(data_file_re, filename.split(path)[1])

    tar = tarfile.open(tar_file, "w:gz")
    if data_dir:
        tar.add(path, base, exclude=get_data_files)
    else:
        tar.add(path, base)
    tar.close()

