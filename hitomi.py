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
            pass
            #with open(download_path, "wb") as img_file:
            #    img_file.write(res.read())
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

SEARCH_DOMAIN = "https://ltn.hitomi.la/{}.nozomi"
def search_category(category: Category, value, language = "all") -> list:
    request_url = SEARCH_DOMAIN.format("{}/{}-{}".format(category.value, value, language))
    return fetch_ids(request_url)

def search_art_type(art_type: ArtType, language = "all") -> list:
    request_url = SEARCH_DOMAIN.format("type/{}-{}".format(category.value, language))
    return fetch_ids(request_url)

def search_tag(tag, language = "all") -> list:
    if tag == "index":
        request_url = SEARCH_DOMAIN.format("{}-{}".format(tag, language))
    else:
        request_url = SEARCH_DOMAIN.format("tag/{}-{}".format(tag, language))
    return fetch_ids(request_url)

def search_direct(category: Category, category_value, art_type: ArtType, tags, language) -> list:
    tag_result = search_tag(tags[0], language)
    for t in tags[1:]:
        result = search_tag(t, language)
        tag_result = filter(lambda x: x in t, tag_result)

    if category != None:
        if category_value == None:
            raise HitomiToolsException("empty category value.")
        category_result = search_category(category, category_value, language);
        tag_result = filter(lambda x: x in category_result, tag_result)

    if art_type != None:
        type_result = search_art_type(art_type, language);
        tag_result = filter(lambda x: x in type_result, tag_result)
    
    return tag_result

def search(artist = None, series = None, character = None, art_type: ArtType = None, tags = ["index"], language = "all") -> list:
    if artist == None and series == None and character == None:
        return search_direct(None, None, art_type, tags, language)
    
    artist_result = None
    series_result = None
    character_result = None
    if artist != None:
        artist_result = search_direct(category = Category.ARTIST, category_value = artist, art_type = art_type, tags = tags, language = language)
    if series != None:
      series_result = search_direct(category = Category.SERIES, category_value = series, art_type = art_type, tags = tags, language = language)
    if character != None:
        character_result = search_direct(category = Category.CHARACTER, category_value = character, art_type = art_type, tags = tags, language = language)
    
    if artist_result != None:
        if series_result != None:
            artist_result = filter(lambda x: x in series_result, artist_result)
        if character_result != None:
            artist_result = filter(lambda x: x in character_result, artist_result)
        return artist_result

    if series_result != None:
        if character_result != None:
            series_result = filter(lambda x: x in character_result, series_result)
        return series_result

    return character_result
