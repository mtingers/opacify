# -*- coding: utf-8 -*-
import sys
import time

prev_tail = '|'
tail = '|'
# Modified version of comment here:
#   https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
def progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='█', timer_start=None):
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
        timer_start - Optional  : for estimating remaining time (time.time())
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
    estimate = None
    if timer_start:
        duration = time.time() - timer_start
        estimate = (((1+duration) / float(iteration+1)) * (total - iteration)) / 60.0

    percent = ("{0:." + str(decimals) + "f}").format(100 * ((1+iteration) / float(total+1)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    if estimate:
        sys.stdout.write('\r%s |%s| %s %s%% %s  %.2fm remaining    \r' % (prefix, bar, tail, percent, suffix, estimate)) #, end = '\r')
    else:
        sys.stdout.write('\r%s |%s| %s %s%% %s\r' % (prefix, bar, tail, percent, suffix)) #, end = '\r')
    sys.stdout.flush()
    #if iteration == total:
    #    print('')


