# -*- coding: utf-8 -*-
import argparse

import hitomi

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artist", help = "artist name", type = str)
    parser.add_argument("-s", "--series", help = "series", type = str)
    parser.add_argument("-c", "--character", help = "character", type = str)
    parser.add_argument("-w", "--worktype", help = "type of work", choices = ["doujinshi", "artistcg", "gamecg", "manga"])
    parser.add_argument("-t", "--tags", help = "tags. you can specify more than one.", nargs='+', default = ["index"])
    parser.add_argument("-l", "--language", help = "language", type = str, default = "all")
    parser.add_argument("-q", "--quiet", help = "do not print errors.", action = "store_true")
    args = parser.parse_args()

    return args 

def main():
    args = parse_args()
    worktype = None
    if args.worktype != None:
        for a in hitomi.ArtType:
            if args.worktype == a.value:
                worktype = a
                break
        else:
            print("invalid worktype.")
            return

    try:
        result = hitomi.search(artist = args.artist, series = args.series, character = args.character, art_type = worktype, tags = args.tags, language = args.language)
    except hitomi.urllib.error.HTTPError:
        if not args.quiet:
            print("no items found.")
    else:
        print(" ".join(str(i) for i in list(result)))
    return

main()
