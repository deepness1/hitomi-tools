# -*- coding: utf-8 -*-
import argparse

import hitomi

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("galleryids", help = "gallary ids of work you want to download. you can specify more than one.", nargs = "*")
    parser.add_argument("-s", "--savedir", help = "directory to save pictures.(=./hitomi_downloads)", default = "hitomi_downloads")
    parser.add_argument("-j", "--threads", help = "number of parallel downloads.(=16)", default = 16, type = int)
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    for g in args.galleryids:
        g = g.replace(',', '')
        g = g.replace(' ', '')
        hitomi.Gallery(g).download(args.savedir, args.threads)
    return

main()
