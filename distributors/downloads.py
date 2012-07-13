
from __future__ import print_function

import os
import requests
import mimetypes
from urlobject import URLObject as URL

os.environ['DJANGO_SETTINGS_MODULE'] = os.environ.get(
    'DJANGO_SETTINGS_MODULE',
    'distributors.settings') or 'distributors.settings'

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import FileSystemStorage

class URLRequestFile(SimpleUploadedFile):
    
    DEFAULT_TYPE = 'text/plain'
    
    def __init__(self, url, filename, **kwargs):
        try:
            request = requests.get(url)
        except (
            requests.exceptions.TooManyRedirects,
            requests.exceptions.ConnectionError,
            requests.exceptions.SSLError,
            requests.exceptions.Timeout), err:
            print("*** Couldn't save %s to a file (%s)" % (url, err))
            content = ''
        else:
            content = request.ok and request.content or ''
        
        content_type = request.ok and \
            request.headers.get('content-type') or \
            kwargs.pop('content_type',
                URLRequestFile.DEFAULT_TYPE)
        
        super(URLRequestFile, self).__init__(
            filename, content, content_type)


class URLRetrievalStorage(FileSystemStorage):
    
    DEFAULT_EXT = '_noext.txt'
    
    def download(self, urlstr, **kwargs):
        url = URL(urlstr)
        
        try:
            headstat = requests.head(url)
        except (
            requests.exceptions.TooManyRedirects,
            requests.exceptions.ConnectionError,
            requests.exceptions.SSLError,
            requests.exceptions.Timeout), err:
            print("*** Headers for %s couldn't be retrieved (%s)" % (url, err))
            return None
        
        exts = mimetypes.guess_all_extensions(
            headstat.headers.get('content-type',
                kwargs.pop('content_type',
                    URLRequestFile.DEFAULT_TYPE)))
        
        if '.jpe' in exts:
            exts.remove('.jpe')
        ext = bool(exts) and \
            exts[0] or \
            URLRetrievalStorage.DEFAULT_EXT
        
        ff = URLRequestFile(url, url.hash, **kwargs)
        fn = "%s%s" % (url.hash, ext)
        
        self.save(fn, ff)
        return ff



if __name__ == "__main__":
    from pprint import pprint
    import tempfile
    td = tempfile.mkdtemp()
    fs = URLRetrievalStorage(location=td)
    
    stuff_to_grab = (
        'http://objectsinspaceandtime.com/',
        'http://objectsinspaceandtime.com/index.html',
        'http://objectsinspaceandtime.com/css/fn_typography.css',
        'http://scs.viceland.com/int/v17n11/htdocs/bright-lights-591/it-s-over.jpg',
        'http://yo-dogggggg.com/i-dont-exist')
    
    print('* directory:', td)
    print('* storage:', fs)
    print('')
    
    for thing in stuff_to_grab:
        print('+++ downloading from:', thing)
        ff = fs.download(thing)
        pprint(ff)
        print('')
    
    print('* listdir:')
    pprint(fs.listdir(''))

