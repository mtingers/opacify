# Opacify

Opacify reads a file and builds a manifest of external sources to rebuild said file.

# Examples

## Opacify A File
```
$ opacify -o --input-file test.txt --external-sources sources.txt --manifest test.opacify
Running pacify on test.txt using sources.txt ...
Status: 100% ... Complete!
```

## Depacify A File
```
$ opacify -d --manifest test.opacify -save test-depacify.txt
Running depacify on test.opacify ...
Status: 100% ... Complete!
```

## Validate Manifest
As time goes by, external sources may disappear or content may change. The following will check that the source
exists (has a valid HTTP response) and check that the source provides enough data of offset+length:
```
$ opacify --verify-external-sources --manifest test.opacify
Validating external sources listed in manifest ...
Status: 100% ... Complete!
```

## Errors
Fail to pacify:
```
$ opacify --pacify --input-file test.txt --external-sources sources.txt --manifest test.opacify
Running pacify on test.txt using sources.txt ...
Status: 54% ... ERROR:
    Not enough external sources to complete manifest!
```

Fail to depacify (external sources changed):
```
$ opacify --depacify --manifest test.opacify -save test-depacify.txt
Running depacify on test.opacify ...
Status: 23% ... ERROR:
    Failed to extract source:
        http://foo/bar.jpg
    Partial contents are located at:
         test-depacify.txt
```

Fail to depacify (external sources changed), but continue on:
```
$ opacify --depacify --manifest test.opacify -save test-depacify.txt --continue
Running depacify on test.opacify ...
Status: 23% ...
ERROR: External source http://foo/bar.jpg failed at offset 32, 40 bytes.
ERROR: External source http://foo/bar.jpg failed at offset 44, 20 bytes..
    We tried our best but not all external sources were good.
    Partial contents are located at:
         test-depacify.txt
```

Fail to validate sha256 or length on depacify:
```
$ opacify --depacify --manifest test.opacify -save test-depacify.txt
Running depacify on test.opacify ...
Status: 44% ...ERROR:
    SHA256 does not match manifest! The data is likely invalid!
    Output file was still saved to:
         test-depacify.txt
```
```
$ opacify --depacify --manifest test.opacify -save test-depacify.txt
Running depacify on test.opacify ...
Status: 12% ... ERROR:
    Length does not match manifest! The data is likely invalid!
    This should not happen, there may be a bug in Opacify
    OR a problem with your system!
    Output file was still saved to:
         test-depacify.txt
```

Fail to validate manifest:
```
$ opacify --verify-external-sources --manifest test.opacify
Validating external sources listed in manifest ...
Status: 55% ... ERROR:
    Source http://foo.bar.jpg returned an invalid response!
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

## Auto External Sources

Instead of having to compile a list of sources to build from, provide a way to auto-build this source
from common locations (e.g. imgur, giphy, reddit, etc). Depending on the input file size, this could
take an extremely long time.

```
$ opacify -o --input-file test.txt --external-sources-auto --manifest test.opacify --verbose
Running pacify on test.txt and finding external sources ...
Status: Found source http://foo.com/hello.txt for offset 0, using 32 bytes
Status: Found source http://foo.com/foo.gif for offset 32, using 12 bytes
...
Status: Complete!
Runtime: 24 minutes
```
