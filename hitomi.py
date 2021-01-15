# -*- coding: utf-8 -*-
import argparse
import enum
import json
import os
import threading
import urllib.request

class HitomiToolsException(Exception):
    pass

class Gallery():
    @staticmethod
    def get_gallery_info(galleryid) -> dict:
        url = "https://ltn.hitomi.la/galleries/{}.js".format(galleryid)
        index = urllib.request.urlopen(url).read().decode("utf-8")
        json_head_pos = index.find("=") + 1
        if json_head_pos == -1:
            raise(HitomiToolsException("bad index file."))
        return json.loads(index[json_head_pos:])

    def download_thread(self, savedir):
        while 1:
            with self.images_next_download_lock:
                if self.images_next_download >= len(self.images):
                    break

                image = self.images[self.images_next_download]
                self.images_next_download += 1
            saved_path = image.download(savedir)
            print(saved_path)

    def download(self, savedir, n_threads):
        if self.japanese_title != None:
            title = self.japanese_title
        else:
            title = self.title
        if title == None:
            title = "unknown {}".format(self.galleryid)
        savedir = "{}/{}".format(savedir, title)
        while 1: 
            try:
                os.makedirs(savedir)
            except FileExistsError:
                savedir = savedir + "_"
            else:
                break

        threads = []
        for i in range(n_threads):
            t = threading.Thread(target = self.download_thread, args = (savedir, ))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def __init__(self, galleryid):
        self.galleryid = galleryid

        # download gallery info
        try:
            info = self.get_gallery_info(self.galleryid)
        except urllib.error.HTTPError as e:
            print(e)
            raise HitomiToolsException("maybe wrong galleryid.")
        
        # parse tags
        self.tags = []
        if info["tags"] != None:
            for t in info["tags"]:
                tag = t["tag"]
                if "male" in t and t["male"] == "1":
                    tag = "male:" + tag
                elif "female" in t and t["female"] == "1":
                    tag = "female:" + tag

        # parse other info
        self.language = info["language"]
        self.title = info["title"]
        self.japanese_title = info["japanese_title"]
        self.type = info["type"]

        # build image URLs
        self.images = []
        for img in info["files"]:
            self.images.append(Image(self.galleryid, img))
        self.images_next_download_lock = threading.Lock()
        self.images_next_download = 0

class Image():
    def __init__(self, galleryid, image_info):
        self.galleryid = galleryid
        self.name = image_info["name"]
       
        ext = self.name[self.name.find("."):]
        hash_a = image_info["hash"][-1]
        hash_b = image_info["hash"][-3:-1]

        try:
            hash_num = int(hash_b, 16)
        except ValueError:
            raise HitomiToolsException("invalid hash number.")

        if hash_num < 0x30:
            number_of_frontends = 2
        else:
            number_of_frontends = 3

        if hash_num < 0x09:
            hash_num = 1

        subdomain = chr(97 + hash_num % number_of_frontends) + "b" ;
        self.image_url = "https://{}.hitomi.la/images/{}/{}/{}{}".format(subdomain, hash_a, hash_b, image_info["hash"], ext)

    def download(self, parent_dir):
        request = create_request(self.image_url)
        request.add_header("Referer", "https://hitomi.la/reader/{}.html".format(self.galleryid))

        download_path = parent_dir + "/" + self.name
        with urllib.request.urlopen(request) as res:
            with open(download_path, "wb") as img_file:
                img_file.write(res.read())
        return download_path

def create_request(url):
    return urllib.request.Request(urllib.parse.quote(url, safe=':/'))

class Category(enum.Enum):
    ARTIST = "artist"
    SERIES = "series"
    CHARACTER = "character"

class ArtType(enum.Enum):
    DOUJINSHI = "doujinshi"
    ARTISTCG = "artistcg"
    GAMECG = "gamecg"
    MANGA = "manga"

def fetch_ids(request_url) -> list:
    request = create_request(request_url)
    request.add_header("Content-Type", "application/octet-stream")
    with urllib.request.urlopen(request) as res:
        arr = res.read()
        ids = []
        arr_len = (len(arr) / 4)
        for i in range(0, int(arr_len)):
            ids.append(int.from_bytes(arr[i * 4:(i + 1) * 4], byteorder='big', signed=False))
    return ids

def filter_ids(id_lists) -> list:
    if len(id_lists) == 0:
        raise HitomiToolsException("empty id list.")
    elif len(id_lists) == 1:
        return id_lists[0]
    base_lists = id_lists[0]
    for i in id_lists[1:]:
        if len(i) < len(base_lists):
            base_lists = i
    id_lists.remove(base_lists)
    for bid in base_lists[:]:
        for lst in id_lists:
            dss = len(lst)
            rng = [0, len(lst) - 1]
            sep = int((len(lst) - 1) / 2)
            while dss > 1:
                dss /= 2
                if bid > lst[sep]:
                    rng[1] = sep
                    sep -= int(dss)
                elif bid < lst[sep]:
                    rng[0] = sep
                    sep += int(dss)
                else:
                    break
            else:
                if not bid in lst[rng[0]:rng[1]]:
                    base_lists.remove(bid)
                    break
    return base_lists

SEARCH_DOMAIN = "https://ltn.hitomi.la/{}.nozomi"
def search_category(category: Category, value, language = "all") -> list:
    request_url = SEARCH_DOMAIN.format("{}/{}-{}".format(category.value, value, language))
    return fetch_ids(request_url)

def search_art_type(art_type: ArtType, language = "all") -> list:
    request_url = SEARCH_DOMAIN.format("type/{}-{}".format(art_type.value, language))
    return fetch_ids(request_url)

def search_tag(tag, language = "all") -> list:
    if tag == "index":
        request_url = SEARCH_DOMAIN.format("{}-{}".format(tag, language))
    else:
        request_url = SEARCH_DOMAIN.format("tag/{}-{}".format(tag, language))
    return fetch_ids(request_url)

def search_direct(category: Category, category_value, art_type: ArtType, tags, language) -> list:
    id_lists = []
    for t in tags:
        id_lists.append(search_tag(t, language))

    if category != None:
        if category_value == None:
            raise HitomiToolsException("empty category value.")
        id_lists.append(search_category(category, category_value, language))

    if art_type != None:
        id_lists.append(search_art_type(art_type, language))
    
    return filter_ids(id_lists)

def search(artist = None, series = None, character = None, art_type: ArtType = None, tags = ["index"], language = "all") -> list:
    if artist == None and series == None and character == None:
        return search_direct(None, None, art_type, tags, language)

    id_lists = []
    if artist != None:
        id_lists.append(search_direct(category = Category.ARTIST, category_value = artist, art_type = art_type, tags = tags, language = language))
    if series != None:
        id_lists.append(search_direct(category = Category.SERIES, category_value = series, art_type = art_type, tags = tags, language = language))
    if character != None:
        id_lists.append(search_direct(category = Category.CHARACTER, category_value = character, art_type = art_type, tags = tags, language = language))

    return filter_ids(id_lists)
