import os
from download.views import get_download_path

from django import template  
register = template.Library()  
 
@register.filter("get_ls")  
def get_ls(url, excludes=[]):
    suff = ['cbf','pck','com']
    for f in ['XDS.INP','XSCALE.INP','XDSCONV.INP']:
        excludes.append(f)
    try:
        return sorted([x for x in os.listdir(get_download_path(url)) if x not in excludes and (len(x.split('.')) > 1 and x.split('.')[1] not in suff)])
    except OSError:
        return []
    

