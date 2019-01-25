import os
import sys
import time
import hashlib
import socket
import requests
import threading
from enum import Enum
from multiprocessing import Process, Manager
from pprint import pprint
import gzip

from .opacifyinfo import *
from .progress import progress_bar

EPILOG  = """
Examples:
    $ opacify pacify --input test.txt --urls urls.txt --manifest test.opm --cache /tmp/cache/
    $ opacify satisfy --out test.txt.out --urls urls.txt --manifest test.opm --cache /tmp/dcache/
"""
INFOTXT  = """
Opacify : %s
Project : %s
Author  : %s
""" % (VERSION, PROJECT, AUTHOR)

#
# IMPORTANT: CHUNK_SIZE
# Apparently, find() is very slow. Default chunk size of 1 byte is orders
# of magnitude faster than iterating multiple find()s at larger sizes.
# There is now a new option -s/--chunksize to override the default.
# Since the manifest is now compressed, most duplicate URL entries will
# still result in a small manifest even the CHUNK_SIZE=1 will cause many
# many more entries.
# Example of the issue:
#
#    $ opacify pacify -i zsh -m test.manifest -c cache -u urls.txt -f -t 6  -s 1 -k
#         Total chunks: 610224
#        Manifest size: 901676
#             Duration: 20.457s
#
#    $ opacify pacify -i zsh -m test.manifest -c cache -u urls.txt -f -t 6  -s 2 -k
#         Total chunks: 305112
#        Manifest size: 855333
#             Duration: 34.285s
#
#    $ opacify pacify -i zsh -m test.manifest -c cache -u urls.txt -f -t 6  -s 4 -k
#         Total chunks: 287376
#        Manifest size: 889166
#             Duration: 461.811s
#
# Note above that the manifest size is very close, but the duration is completely
# different.
#
CHUNK_SIZE = 1

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
    E_URL_NOT_FOUND     = 16
    E_FAILED            = 17
    E_MANIFEST          = 18

class Status(object):
    def __init__(self, code=None, message=None):
        self.codes = []
        self.messages = []
        if code is not None:
            self.add(code, message)

    def add(self, code, message):
        if type(code) != StatusCodes:
            raise Exception('Status expects code to be of type StatusCodes')
        self.codes.append(code)
        self.messages.append(message)

class Results(object):
    def __init__(self):
        self.results = []

    def add(self, status):
        if type(status) != Status:
            raise Exception('Results expects status to be of type Status')
        self.results.append(status)

    def get(self):
        return self.results

class Opacify(object):
    def __init__(self, cache_dir=None, debug=False, chunk_size=None):
        self.total_chunks = 0
        self.total_chunk_size = 0
        self.__version = VERSION
        self.cache_dir = 'cache'
        self.debug = debug
        if cache_dir:
            self.cache_dir = cache_dir
        self._failed_urls_cache = []
        self.timer_start = time.time()
        self.results = Results()
        self.digest = None
        self.clength = 0
        self.chunk_size = CHUNK_SIZE
        if chunk_size:
            self.chunk_size = int(chunk_size)

    def messages(self):
        return self._messages

    def print_debug(self, msg):
        if self.debug:
            print('DEBUG: %s' % (msg))

    def result(self, code, message):
        if self.debug:
            self.print_debug('code=%s message=%s' % (code.name, message))
        self.results.add(Status(code=code, message=message))
        return code

    def _write_url_to_cache(self, url, overwrite=False):
        cache_path = self._cache_path(url)
        if not os.path.exists(cache_path) or overwrite is True:
            self.print_debug('create cache file: %s' % (cache_path))
            self.print_debug('get: %s' % (url))
            r = requests.get(url, timeout=5, stream=True)
            if r.status_code != 200:
                self._failed_urls_cache.append(url)
                return self.result(StatusCodes.E_URL_OPEN, 'Failed to open URL: %s' % (url))
            try:
                with open(cache_path, 'wb') as cache_f:
                    for chunk in r:
                        cache_f.write(chunk)
            except Exception as e:
                return self.result(StatusCodes.E_CACHE_OPEN, "Failed to open cache '%s'. Error=%s" % (cache_path, e))
        return StatusCodes.OK

    def _find_buf(self, buf, urls):
        while True:
            for url in urls:
                if url in self._failed_urls_cache:
                    continue
                test = self._write_url_to_cache(url)
                if test == StatusCodes.E_URL_OPEN:
                    continue
                elif test == StatusCodes.E_CACHE_OPEN:
                    return test

                cache_path = self._cache_path(url)
                cache_f = open(cache_path, 'rb')
                total_chunk_size = 0
                while True:
                    chunk = cache_f.read(self.chunk_size*1024)
                    if not chunk:
                        break
                    offset = chunk.find(buf)
                    if offset > 0:
                        #assert (len(buf) % 2 == 0 or (len(buf) != 1 and len(buf) % 2 == 0)), "Odd buffer size: %d" % (len(buf))
                        return (len(buf), total_chunk_size+offset, url)
                    total_chunk_size += len(chunk)
            lb = len(buf)
            #buf = buf[:-1]
            if lb > 8:
                buf = buf[:-8]
            elif lb > 4:
                buf = buf[:-4]
            elif lb > 2:
                buf = buf[:-2]
            else:
                buf = buf[:-1]
            if len(buf) < 1:
                return False
                #return self.result(StatusCodes.E_URL_NOT_FOUND, 'Unable to find buffer in all URLs')

        # Fallthrough that should not be reached. If it is, there is an error in the logic
        return self.result(StatusCodes.E_FAILED, 'Programmer error in _find_buf')

    def build_cache(self, urls):
        sys.stdout.write('Building cache...\r')
        sys.stdout.flush()
        if not os.path.exists(self.cache_dir):
            os.mkdir(self.cache_dir)
        for url in urls:
            if url in self._failed_urls_cache:
                continue
            self._write_url_to_cache(url)

    def _pacify(self, input_file=None, url_file=None, manifest=None, overwrite=False, keep_cache=False,
            input_offset=None, input_end=None, show_progress=False, thread_id=None, thread_info=None):
        input_hash = hashlib.sha256()
        if not input_file or not url_file or not manifest:
            raise Exception('Programmer error: pacify() requires input_file, url_file, manifest')

        if os.path.exists(manifest) and not overwrite:
            r = self.result(StatusCodes.E_MANIFEST_EXISTS, 'Manifest file exists. Use --force to overwrite')
            if thread_id is not None and thread_id is not False and thread_info:
                thread_info['result'] = self.results
            return r

        if input_offset is not None and input_end is not None:
            manifest += '-%s-%s.tmp' % (input_offset, input_end)
            inf_f = open(input_file, 'rb')
            self.print_debug('THREADED(%d): input_offset:%d input_end:%d' % (thread_id, input_offset, input_end))
            inf_f.seek(input_offset, os.SEEK_SET)
            input_size = input_end - input_offset
            offset = 0 #ehhh 0 should work? right?
            thread_info['up'] = True
        else:
            inf_f = open(input_file, 'rb')
            input_size = os.path.getsize(input_file)
            offset = 0

        man_f = gzip.open(manifest, 'wb')
        urls = open(url_file).read().strip().split('\n')
        if show_progress:
            if thread_id is not None:
                progress_bar(0, input_size, prefix='Progress:', suffix='thread-%s' % (thread_id),
                    length=24, timer_start=self.timer_start)
            else:
                progress_bar(0, input_size, prefix='Progress:', suffix='', length=24,
                    timer_start=self.timer_start)
        while offset < input_size:
            if input_size - offset < self.chunk_size:
                buf = inf_f.read(input_size - offset)
            else:
                buf = inf_f.read(self.chunk_size)
            if not buf:
                break
            input_hash.update(buf)
            start_buf_len = len(buf)
            prev_buf_len = len(buf)
            cur_offset = offset
            while prev_buf_len > 0:
                fbu = self._find_buf(buf, urls)
                if type(fbu) is not tuple: #StatusCodes.E_NONE:
                    # If this is a thread, return will not do anything
                    # Instead messages are pushed into results and results
                    # added to Manger() dict
                    r = self.result(StatusCodes.E_URL_NOT_FOUND, 'Could not find url for buf at offset: %d' % (offset))
                    if thread_info is not None:
                        thread_info['result'] = self.results
                    return r

                (buf_len, url_offset, url) = fbu
                self.total_chunk_size += buf_len
                self.total_chunks += 1
                cur_offset += buf_len
                assert buf_len != 0, 'buffer length is 0'
                self.print_debug('buf_len=%d url_offset=%d foff=%d url=%s' % (buf_len, url_offset, offset, url))
                man_f.write(bytes('%s %s %s\n' % (url, url_offset, buf_len), 'utf-8'))
                buf = buf[buf_len:]
                prev_buf_len = len(buf)
                if show_progress:
                    if thread_id is None:
                        progress_bar(cur_offset, input_size, prefix='Progress:', suffix='', length=24,
                            timer_start=self.timer_start)

            offset += start_buf_len
            if not self.debug and show_progress:
                if thread_id is not None:
                    progress_bar(offset, input_size, prefix='Progress:', suffix='thread-%s' % (thread_id),
                        length=24, timer_start=self.timer_start)
                else:
                    progress_bar(offset, input_size, prefix='Progress:', suffix='', length=24,
                        timer_start=self.timer_start)
        sha = input_hash.hexdigest()
        self.digest = sha
        self.clength = offset
        man_header = bytes('_header:%s:%s:%d\n' % (self.__version, sha, offset), 'utf-8')
        man_f.write(man_header)
        inf_f.close()
        man_f.close()
        if thread_id is not None and thread_id is not False and thread_info:
            thread_info['result'] = self.results
            #thread_info['msgs'] = self.messages()
        return self.result(StatusCodes.OK, 'OK')

    def pacify(self, input_file=None, url_file=None, manifest=None, overwrite=False, keep_cache=False, threads=None):
        self.timer_start = time.time()
        self.build_cache(open(url_file).read().strip().split('\n'))
        if threads is None:
            return self._pacify(input_file=input_file, url_file=url_file, manifest=manifest,
                overwrite=overwrite, keep_cache=keep_cache, show_progress=True)

        # threads is set
        n_threads = int(threads)
        input_size = os.path.getsize(input_file)
        # do not thread on small sizes
        if n_threads*10 > input_size:
            return self._pacify(input_file=input_file, url_file=url_file, manifest=manifest,
                overwrite=overwrite, keep_cache=keep_cache, show_progress=True)

        leftovers = input_size % n_threads
        per_thread = int(input_size / n_threads)
        # {} Allows multiprocess communication back to parent
        manager = Manager()
        thread_info = {} #manager.dict()
        offset = 0
        for i in range(n_threads):
            offset += per_thread
            thread_info[i] = manager.dict(
                {'offset':offset-per_thread, 'end':offset, 'result':None, 'up':False, 'msgs':[]})
        thread_info[i]['end'] += leftovers # Add the remaining to the last thread
        threads = []
        for i in range(n_threads):
            kw = {
                'input_file':input_file,
                'url_file':url_file,
                'manifest':manifest,
                'overwrite':overwrite,
                'keep_cache':keep_cache,
                'input_offset':thread_info[i]['offset'],
                'input_end':thread_info[i]['end'],
                'thread_id':i, 'show_progress':True,
                'thread_info':thread_info[i],
            }
            if i+1 >= n_threads:
                kw['show_progress'] = True
            #t = threading.Thread(target=self._pacify, kwargs=kw)
            t = Process(target=self._pacify, kwargs=kw)
            #t.daemon = True
            t.start()
            threads.append(t)
        # Threads will write to their own unique file "mainifest+offset+end.tmp"
        # We then need to join these temp files in order to create the final
        # manifes
        for t in threads:
            t.join()

        for i in range(n_threads):
            status = thread_info[i]
            if status['result']:
                for x in status['result'].get():
                    for j in range(len(x.codes)):
                        self.result(x.codes[j], x.messages[j])

        combined_manifest = gzip.open(manifest, 'wb') # TODO: check if --force
        total_len = 0
        errors = 0
        for i in range(n_threads):
            t_manifest = '%s-%s-%s.tmp' % (manifest, thread_info[i]['offset'], thread_info[i]['end'])
            try:
                (version, sha, length) = self.get_manifest_header(t_manifest)
            except Exception as e:
                self.print_debug('%s' % (e))
                self.result(StatusCodes.E_MANIFEST, 'Invalid manifest from thread: %s' % (t_manifest))
                errors += 1
                continue
            with gzip.open(t_manifest, 'rb') as m_f:
                for line in m_f:
                    line = line.decode()
                    if line.startswith('_header:'): break
                    (url, url_offset, buf_len) = line.strip().split(' ')
                    self.total_chunk_size += int(buf_len)
                    self.total_chunks += 1
                    total_len += int(buf_len)
                    combined_manifest.write(bytes('%s %s %s\n' % (url, url_offset, buf_len), 'utf-8'))
            os.unlink(t_manifest)
        if errors > 0:
            return self.result(StatusCodes.E_MANIFEST, 'Failed to combine all manifests.')
        input_hash = hashlib.sha256()
        offset = 0
        with open(input_file, 'rb') as inf_f:
            while True:
                if total_len - offset < self.chunk_size:
                    buf = inf_f.read(total_len - offset)
                else:
                    buf = inf_f.read(self.chunk_size)
                if not buf:
                    break
                offset += len(buf)
                input_hash.update(buf)
        sha = input_hash.hexdigest()
        self.digest = sha
        self.clength = total_len
        man_header = bytes('_header:%s:%s:%d\n' % (self.__version, sha, total_len), 'utf-8')
        inf_f.close()
        combined_manifest.write(man_header)
        combined_manifest.close()
        if not keep_cache:
            self.clean_cache()
        return self.result(StatusCodes.OK, 'OK')

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
        with gzip.open(manifest_path, 'rb') as f:
            f.seek(start_offset, os.SEEK_SET)
            for last_line in f:
                pass
        last_line = last_line.decode()
        z = last_line.split(':')
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
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                h.update(chunk)
                clength += len(chunk)
        digest = h.hexdigest()
        self.print_debug('digest=%s sha=%s' % (digest, sha))
        if digest != sha:
            return self.result(StatusCodes.E_HASH_MISMATCH, 'Output file hash did not match manifest hash!')
        self.print_debug('length=%d clen=%d' % (length, clength))
        if length != clength:
            return self.result(StatusCodes.E_LEN_MISMATCH, 'Output file length did not match manifest length!')
        self.digest = digest
        self.clength = clength
        return self.result(StatusCodes.OK, 'OK')

    def satisfy(self, manifest=None, out_file=None, keep_cache=False, overwrite=False, show_progress=True):
        if os.path.exists(out_file) and not overwrite:
            return self.result(StatusCodes.E_OUTFILE_EXISTS, 'Output file exists. Use --force option to overwrite.')

        out_f = open(out_file, 'wb')
        (version, sha, length) = self.get_manifest_header(manifest)
        length = int(length)
        self.print_debug('Manifest: %s %s %s' % (version, sha, length))
        timer_start = time.time()
        progress_offset = 0
        with gzip.open(manifest, 'rb') as m_f:
            for line in m_f:
                line = line.decode()
                if line.startswith('_header:'): break
                (url, url_offset, buf_len) = line.strip().split(' ')
                url_offset = int(url_offset)
                buf_len = int(buf_len)
                self.print_debug('url=%s offset=%d len=%d' % (url, url_offset, buf_len))
                progress_offset += buf_len
                if show_progress:
                    progress_bar(progress_offset, length, prefix='Progress:', suffix='', length=24,
                        timer_start=timer_start)
                buf = b''
                cache_path = self._cache_path(url)
                self.print_debug(cache_path)
                if not os.path.exists(cache_path):
                    self.print_debug('create cache file: %s' % (cache_path))
                    self.print_debug('get: %s' % (url))
                    r = requests.get(url, timeout=5, stream=True)
                    if r.status_code != 200:
                        return self.result(StatusCodes.E_OPEN_URL,
                            'Failed to open url: %s\nOutput file is incomplete.' % (url))
                    with open(cache_path, 'wb') as cache_f:
                        for chunk in r:
                            buf += chunk
                            cache_f.write(chunk)
                buf = b''
                cache_f = open(cache_path, 'rb')
                while True:
                    tmp = cache_f.read(self.chunk_size*1000)
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

