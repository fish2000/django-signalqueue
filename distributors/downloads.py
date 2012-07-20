
from __future__ import print_function

from django.conf import settings
if not settings.configured:
    settings.configure(**dict())

import sys
import requests
import mimetypes
from os.path import dirname
from urlobject import URLObject as URL

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import FileSystemStorage
from django.core.files.move import file_move_safe
from django.utils._os import safe_join

class URLRequestFile(SimpleUploadedFile):
    
    DEFAULT_TYPE = 'text/plain'
    
    def __init__(self, url, filename, **kwargs):
        """ A URLRequestFile is created with a URL and a filename.
        The data from the URL is immediately fetched when one constructs
        a new URLRequestFile object -- exceptions are thrown in
        the event of failure. """
        
        self._source_url = url
        
        try:
            request = requests.get(url)
        except (
            requests.exceptions.TooManyRedirects,
            requests.exceptions.ConnectionError,
            requests.exceptions.SSLError,
            requests.exceptions.Timeout), err:
            print("*** Couldn't save %s to a file" % url,
                file=sys.stderr)
            print("*** (%s)" % err,
                file=sys.stderr)
            content = ''
        else:
            content = request.ok and request.content or ''
        
        content_type = request.ok and \
            request.headers.get('content-type') or \
            kwargs.pop('content_type',
                URLRequestFile.DEFAULT_TYPE)
        
        self._source_content_type = content_type
        self._source_encoding = request.ok and request.encoding or None
        
        super(URLRequestFile, self).__init__(
            filename, content, content_type)
        self.charset = self._source_encoding
    
    @property
    def source_url(self):
        return getattr(self, '_source_url', None)
    
    @property
    def source_content_type(self):
        return getattr(self, '_source_content_type', None)
    
    @property
    def source_encoding(self):
        return getattr(self, '_source_encoding', None)
    
    @property
    def source_charset(self):
        return self.source_encoding


class URLRetrievalStorage(FileSystemStorage):
    
    DEFAULT_EXT = '_noext.txt'
    MINIMUM_BYTE_SIZE = 10
    
    def _extension(self, mime_type=DEFAULT_EXT):
        """ Get the common-law file extension for a given MIME type."""
        exts = mimetypes.guess_all_extensions(mime_type)
        if '.jpe' in exts:
            exts.remove('.jpe') # WHO USES THAT.
        ext = bool(exts) and \
            exts[0] or \
            URLRetrievalStorage.DEFAULT_EXT
        return ext
    
    def download(self, urlstr, **kwargs):
        """ Call url_rs.download('URL') to save that URL's contents
        into a new file within the storages' filesystem.
        Optionally setting the 'clobber' keyword to False will raise
        an exception before overwriting existing data.
        Any other keyword args are passed wholesale to URLRequestFile's
        constructor when the new file is saved locally. """
        
        url = URL(urlstr)
        clobber = bool(kwargs.pop('clobber', True))
        
        try:
            headstat = requests.head(url)
        except (
            requests.exceptions.TooManyRedirects,
            requests.exceptions.ConnectionError,
            requests.exceptions.SSLError,
            requests.exceptions.Timeout), err:
            print("*** HTTP HEAD failed for %s" % url,
                file=sys.stderr)
            print("--- (%s)" % err,
                file=sys.stderr)
            return None
        
        ct = kwargs.pop('content_type',
            headstat.headers.get('content-type',
                URLRequestFile.DEFAULT_TYPE))
        if ';' in ct:
            ct = ct.split(';')[0]
        
        ext = self._extension(ct)
        fn = "%s%s" % (url.hash, ext)
        ff = URLRequestFile(url, fn, **kwargs)
        #print('ext/ct',ext,ct)
        
        if self.exists(fn) and not clobber:
            raise IOError(
                "*** Can't overwrite existing file %s (clobber=%s)" % (fn, clobber))
        
        if ff.size < URLRetrievalStorage.MINIMUM_BYTE_SIZE:
            raise ValueError(
                "*** Bailing -- ownloaded data is less than URLRetrievalStorage.MINIMUM_BYTE_SIZE (%sb)" %
                    URLRequestFile.MINIMUM_BYTE_SIZE)
        
        self.save(fn, ff)
        return ff
    
    def downloaded(self, urlstr, path=None):
        """ We say that a remote file has been 'downloaded' to a local directory
        if we can spot the SHA1 of its URL inside exactly one local filename. """
        
        path = self.path(path or '')
        oneornone = filter(
            lambda fn: fn.find(URL(urlstr).hash) > -1,
            self.listdir(path)[-1])
        
        if len(oneornone) is 1:
            one = oneornone[0]
            return bool(self.size(one)) and self.path(one) or None
        return None
    
    def local_content_type(self, urlstr, path=None):
        """ Guess an existant local file's mimetype from its
        corresponding remote URL... it sounds circuitous I know. """
        if self.exists(self.downloaded(urlstr, path)):
            return mimetypes.guess_type(urlstr)
    
    def safely_rename(self, url_request_file, new_name, clobber=False):
        """ Pass a URLRequestFile, with a new filename, to move or rename. """
        new_path = safe_join(
            dirname(self.path(url_request_file.name)),
            new_name)
        
        file_move_safe(
            self.path(url_request_file.name),
            new_path,
            allow_overwrite=clobber)
        
        url_request_file.name = new_name
    
    safely_move = safely_rename


if __name__ == "__main__":
    from pprint import pformat
    import tempfile
    td = tempfile.mkdtemp()
    fs = URLRetrievalStorage(
        location=td, base_url='http://owls.com/discount')
    
    stuff_to_grab = (
        'http://objectsinspaceandtime.com/',
        'http://objectsinspaceandtime.com/index.html',
        'http://objectsinspaceandtime.com/css/fn_typography.css',
        'http://scs.viceland.com/int/v17n11/htdocs/bright-lights-591/it-s-over.jpg',
        'http://yo-dogggggg.com/i-dont-exist')
    
    print('> directory:', td)
    print('> storage:', fs)
    print('')
    
    for thing in stuff_to_grab:
        print('-' * 133)
        print('')
        
        print('\t +++ URL: %s' % thing)
        
        ff = fs.download(thing)
        success = bool(fs.downloaded(thing))
        
        print('\t +++ success: %s' % str(success))
        
        if success:
            print('\t +++ local content/type (guess): %s' % fs.local_content_type(thing)[0])
            if ff is not None:
                print('\t +++ file object: %s' % ff)
                print('\t +++ path:', fs.path(ff.name))
                print('\t +++ FS url:', fs.url(ff.name))
                print('\t +++ orig URL:', ff.source_url)
                print('')
                print(pformat(ff.__dict__,
                    indent=8))
        
        print('')
    
    print('-' * 133)
    print('')
    
    yieldem = fs.listdir('')[-1]
    
    print('> fs.listdir(\'\')[-1] yields %s files:' % len(yieldem))
    print('')
    print(pformat(yieldem,
        indent=8))
    
    print('')
    print('')
