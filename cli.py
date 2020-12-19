import hashlib
from hashlibcrc32 import *

filename = "/home/seigneurfuo/NAS/Vidéos/Séries et web séries/Hercule Poirot/Saison 1/H.Poirot.S01E01.La.cuisine.mysterieuse.de.Clapham.MULTI.1080p.x264 [A016D394].mkv"


def get_file_hash(filename, blocksize=2048, algorithm=hashlib.md5()):
    hash = algorithm
    with open(filename, "rb") as f:
        while True:
            data = f.read(blocksize)
            if not data:
                break
            hash.update(data)

    return hash.hexdigest()

def get_crc32_checksum(filename, blocksize=65536):
    import zlib

    with open(filename, 'rb') as f:
        data = f.read(blocksize)
        crcvalue = 0
        while len(data) > 0:
            crcvalue = zlib.crc32(data, crcvalue)
            data = f.read(blocksize)

    return format(crcvalue & 0xFFFFFFFF, '08x').upper()  # a509ae4b

text = get_crc32_checksum(filename)
print(text)