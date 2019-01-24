import sys
import os
import time
import argparse
from opacify import Opacify, StatusCodes
from opacify import INFOTXT, EPILOG
from opacify import reddit

def version():
    return INFOTXT

#if __name__ == '__main__':
def main():
    parser = argparse.ArgumentParser(
        description=INFOTXT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG
    )
    subparser = parser.add_subparsers(dest='func')
    if sys.version_info[0] < 3:
        subparser.required = True
    group1 = subparser.add_parser('pacify', description='Run in pacify mode (builds manifest from input file)',
         help='Run in pacify mode (builds manifest from input file)')
    group2 = subparser.add_parser('satisfy', description='Run in satisfy mode (rebuilds file using manifest)',
        help='Run in satisfy mode (extracts file using manifest)')
    group3 = subparser.add_parser('verify', description='Validate manifest URLs and response length',
        help='Validate manifest URLs and response length')
    group4 = subparser.add_parser('reddit', description='Auto-generate a urls file from reddit links',
        help='Auto-generate a urls file from reddit links')
    # Pacify
    group4.add_argument('-o', '--out', required=True, help='Path to write urls to')
    group4.add_argument('-c', '--count', required=True, help='How many links to get')
    group1.add_argument('-i', '--input', required=True, help='Path to input file')
    group1.add_argument('-u', '--urls', required=True, help='Path to urls file')
    group1.add_argument('-m', '--manifest', required=True, help='Output path of manifest file')
    group1.add_argument('-c', '--cache', required=True, help='Path to cache directory')
    group1.add_argument('-k', '--keep', action='store_const', const=True,
        help='Do not remove cache after completed. Useful for testing')
    group1.add_argument('-f', '--force', action='store_const', const=True, help='Overwrite manifest if it exists')
    group1.add_argument('-d', '--debug', action='store_const', const=True, help='Turn on debug output')
    group1.add_argument('-t', '--threads', help='Run processing multiple threads')
    # Satisfy
    group2.add_argument('-m', '--manifest', required=True, help='Path of manifest file')
    group2.add_argument('-o', '--out', required=True, help='Path to write output file to')
    group2.add_argument('-c', '--cache', required=True, help='Path to cache directory')
    group2.add_argument('-k', '--keep', action='store_const', const=True,
        help='Do not remove cache after completed. Useful for testing')
    group2.add_argument('-f', '--force', action='store_const', const=True, help='Overwrite output file if it exists', default=False)
    group2.add_argument('-d', '--debug', action='store_const', const=True, help='Turn on debug output')
    group3.add_argument('-m', '--manifest', required=True, help='Path of manifest file')
    group3.add_argument('-d', '--debug', action='store_const', const=True, help='Turn on debug output')
    parser.add_argument('-V', '--version', help='Display Opacify version info',
        action='version', version=version()) #'%(prog)s '+VERSION)
    args = parser.parse_args()
    cache = 'cache'
    if args.func in ('pacify', 'satisfy'):
        if args.cache:
            cache = args.cache
    start_timer = time.time()
    debug = getattr(args, 'debug', False)
    n_threads = getattr(args, 'threads', None)
    o = Opacify(cache_dir=cache, debug=debug)
    if args.func == 'pacify':
        r = o.pacify(
            input_file=args.input,
            url_file=args.urls,
            manifest=args.manifest,
            overwrite=args.force,
            keep_cache=args.keep,
            threads=n_threads,
        )
        print('\n')
        end_timer = time.time()
        avg_chunk_size = (o.total_chunk_size+1) / float(o.total_chunks+1)
        #if type(r) != tuple:
        if r != StatusCodes.OK:
            print('ERROR: Failed to pacify:')
            for status in o.results.get():
                for i in range(len(status.codes)):
                    code = status.codes[i]
                    msg = status.messages[i]
                    if code == StatusCodes.OK: continue
                    print('%s: %s' % (code.name, msg))
        else:
            print('Wrote manifest to: %s' % (args.manifest))
            print('   Avg chunk size: %.2f' % (avg_chunk_size))
            print('     Total chunks: %s' % (o.total_chunks))
            print('    Manifest size: %s' % (os.path.getsize(args.manifest)))
            #print('    Original size: %s' % (r[1]))
            #print('     Input sha256: %s' % (r[0]))
            print('    Original size: %s' % (o.clength))
            print('     Input sha256: %s' % (o.digest))
            print('         Duration: %.3fs' % (end_timer - start_timer))
    elif args.func == 'satisfy':
        r = o.satisfy(manifest=args.manifest, out_file=args.out, keep_cache=args.keep, overwrite=args.force)
        print('\n')
        #if type(r) != tuple:
        if r != StatusCodes.OK:
            print('ERROR: Failed to satisfy:')
            for status in o.results.get():
                for i in range(len(status.codes)):
                    code = status.codes[i]
                    msg = status.messages[i]
                    if code == StatusCodes.OK: continue
                    print('%s: %s' % (code.name, msg))
        else:
            end_timer = time.time()
            print('    Manifest size: %s' % (os.path.getsize(args.manifest)))
            print('    Output sha256: %s' % (o.digest))
            print('      Output size: %s' % (o.clength))
            print('         Duration: %.3fs' % (end_timer - start_timer))
    elif args.func == 'reddit':
        print('Generating urls from reddit data...')
        mode = 'w'
        if os.path.exists(args.out):
            print('NOTE: %s exists. Appending to file.' % (args.out))
            mode = 'a'
        links = reddit.reddit_get_links(count=args.count, sleep=5, giveup=600)
        with open(args.out, mode) as f:
            for link in links:
                f.write('%s\n' % (link))
        print('Wrote urls data to: %s' % (args.out))

    else:
        parser.print_help()
        if args.func:
            if args.func != 'func':
                print("")
                print('NOTICE: Not yet implemented: %s' % (args.func))
                print("")
    if r == StatusCodes.OK:
        for status in o.results.get():
            for i in range(len(status.codes)):
                code = status.codes[i]
                msg = status.messages[i]
                if code == StatusCodes.OK: continue
                print('%s: %s' % (code.name, msg))
