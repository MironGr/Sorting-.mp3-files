import os.path as path
import os
import sys
import shutil
import argparse
import glob
from collections import namedtuple


from mp3_tagger import MP3File


def get_working_dirs():
    """
    Creates console commands ("-s", "--src-dir") and ("-d", "--dst-dir"),
    which default=os.getcwd()
    :return: namedtuple(src_dir, dst_dir)
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--src-dir",
                        help="set origin dir, example: \\name_dir\\... or example: D:\\name_dir\\...",
                        default=os.getcwd())
    parser.add_argument("-d", "--dst-dir",
                        help="set working dir, example: \\name_dir\\... or example: D:\\name_dir\\...",
                        default=os.getcwd())
    args = parser.parse_args()
    directs = namedtuple('Directs', 'src_dir dst_dir')
    return directs(args.src_dir, args.dst_dir)


def get_absolute_directory(directory):
    """
    Getting the absolute path from the relative depending on the OS
    :param directory: absolute or relative path
    :return: absolute path <class 'str'>
    """
    if sys.platform == 'win32' and directory[0] == '/':
        directory = f'{os.getcwd()}{directory}'
    elif sys.platform == 'linux' and directory[:4] != '/home':
        directory = f'{os.getcwd()}{directory}'
    return directory


def get_ID3v2_tags(mp3_file):
    """
    Extract ID3v2 tags (artist, album, song) from *.mp3. If ID3v2 tags missing or not file permissions equate
    (artist=None, album=None, song=None).
    :param mp3_file: some *.mp3
    :return: namedtuple(artist, album, song)
    """
    try:
        audio = MP3File(mp3_file).get_tags().get('ID3TagV2')
    except AttributeError:
        audio = None
    except PermissionError:
        audio = None
    tags_mp3 = namedtuple('Tags', 'artist album song')
    tags = None
    if not audio:
        tags = tags_mp3(None, None, None)
    else:
        try:
            artist = del_system_char(audio.get('artist').strip())
        except AttributeError:
            artist = None
        try:
            album = del_system_char(audio.get('album').strip())
        except AttributeError:
            album = None
        try:
            song = del_system_char(audio.get('song').strip())
        except AttributeError:
            song = None
        if artist and album and song:
            tags = tags_mp3(artist, album, song)
    return tags


def del_system_char(string):
    """
    Removes invalid characters '\/:*?"<>|' to avoid file name errors
    :param string: <class 'str'>
    :return: <class 'str'> no invalid characters
    """
    table = str.maketrans('', '', '\/:*?"<>|')
    return string.translate(table)


def replace_mp3(source_dir):
    """
    Renames with replacement *.mp3 to 'song - artist - album.mp3' where parts of the name are ID3v2 tags.
    If ID3v2 tags are missing, do not rename the *.mp3.
    :param source_dir: relative or absolute  path to directory with *.mp3
    """
    source_dir = get_absolute_directory(source_dir)
    for mp3_file in glob.glob(f'{source_dir}/*.mp3'):
        tags = get_ID3v2_tags(mp3_file)
        artist = tags.artist
        album = tags.album
        song = tags.song
        if artist and album and song:
            title_song = f'{song} - {artist} - {album}.mp3'
            os.replace(f'{mp3_file}', f'{source_dir}/{title_song}')


def create_directory_structure(source_dir, final_dir):
    """
    Creates a directory structure in the final_dir according to the scheme
    <final_dir>/<artist>/<album>/<file_name>.mp3. Or does nothing if not access rights.
    :param source_dir: relative or absolute  path to directory with *.mp3
    :param final_dir: relative or absolute  path to destination storage *.mp3
    """
    for mp3_file in glob.glob(f'{get_absolute_directory(source_dir)}/*.mp3'):
        tags = get_ID3v2_tags(mp3_file)
        artist = tags.artist
        album = tags.album
        if artist and album:
            try:
                os.makedirs(f'{get_absolute_directory(final_dir)}/{artist}/{album}', exist_ok=True)
            except PermissionError:
                continue     # обрабатываем искоючение и в move_mp3()


def move_mp3(source_dir, final_dir):
    """
    Moves *.mp3 files from the source_dir to the final_dir according to the scheme
    <final_dir>/<artist>/<album>/<file_name>.mp3.
    Display a log <source_dir>/<file_name>.mp3 -> <final_dir>/<file_name>.mp3.
    Or does nothing if there is no access rights or file is missing.
    :param source_dir: relative or absolute  path to directory with *.mp3
    :param final_dir: relative or absolute  path to destination storage *.mp3
    """
    source_dir = get_absolute_directory(source_dir)
    final_dir = get_absolute_directory(final_dir)
    for mp3_file in glob.glob(f'{source_dir}/*.mp3'):
        mp3_file_name = path.basename(mp3_file)
        tags = get_ID3v2_tags(mp3_file)
        artist = tags.artist
        album = tags.album
        if artist and album:
            print(f'{source_dir}/{mp3_file_name} -> {final_dir}/{mp3_file_name}')
            try:
                shutil.move(mp3_file, f'{final_dir}/{artist}/{album}')
            except shutil.Error:
                os.remove(f'{final_dir}/{artist}/{album}/{mp3_file_name}')
                shutil.move(mp3_file, f'{final_dir}/{artist}/{album}')
            except (PermissionError, FileNotFoundError):
                print(f'Нет прав доступа к папке / подпапкам {final_dir}')


def check_mp3_in_src_dir(source_dir):
    """
    Checks the remaining *.mp3 in the source_dir and display them.
    Or does nothing if there are no *.mp3.
    :param source_dir: relative or absolute  path to directory with *.mp3
    """
    source_dir = get_absolute_directory(source_dir)
    for mp3_file in glob.glob(f'{source_dir}/*.mp3'):
        mp3_file_name = path.basename(mp3_file)
        print(f'У файла "{mp3_file_name}" отсутствуют теги ID3v2 либо нет прав доступа к файлу')


if __name__ == '__main__':
    src_dir = get_working_dirs().src_dir
    dst_dir = get_working_dirs().dst_dir
    replace_mp3(src_dir)
    create_directory_structure(src_dir, dst_dir)
    move_mp3(src_dir, dst_dir)
    check_mp3_in_src_dir(src_dir)
