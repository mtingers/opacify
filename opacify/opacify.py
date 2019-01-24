import os
import sys
import requests
import hashlib
from enum import Enum

from .opacifyinfo import *

EPILOG  = """
Examples:
    $ opacify pacify --input test.txt --urls urls.txt --manifest test.opm --cache /tmp/cache/
    $ opacify depacify --output test.txt.out --urls urls.txt --manifest test.opm --cache /tmp/dcache/
"""
INFOTXT  = """
Opacify : %s
Project : %s
Author  : %s
Commit  : %s
""" % (VERSION, PROJECT, AUTHOR, COMMIT)

CHUNK_SIZE = 24

class StatusCodes(Enum):
    OK                  = True
    E_NONE              = None
    E_PATH_EXISTS       = 2
    E_CACHE_OPEN        = 3
    E_URL_OPEN          = 4
    E_BUFFER_SIZE       = 5
    E_FIND_BUFFER       = 6
    E_MANIFEST_EXISTS   = 7
    E_OPEN_URL_FILE     = 8
    E_OPEN_MANIFEST     = 9
    E_OPEN_INPUT_FILE   = 10
    E_UNKNOWN           = 11
    E_OPEN_URL          = 12
    E_HASH_MISMATCH     = 13
    E_LEN_MISMATCH      = 14
    E_OUTFILE_EXISTS    = 15

class Opacify(object):
    def __init__(self, cache_dir=None, debug=False):
        self.__version = VERSION
        self.cache_dir = 'cache'
        self._status_messages = []
        self.debug = debug
        if cache_dir:
            self.cache_dir = cache_dir
    def messages(self):
        return self._status_messages

    def print_debug(self, msg):
        if self.debug:
            print('DEBUG: %s' % (msg))

    def status(self, status, msg=None):
        if msg is None:
            msg = status.name
        self._status_messages.append((status.name, msg))
        if self.debug:
            self.print_debug(msg)
        return status

    def _write_url_to_cache(self, url, overwrite=False):
        cache_path = self._cache_path(url)
        if not os.path.exists(cache_path) or overwrite is True:
            self.print_debug('create cache file: %s' % (cache_path))
            r = requests.get(url, timeout=5, stream=True)
            if r.status_code != 200:
                return self.status(StatusCodes.E_URL_OPEN, msg='Failed to open URL: %s' % (url))
            try:
                with open(cache_path, 'wb') as cache_f:
                    for chunk in r:
                        cache_f.write(chunk)
            except Exception as e:
                return self.status(StatusCodes.E_CACHE_OPEN,
                    msg="Failed to open cache '%s'. Error=%s" % (cache_path, e))
        return StatusCodes.OK

    def _find_buf(self, buf, urls):
        while True:
            for url in urls:
                test = self._write_url_to_cache(url)
                if test == StatusCodes.E_URL_OPEN:
                    continue
                elif test == StatusCodes.E_CACHE_OPEN:
                    return test

                cache_path = self._cache_path(url)
                cache_f = open(cache_path, 'rb')
                total_chunk_size = 0
                while True:
                    chunk = cache_f.read(CHUNK_SIZE*1024)
                    if not chunk:
                        break
                    offset = chunk.find(buf)
                    if offset > 0:
                        assert (len(buf) % 2 == 0 or (len(buf) != 1 and len(buf) % 2 == 0)), "Odd buffer size"
                        return (len(buf), total_chunk_size+offset, url)
                    total_chunk_size += len(chunk)
            lb = len(buf)
            if lb > 8:
                buf = buf[:-8]
            elif lb > 4:
                buf = buf[:-4]
            elif lb > 2:
                buf = buf[:-2]
            else:
                buf = buf[:-1]
            if len(buf) < 1:
                return self.status(StatusCodes.E_BUFFER_NOT_FOUND,
                    msg='Unable to find buffer in all URLs')

        return StatusCodes.E_NONE


    def pacify(self, input_file=None, url_file=None, manifest=None, overwrite=False, keep_cache=False):
        input_hash = hashlib.sha256()
        if not input_file or not url_file or not manifest:
            raise Exception('pacify() requires input_file, url_file, manifest')

        if os.path.exists(manifest) and not overwrite:
            return self.status(StatusCodes.E_MANIFEST_EXISTS,
                msg='Manifest file exists. Use --force to overwrite')

        inf_f = open(input_file, 'rb')
        man_f = open(manifest, 'w')
        urls = open(url_file).read().strip().split('\n')
        offset = 0
        while True:
            buf = inf_f.read(CHUNK_SIZE)
            if not buf:
                break
            input_hash.update(buf)
            start_buf_len = len(buf)
            prev_buf_len = len(buf)
            while prev_buf_len > 0:
                fbu = self._find_buf(buf, urls)
                if fbu is StatusCodes.E_NONE:
                    raise self.status(StatusCodes.E_NO_URL_FOUND,
                        msg='Could not find url for buf at offset: %d' % (offset))
                (buf_len, url_offset, url) = fbu
                assert buf_len != 0, 'buffer length is 0'
                self.print_debug('buf_len=%d url_offset=%d foff=%d url=%s' % (buf_len, url_offset, offset, url))
                man_f.write('%s %s %s\n' % (url, url_offset, buf_len))
                buf = buf[buf_len:]
                prev_buf_len = len(buf)

            offset += start_buf_len
        sha = input_hash.hexdigest()
        man_header = '_header:%s:%s:%d\n' % (self.__version, sha, offset)
        man_f.write(man_header)
        inf_f.close()
        man_f.close()
        if not keep_cache:
            self.clean_cache()
        return (sha, offset)

    def _cache_path(self, url):
        h = hashlib.sha256(url.encode()).hexdigest()
        cache_path = '%s/opacify-%s.tmp' % (self.cache_dir, h)
        return cache_path


    def get_manifest_header(self, manifest_path):
        last_line = None
        # Start close to the end, but with enough padding that
        # we won't skip the last line
        start_offset = os.path.getsize(manifest_path) - 1024
        if start_offset < 0:
            start_offset = 0
        self.print_debug('get_manifest_header: start_offest=%d' % (start_offset))
        with open(manifest_path, 'r') as f:
            f.seek(start_offset, os.SEEK_SET)
            for last_line in f:
                pass
        (_, version, sha, length) = last_line.split(':')
        return (version, sha, int(length))

    def clean_cache(self):
        self.print_debug('Cleaning cache path: %s' % (self.cache_dir))
        for name in os.listdir(self.cache_dir):
            if not name.startswith('opacify-') or not name.endswith('.tmp'):
                continue
            path = '%s/%s' % (self.cache_dir, name)
            self.print_debug('Remove cache file: %s' % (path))
            os.unlink(path)

    def validate_output(self, path, sha, length):
        h = hashlib.sha256()
        clength = 0
        length = int(length)
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                h.update(chunk)
                clength += len(chunk)
        digest = h.hexdigest()
        self.print_debug('digest=%s sha=%s' % (digest, sha))
        if digest != sha:
            return self.status(StatusCodes.E_HASH_MISMATCH,
                'Output file hash did not match manifest hash!')
        self.print_debug('length=%d clen=%d' % (length, clength))
        if length != clength:
            return self.status(StatusCodes.E_LEN_MISMATCH, 'Output file length did not match manifest length!')
        return (digest, clength)

    def depacify(self, manifest=None, out_file=None, keep_cache=False, overwrite=False):
        if os.path.exists(out_file) and not overwrite:
            return self.status(StatusCodes.E_OUTFILE_EXISTS, msg='Output file exists. Use --force option to overwrite.')
        out_f = open(out_file, 'wb')
        (version, sha, length) = self.get_manifest_header(manifest)
        self.print_debug('Manifest: %s %s %s' % (version, sha, length))
        with open(manifest, 'r') as m_f:
            for line in m_f:
                if line.startswith('_header:'): break
                (url, url_offset, buf_len) = line.strip().split(' ')
                url_offset = int(url_offset)
                buf_len = int(buf_len)
                self.print_debug('url=%s offset=%d len=%d' % (url, url_offset, buf_len))
                buf = b''
                cache_path = self._cache_path(url)
                self.print_debug(cache_path)
                if not os.path.exists(cache_path):
                    self.print_debug('create cache file: %s' % (cache_path))
                    r = requests.get(url, timeout=30, stream=True)
                    if r.status_code != 200:
                        return self.status(StatusCodes.E_OPEN_URL,
                            msg='Failed to open url: %s\nOutput file is incomplete.' % (url))
                    with open(cache_path, 'wb') as cache_f:
                        for chunk in r:
                            buf += chunk
                            cache_f.write(chunk)
                buf = b''
                cache_f = open(cache_path, 'rb')
                while True:
                    tmp = cache_f.read(CHUNK_SIZE*1000)
                    if not tmp :break
                    buf += tmp
                    if len(buf) > buf_len + url_offset:
                        break
                cache_f.close()
                buf = buf[url_offset:url_offset+buf_len]
                out_f.write(buf)
            out_f.close()
        if not keep_cache:
            self.clean_cache()
        return self.validate_output(out_file, sha, length)

