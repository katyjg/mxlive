import os
import tarfile

def create_tar(path, tar_file):
    # make a gzipped tar archive of path in file specified by the full path 'tar_file'
    
    dir_name = os.path.dirname(tar_file)
    root = os.path.dirname(path)
    base = os.path.basename(path)
    os.chdir(root)
    if not os.path.exists(dir_name) and dir_name != '':
        os.makedirs(dir_name)
    tar = tarfile.open(tar_file, "w:gz")
    tar.add(base)
    tar.close()

