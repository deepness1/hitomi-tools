# -*- coding: utf-8 -*-
import argparse
import sys

import hitomi

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--galleryids", help = "gallary ids of work you want to download. you can specify more than one.", nargs = "*", type = int)
    parser.add_argument("-s", "--savedir", help = "directory to save pictures.(=./hitomi_downloads)", default = "hitomi_downloads")
    parser.add_argument("-j", "--threads", help = "number of parallel downloads.(=16)", default = 16, type = int)
    args = parser.parse_args()
    return args

def main():
    if not sys.stdin.isatty():
        input_ids = [int(x.strip()) for x in sys.stdin.read().split(" ")]
    else:
        input_ids = []
    args = parse_args()
    if args.galleryids != None:
        input_ids += args.galleryids
    print(input_ids)
    return;
    for g in input_ids:
        g = g.replace(',', '')
        g = g.replace(' ', '')
        hitomi.Gallery(g).download(args.savedir, args.threads)
    return

main()
