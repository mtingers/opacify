# Opacify

Opacify reads a file and builds a manifest of external sources to rebuild said file.

# Usage
```
usage: opacify [-h] [-V] {pacify,depacify,verify} ...

Opacify : v0.1.2
Project : http://github.com/mtingers/opacify
Author  : Matth Ingersoll <matth@mtingers.com>
Commit  : 754ed2be468c3b626d827c0cbfec3d3bcdc30dd0

positional arguments:
  {pacify,depacify,verify}
    pacify              Run in pacify mode (builds manifest from input file)
    depacify            Run in depacify mode (extracts file using manifest)
    verify              Validate manifest URLs and response length

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         Display Opacify version info

Examples:
    $ opacify pacify --input test.txt --urls urls.txt --manifest test.opm --cache /tmp/cache/
    $ opacify depacify --output test.txt.out --urls urls.txt --manifest test.opm --cache /tmp/dcache/

```

```
usage: opacify pacify [-h] -i INPUT -u URLS -m MANIFEST -c CACHE [-k] [-f]
                         [-d]

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
```

```
usage: opacify depacify [-h] -m MANIFEST -o OUT -c CACHE [-k] [-f] [-d]

Run in depacify mode (rebuilds file using manifest)

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
# Examples

Please note that the example output may not be accurate at this time as it is a work
in progress.

## Opacify A File
```
$ opacify pacify --input test.txt --urls sources.txt --manifest test.opacify
Running pacify on test.txt using sources.txt ...
Status: 100% ... Complete!
```

## Depacify A File
```
$ opacify depacify --manifest test.opacify --out test-depacify.txt
Running depacify on test.opacify ...
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

Fail to depacify (external sources changed):
```
$ opacify depacify --manifest test.opacify --out test-depacify.txt
Running depacify on test.opacify ...
Status: 23% ... ERROR:
    E2: Failed to extract source:
        http://foo/bar.jpg
    Partial contents are located at:
         test-depacify.txt
```

Fail to depacify (external sources changed), but continue on:
```
$ opacify depacify --manifest test.opacify --out test-depacify.txt --continue
Running depacify on test.opacify ...
Status: 23% ...
ERROR: External source http://foo/bar.jpg failed at offset 32, 40 bytes.
ERROR: External source http://foo/bar.jpg failed at offset 44, 20 bytes.
    E3: We tried our best but not all external sources were good.
    Partial contents are located at:
         test-depacify.txt
```

Fail to validate sha256 or length on depacify:
```
$ opacify depacify --manifest test.opacify --out test-depacify.txt
Running depacify on test.opacify ...
Status: 44% ...ERROR:
    E4: SHA256 does not match manifest! The data is likely invalid!
    Output file was still saved to:
         test-depacify.txt
```
```
$ opacify depacify --manifest test.opacify --out test-depacify.txt
Running depacify on test.opacify ...
Status: 12% ... ERROR:
    E5: Length does not match manifest! The data is likely invalid!
        This should not happen, there may be a bug in Opacify
        OR a problem with your system!
    Output file was still saved to:
         test-depacify.txt
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
* source-file-sha256: The sha256 of the input file. This is used to validate on depacify.
* source-file-length: The length of the input file. This is also used to validate on depacify.

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

## Implementation

~~You know, implement the code.~~ First POC done.

## Threading

Make a --threads option to speed up operations when interacting with external sources.

## Auto External Sources

Instead of having to compile a list of sources to build from, provide a way to auto-build this source
from common locations (e.g. imgur, giphy, reddit, etc). Depending on the input file size, this could
take an extremely long time.

```
$ opacify pacify --input test.txt --urls-auto --manifest test.opacify --verbose
Running pacify on test.txt and finding external sources ...
Status: Found source http://foo.com/hello.txt for offset 0, using 32 bytes
Status: Found source http://foo.com/foo.gif for offset 32, using 12 bytes
...
Status: Complete!
Runtime: 24 minutes
```

## Backup

Add ```--backup-level N``` option to create multiple manifest items for a buffer.
This is like having replication/a backup for part of a file. If one URL source fails, a backup
URL can be used.

