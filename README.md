# Opacify

Opacify reads a file and builds a manifest of external URLs to rebuild said file.

[![asciicast](https://asciinema.org/a/AubzHtwn5qSRTFuFL1lV72w5h.png)](https://asciinema.org/a/AubzHtwn5qSRTFuFL1lV72w5h)

# Install
```
pip install opacify
```

# Must Knows

1. Opacify is slow (and probably always will be)!
2. A cache is built locally to speedup both pacify and satisfy. It is removed on completed unless you specify ```--keep```.
3. *The cache is built from downloading the data from the urls list.* TODO: Add cache limit flag.
4. It probably could be used for illegal purposes. Please do not do this.
5. ```--threads N``` option will help speedup the pacify command.

# Why

Why not? Some reasons:

1. For fun
2. Storing a backup in a terrible manner
3. Hiding or obfuscating data
4. Avoid censorship


# Examples

Please note that the example output may not be accurate at this time as it is a work
in progress.

## Pacify A File
```
$ opacify pacify --input test.txt --manifest test.manifest --cache cache/ --urls urls.txt --keep --threads 4 --force
Progress: |████████████████████████████████████████████████████| * 100.0% thread-2 0.00m remaining

Wrote manifest to: test.manifest
   Avg chunk size: 3.40
     Total chunks: 2107
    Manifest size: 164291
    Original size: 7173
     Input sha256: 44060449ed92a19e59231d48ab634cbe89d7328f1c24ac7b48b4992b1256657f
         Duration: 7.170s
```

## Satisfy A File
```
$ opacify satisfy --out test.txt.out --manifest test.manifest --cache dcache/ --force
Progress: |████████████████████████████████████████████████████| . 100.0%  0.00m remaining

    Manifest size: 164291
    Output sha256: 44060449ed92a19e59231d48ab634cbe89d7328f1c24ac7b48b4992b1256657f
      Output size: 7173
         Duration: 15.079s
$ shasum test.txt.out test.txt
85c7bd6f40ba36326f9acd695779db7847434db4  test.txt.out
85c7bd6f40ba36326f9acd695779db7847434db4  test.txt
```

## Build Url List from Reddit
Please note that Reddit data is volatile and often disappears.
```
$ opacify reddit --out reddit-urls.txt --count 20
Generating urls from reddit data...
Wrote urls data to: reddit-urls.txt

$ wc -l reddit-urls.txt
      20 reddit-urls.txt
```

## Validate Manifest
As time goes by, external sources may disappear or content may change. The following will check that the source
exists (has a valid HTTP response) and check that the source provides enough data of offset+length:
```
$ opacify verify --manifest test.opacify
Validating external sources listed in manifest ...
Status: 100% ... Complete!
```

# Usage
```
usage: opacify [-h] [-V] {pacify,satisfy,verify,reddit} ...

Opacify : vx.x.x
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

# Errors
See [Error Codes](/ERRORS.md) for a list of errors and meanings.

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

## Backup

Add ```--backup-level N``` option to create multiple manifest items for a buffer.
This is like having replication/a backup for part of a file. If one URL source fails, a backup
URL can be used.

