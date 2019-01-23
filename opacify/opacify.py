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
        #if offset > 0:
        #    print("%s" % (chunk[offset:offset+len(buf)])),
        return offset

    def _find_buf(self, buf, urls):
        offsets = []
        while True:
            for url in urls:
                h = hashlib.sha224(url.encode()).hexdigest()
                cache_path = 'cache/%s.tmp' % (h)
                if not os.path.exists(cache_path):
                    #print('DEBUG: url=%s' % (url))
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
                    if t != -1 and t != 0:
                        #if len(buf) % 2 != 0 and len(buf) != 1:
                        #    raise Exception('odd buffer?: %d' % (len(buf)))
                        return (len(buf), t, url)
            lb = len(buf)
            """if lb > 8:
                buf = buf[:-8]
            elif lb > 4:
                buf = buf[:-4]
            elif lb > 2:
                buf = buf[:-2]
            else:
                buf = buf[:-1]
            """
            if lb > 1:
                buf = buf[:-1]

            #buf = buf[:int(len(buf)/2)]
            if len(buf) < 1:
                raise Exception('E: No urls fulfilled buffer data')
                
        return None

    def pacify(self, input_file=None, url_file=None, manifest=None):
        if not input_file or not url_file or not manifest:
            raise Exception('pacify() requires input_file, url_file, manifest')
        inf_f = open(input_file, 'rb')
        man_f = open(manifest, 'w') 
        urls = open(url_file).read().strip().split('\n')
        offset = 0
        while True:
            buf = inf_f.read(CHUNK_SIZE)
            if not buf:
                break
            #print(buf) 
            start_buf_len = len(buf)
            prev_buf_len = len(buf)
            while prev_buf_len > 0:
                print(len(buf))
                fbu = self._find_buf(buf, urls)
                if fbu is None:
                    raise Exception('Could not find url for buf at offset: %d' % (offset))
                (buf_len, url_offset, url) = fbu
                if buf_len == 0:
                    raise Exception('buf_len == 0')
                print('DEBUG: buf_len=%d url_offset=%d foff=%d url=%s' % (buf_len, url_offset, offset, url))
                """output = url
                output += ' '
                output += str(url_offset)
                output += ' '
                output += str(buf_len)
                """
                man_f.write('%s %s %s\n' % (url, url_offset, buf_len))
                buf = buf[buf_len:]
                prev_buf_len = len(buf)

            offset += start_buf_len
        inf_f.close()
        man_f.close()

    def depacify(self, manifest=None, out_file=None):
        out_f = open(out_file, 'wb')
        with open(manifest, 'r') as m_f:
            for line in m_f:
                (url, url_offset, buf_len) = line.strip().split(' ')
                url_offset = int(url_offset)
                buf_len = int(buf_len)
                print('DEBUG: url=%s offset=%d len=%d' % (url, url_offset, buf_len)) 
                buf = b''
                h = hashlib.sha224(url.encode()).hexdigest()
                cache_path = 'cache/%s.tmp' % (h)
                if not os.path.exists(cache_path):
                    r = requests.get(url, stream=True)
                    if r.status_code != 200:
                        raise Exception('Failed to open url: %s\nFile is incomplete' % (url))
                    for chunk in r:
                        buf += chunk
                        if len(buf) > buf_len + url_offset:
                            break
                    buf = buf[url_offset:url_offset+buf_len]
                    out_f.write(buf)
                else:
                    cache_f = open(cache_path, 'rb')
                    while True:
                        tmp = cache_f.read(CHUNK_SIZE*1000)
                        if not tmp:
                            break
                        buf += tmp
                        if len(buf) > buf_len + url_offset:
                            break
                    buf = buf[url_offset:url_offset+buf_len]
                    out_f.write(buf)
                    cache_f.close()
            out_f.close()                 
    
o = Opacify()

o.pacify(input_file=sys.argv[1], url_file=sys.argv[2], manifest=sys.argv[3])
o.depacify(manifest=sys.argv[3], out_file=sys.argv[4])

