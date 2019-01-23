# Opacify

Opacify reads a file and builds a manifest of external sources to rebuild said file.

# Examples

## Opacify A File
```bash
$ opacify -o --input-file test.txt --external-sources sources.txt --manifest test.opacify
Running pacify on test.txt using sources.txt ...
Status: 54% ... Complete!
```

## Depacify A File
```bash
$ opacify -d --manifest test.opacify -save test-depacify.txt
Running depacify on test.opacify ...
Status: 23% ... Complete!
```

## Errors
Fail to pacify:
```bash
$ opacify --pacify --input-file test.txt --external-sources sources.txt --manifest test.opacify
Running pacify on test.txt using sources.txt ...
Status: 54% ... ERROR:
    Not enough external sources to complete manifest!
```

Fail to depacify (external sources changed):
```bash
$ opacify --depacify --manifest test.opacify -save test-depacify.txt
Running depacify on test.opacify ...
Status: 23% ... ERROR:
    Failed to extract source:
        http://foo/bar.jpg
    Partial contents are located at:
         test-depacify.txt
```

# Manifest Format

The manifest consists of a header and body.

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


## Header
The header is one line with a ':' delimiter.  It contains the following in order as of this writing:
    version:source-file-sha256:source-file-length

* version: The version of Opacify that the manifest was built with.
* source-file-sha256: The sha256 of the input file. This is used to validate on depacify.
* source-file-length: The length of the input file. This is also used to validate on depacify.

# TODO

## Auto External Sources

Instead of having to compile a list of sources to build from, provide a way to auto-build this source
from common locations (e.g. imgur, giphy, reddit, etc). Depending on the input file size, this could
take an extremely long time.

```bash
$ opacify -o --input-file test.txt --external-sources-auto --manifest test.opacify --verbose
Running pacify on test.txt and finding external sources ...
Status: Found source http://foo.com/hello.txt for offset 0, using 32 bytes
Status: Found source http://foo.com/foo.gif for offset 32, using 12 bytes
...
Status: Complete!
Runtime: 24 minutes
```
