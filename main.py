import os
import shutil
import re
import stat
import zipfile

from pathlib import Path
from asyncio import run, gather
from aiopathlib import AsyncPath


CYRILLIC_SYMBOLS = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяєіїґАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯЄІЇҐ"
TRANSLATION = (
    "a", "b", "v", "g", "d", "e", "e", "j", "z", "i", "j", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
    "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "u", "ja", "je", "ji", "g",
    "A", "B", "V", "G", "D", "E", "E", "J", "Z", "I", "J", "K", "L", "M", "N", "O", "P", "R", "S", "T", "U",
    "F", "H", "TS", "CH", "SH", "SCH", "", "Y", "", "E", "YU", "U", "JA", "JE", "JI", "G"
)

RULES = {'JPEG': 'images\\', 'PNG': 'images\\', 'JPG': 'images\\', 'SVG': 'images\\',
         'AVI': 'video\\', 'MP4': 'video\\', 'MOV': 'video\\', 'MKV': 'video\\',
         'DOC': 'documents\\', 'DOCX': 'documents\\', 'TXT': 'documents\\', 'PDF': 'documents\\', 'XLSX': 'documents\\',
         'PPTX': 'documents\\',
         'MP3': 'music\\', 'OGG': 'music\\', 'WAV': 'music\\', 'AMR': 'music\\',
         'ZIP': 'archives\\', 'GZ': 'archives\\', 'TAR': 'archives\\'}


def file_type(file_path):
    parts = str(file_path).upper().split(".")
    return parts[-1]


def translate(name):
    trans = {}
    for c, l in zip(CYRILLIC_SYMBOLS, TRANSLATION):
        trans[ord(c)] = l
    return name.translate(trans)


def get_type(file_name):
    return file_name.rsplit(".", 1)[1].upper()


def non_alpha(file_name):
    file_name = file_name.rsplit(".", 1)
    pattern = "[^a-zA-Z0-9]"
    new_file_name = re.sub(pattern, "_", file_name[0])
    new_file_name = new_file_name + "." + file_name[1]
    return new_file_name


def normalize(file_name):
    new_file_name = translate(file_name)
    new_file_name = non_alpha(new_file_name)
    return new_file_name


def on_rm_error( func, folder_path, exc_info):
    os.chmod( folder_path, stat.S_IWRITE )
    os.unlink( folder_path )


async def move_file(file_path, folder_path):
    f = AsyncPath(file_path)
    f_type = file_type(file_path=f)
    if not f.exists():
        return
    if RULES.get(f_type) == 'archives\\':
        await shutil.unpack_archive(str(f), os.path.join(folder_path, 'archives\\', os.path.basename(f).rsplit(".", 1)[0]))
        await f.unlink()
    elif f_type in RULES:
        new_file_path = os.path.join(folder_path, RULES[f_type], normalize(os.path.basename(f)))
        if not Path(new_file_path).exists():
            try:
                await f.rename(new_file_path)
            except FileExistsError:
                await f.rename(new_file_path.replace('.', '_.'))
    else:
        new_file_path = os.path.join(folder_path, 'others\\', normalize(os.path.basename(f)))
        if not Path(new_file_path).exists():
            try:
                await f.rename(new_file_path)
            except FileExistsError:
                await f.rename(new_file_path.replace('.', '_.'))


async def sorter(folder_path):
    home = AsyncPath(folder_path)
    files = [p for p in AsyncPath.glob(home, '**/*.*')]

    new_folders = ['images', 'video', 'documents', 'music', 'archives', 'others']
    print(files)

    for folder in new_folders:
        new_path = os.path.join(folder_path, folder)
        if not os.path.exists(new_path):
            os.mkdir(new_path)

    scrapers = [move_file(f, folder_path) for f in files]

    await gather(*scrapers)

    list_dir = os.listdir(folder_path)
    for folder in list_dir:
        if folder not in new_folders:
            shutil.rmtree(os.path.join(folder_path, folder), onerror=on_rm_error, ignore_errors=True)

    list_types = []
    stats = {}
    for folder in new_folders:
        list_files = [str(f) for f in Path(folder_path).rglob(f'{folder}/*.*')]
        list_files = [os.path.basename(f) for f in list_files]
        list_types.extend(list(set([get_type(f) for f in list_files])))
        stats.update({folder: list_files})
    print(f"Sorted files {stats}")

    known_types = list(set([t for t in list_types if t in RULES.keys()]))
    unknown_types = list(set([t for t in list_types if t not in RULES.keys()]))

    print(f"Known file types: {known_types}")
    print(f"Unknown file types: {unknown_types}")
    return


async def amain(folder_path):
    await sorter(folder_path)


def main(folder_path):
    run(amain(folder_path))


if __name__ == '__main__':
    dir_path = r'D:\projects\data\Susanna_sort'
    shutil.rmtree(dir_path)
    with zipfile.ZipFile(dir_path + '.zip', 'r') as zip_ref:
        zip_ref.extractall(dir_path)

    main(r'D:/projects/data/Susanna_sort')

