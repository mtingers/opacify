# -*- coding: utf-8 -*-
import sys

prev_tail = '|'
tail = '|'

# Modified version of comment here:
#   https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
def progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    global tail, prev_tail
    if tail == '.':
        tail = '*'
    else:
        tail = '.'
    """if prev_tail == '|':
        prev_tail = tail
        tail = '/'
    elif prev_tail == '/':
        prev_tail = tail
        tail = '-'
    elif prev_tail == '-':
        prev_tail = tail
        tail = '\\'
    elif prev_tail == '\\':
        prev_tail = tail
        tail = '|'
    """

    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write('\r%s |%s| %s %s%% %s\r' % (prefix, bar, tail, percent, suffix)) #, end = '\r')
    sys.stdout.flush()
    #if iteration == total:
    #    print('')


