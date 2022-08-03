import os
import shutil
import re
import stat
import zipfile
from threading import Thread
from concurrent.futures import ThreadPoolExecutor, wait


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


def walk(path, prev_list_dir=[], exclude=[]):
    os.chdir(path)
    list_files = list(filter(os.path.isfile, os.listdir()))
    list_files = [os.path.join(path, file) for file in list_files]
    list_dir = list(filter(os.path.isdir, os.listdir()))
    list_dir = [f for f in list_dir if f not in exclude]
    sub_dirs = [fr'{path}\{el}' for el in list_dir]
    n_dirs = len(list_dir)

    with ThreadPoolExecutor() as executor:
        new_list_files = executor.map(walk, sub_dirs, [list_dir]*n_dirs)

    list_files += new_list_files
    return list_files


def file_type(file_path):
    parts = file_path.upper().split(".")
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
    pattern = "[^a-zA-Z]"
    new_file_name = re.sub(pattern, "_", file_name[0])
    new_file_name = new_file_name + "." + file_name[1]
    return new_file_name


def normalize(file_name):
    new_file_name = translate(file_name)
    new_file_name = non_alpha(new_file_name)
    return new_file_name


def on_rm_error( func, path, exc_info):
    os.chmod( path, stat.S_IWRITE )
    os.unlink( path )


def move_file(file_path, path):
    f = file_path
    f_type = file_type(file_path=f)
    if RULES.get(f_type) == 'archives\\':
        shutil.unpack_archive(f, os.path.join(path, 'archives\\', os.path.basename(f).rsplit(".", 1)[0]))
        os.remove(f)
    elif f_type in RULES:
        new_file_path = os.path.join(path, RULES[f_type], normalize(os.path.basename(f)))
        shutil.move(f, new_file_path)
    else:
        new_file_path = os.path.join(path, 'others\\', normalize(os.path.basename(f)))
        shutil.move(f, new_file_path)


def sorter(path):
    new_folders = ['images', 'video', 'documents', 'music', 'archives', 'others']
    files = walk(path=r'D:\projects\data\Susanna_sort', exclude=new_folders)

    for folder in new_folders:
        new_path = os.path.join(path, folder)
        if not os.path.exists(new_path):
            os.mkdir(new_path)

    with ThreadPoolExecutor() as executor:
        executor.map(move_file, files, [path]*len(files))

    list_dir = os.listdir(path)
    for folder in list_dir:
        if folder not in new_folders:
            shutil.rmtree(os.path.join(path, folder), onerror=on_rm_error, ignore_errors=True)

    list_types = []
    stats = {}
    for folder in new_folders:
        list_files = walk(os.path.join(path, folder))
        list_files = [os.path.basename(f) for f in list_files]
        list_types.extend(list(set([get_type(f) for f in list_files])))
        stats.update({folder: list_files})
    print(f"Sorted files {stats}")

    known_types = list(set([t for t in list_types if t in RULES.keys()]))
    unknown_types = list(set([t for t in list_types if t not in RULES.keys()]))

    print(f"Known file types: {known_types}")
    print(f"Unknown file types: {unknown_types}")


if __name__ == '__main__':
    dir_path = r'D:\projects\data\Susanna_sort'
    shutil.rmtree(dir_path)
    with zipfile.ZipFile(dir_path + '.zip', 'r') as zip_ref:
        zip_ref.extractall(dir_path)

    sorter(r'D:\projects\data\Susanna_sort')


