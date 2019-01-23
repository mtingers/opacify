#!/usr/bin/env python

import os
import sys
import argparse
import requests
import hashlib


CHUNK_SIZE = 24

class Opacify(object):
    def __init__(self):
        self.mode       = None
        self.input_path = None
        self.src_path   = None
        self.threads    = None
        self.save_path  = None
        self.manifest   = None


    def _cmp_buf_chunk(self, buf, chunk):
        offset = chunk.find(buf)
        return offset

    def _find_buf(self, buf, urls):
        offsets = []
        while True:
            for url in urls:
                h = hashlib.sha224(url).hexdigest()
                cache_path = 'cache/%s.tmp' % (h)
                if not os.path.exists(cache_path):
                    print('DEBUG: url=%s' % (url))
                    r = requests.get(url, stream=True)
                    if r.status_code != 200: continue
                    with open(cache_path, 'wb') as cache_f:
                        for chunk in r:
                            cache_f.write(chunk)
                #else:
                #    print('DEBUG: cache=%s' % (cache_path))

                cache_f = open(cache_path, 'rb')
                while True:
                    chunk = cache_f.read(CHUNK_SIZE*1024)
                    if not chunk:
                        break
                    t = self._cmp_buf_chunk(buf, chunk)
                    if t != -1:
                        return (len(buf), t, url)
            buf = buf[:int(len(buf)/2)]
            if len(buf) < 1:
                raise Exception('E: No urls fulfilled buffer data')
                
        return None

    def pacify(self, input_file=None, url_file=None, manifest=None):
        if not input_file or not url_file or not manifest:
            raise Exception('pacify() requires input_file, url_file, manifest')
        inf_f = open(input_file, 'rb')
        man_f = open(manifest, 'wb') 
        urls = open(url_file).read().strip().split('\n')
        offset = 0
        while True:
            buf = inf_f.read(CHUNK_SIZE)
            if not buf:
                break
            #print(buf) 
            start_buf_len = len(buf)
            prev_buf_len = len(buf)
            while prev_buf_len != 0:
                fbu = self._find_buf(buf, urls)
                if fbu is None:
                    raise Exception('Could not find url for buf at offset: %d' % (offset))
                (buf_len, url_offset, url) = fbu
                print('DEBUG: buf_len=%d url_offset=%d foff=%d url=%s' % (buf_len, url_offset, offset, url))
                man_f.write('%s %s %s\n' % (url, url_offset, buf_len))
                buf = buf[buf_len:]
                prev_buf_len = len(buf)
            offset += start_buf_len
        inf_f.close()
        man_f.close()
            
o = Opacify()

o.pacify(input_file=sys.argv[1], url_file=sys.argv[2], manifest=sys.argv[3])


