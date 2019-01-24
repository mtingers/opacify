# Opacify

Opacify reads a file and builds a manifest of external sources to rebuild said file.

# Usage
```
usage: opacify [-h] [-V] {pacify,satisfy,verify,reddit} ...

Opacify : v0.2.1
Project : http://github.com/mtingers/opacify
Author  : Matth Ingersoll <matth@mtingers.com>

positional arguments:
  {pacify,satisfy,verify,reddit}
    pacify              Run in pacify mode (builds manifest from input file)
    satisfy             Run in satisfy mode (extracts file using manifest)
    verify              Validate manifest URLs and response length
    reddit              Auto-generate a urls file from reddit links

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         Display Opacify version info

Examples:
    $ opacify pacify --input test.txt --urls urls.txt --manifest test.opm --cache /tmp/cache/
    $ opacify satisfy --out test.txt.out --urls urls.txt --manifest test.opm --cache /tmp/dcache/
```

```
usage: opacify pacify [-h] -i INPUT -u URLS -m MANIFEST -c CACHE [-k] [-f]
                      [-d] [-t THREADS]

Run in pacify mode (builds manifest from input file)

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Path to input file
  -u URLS, --urls URLS  Path to urls file
  -m MANIFEST, --manifest MANIFEST
                        Output path of manifest file
  -c CACHE, --cache CACHE
                        Path to cache directory
  -k, --keep            Do not remove cache after completed. Useful for
                        testing
  -f, --force           Overwrite manifest if it exists
  -d, --debug           Turn on debug output
  -t THREADS, --threads THREADS
                        Run processing multiple threads
```

```
usage: opacify satisfy [-h] -m MANIFEST -o OUT -c CACHE [-k] [-f] [-d]

Run in satisfy mode (rebuilds file using manifest)

optional arguments:
  -h, --help            show this help message and exit
  -m MANIFEST, --manifest MANIFEST
                        Path of manifest file
  -o OUT, --out OUT     Path to write output file to
  -c CACHE, --cache CACHE
                        Path to cache directory
  -k, --keep            Do not remove cache after completed. Useful for
                        testing
  -f, --force           Overwrite output file if it exists
  -d, --debug           Turn on debug output
```

```
usage: opacify verify [-h] -m MANIFEST [-d]

Validate manifest URLs and response length

optional arguments:
  -h, --help            show this help message and exit
  -m MANIFEST, --manifest MANIFEST
                        Path of manifest file
  -d, --debug           Turn on debug output
```

```
usage: opacify reddit [-h] -o OUT -c COUNT

Auto-generate a urls file from reddit links

optional arguments:
  -h, --help            show this help message and exit
  -o OUT, --out OUT     Path to write urls to
  -c COUNT, --count COUNT
                        How many links to get
```

# Examples

Please note that the example output may not be accurate at this time as it is a work
in progress.

## Opacify A File
```
$ opacify pacify --input test.txt --urls sources.txt --manifest test.opacify
Running pacify on test.txt using sources.txt ...
Status: 100% ... Complete!
```

## Satisfy A File
```
$ opacify satisfy --manifest test.opacify --out test-satisfy.txt
Running satisfy on test.opacify ...
Status: 100% ... Complete!
```

## Validate Manifest
As time goes by, external sources may disappear or content may change. The following will check that the source
exists (has a valid HTTP response) and check that the source provides enough data of offset+length:
```
$ opacify verify --manifest test.opacify
Validating external sources listed in manifest ...
Status: 100% ... Complete!
```

## Errors
See [Error Codes](/ERRORS.md) for a list of errors and meanings.

Fail to pacify:
```
$ opacify pacify --input test.txt --urls sources.txt --manifest test.opacify
Running pacify on test.txt using sources.txt ...
Status: 54% ... ERROR:
    E1: Not enough external sources to complete manifest!
```

Fail to satisfy (external sources changed):
```
$ opacify satisfy --manifest test.opacify --out test-satisfy.txt
Running satisfy on test.opacify ...
Status: 23% ... ERROR:
    E2: Failed to extract source:
        http://foo/bar.jpg
    Partial contents are located at:
         test-satisfy.txt
```

Fail to satisfy (external sources changed), but continue on:
```
$ opacify satisfy --manifest test.opacify --out test-satisfy.txt --continue
Running satisfy on test.opacify ...
Status: 23% ...
ERROR: External source http://foo/bar.jpg failed at offset 32, 40 bytes.
ERROR: External source http://foo/bar.jpg failed at offset 44, 20 bytes.
    E3: We tried our best but not all external sources were good.
    Partial contents are located at:
         test-satisfy.txt
```

Fail to validate sha256 or length on satisfy:
```
$ opacify satisfy --manifest test.opacify --out test-satisfy.txt
Running satisfy on test.opacify ...
Status: 44% ...ERROR:
    E4: SHA256 does not match manifest! The data is likely invalid!
    Output file was still saved to:
         test-satisfy.txt
```
```
$ opacify satisfy --manifest test.opacify --out test-satisfy.txt
Running satisfy on test.opacify ...
Status: 12% ... ERROR:
    E5: Length does not match manifest! The data is likely invalid!
        This should not happen, there may be a bug in Opacify
        OR a problem with your system!
    Output file was still saved to:
         test-satisfy.txt
```

Fail to validate manifest:
```
$ opacify verify --manifest test.opacify
Validating external sources listed in manifest ...
Status: 55% ... ERROR:
    E6: Source http://foo.bar.jpg returned an invalid response!
        You cannot fully rebuild from the manifest!
```

# Manifest Format

The manifest consists of a header and body.

## Header
The header is one line with a ':' delimiter.  It contains the following in order as of this writing:
    version:source-file-sha256:source-file-length

* version: The version of Opacify that the manifest was built with.
* source-file-sha256: The sha256 of the input file. This is used to validate on satisfy.
* source-file-length: The length of the input file. This is also used to validate on satisfy.

## Body

Each line represents an item and has a space as a delimiter.  The lines are in order of the input
file data.  Example:
```
http://foo/bar.png 23 55
http://bar/foo.png 100 32
```

The body items (each line) consist of the following parts:
1. encoded url
2. external source data offset
3. external source data length


This example describes the following process to rebuild the input file from the above example:
1. Read 55 bytes from http://foo/bar.png starting at an offset of 23 bytes.
2. Append this data to the output file.
3. Read 32 bytes from http://bar/foo.png starting at an offset of 100 bytes.
4. Append this data to the output file.


# TODO

## Threading

Make a --threads option to speed up operations when interacting with external sources.

## Backup

Add ```--backup-level N``` option to create multiple manifest items for a buffer.
This is like having replication/a backup for part of a file. If one URL source fails, a backup
URL can be used.

