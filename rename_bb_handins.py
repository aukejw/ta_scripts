'''
Assumes you have 7z (p7zip-full) and unrar installed.

Automatically extracts zips/rars/7zs (but not yet tarballs) and places
contents in folders based on the corresponding txtfile.
'''

import os
import sys
import zipfile
import subprocess
import tarfile

rarfile_present = True
try:
    import rarfile
except ImportError:
    print "Uses rarfile (https://pypi.python.org/pypi/rarfile/2.2)"
    rarfile_present = False


def log(msg, nl=True):
    if verbose and nl:
        print msg
    elif verbose:
        print msg,


if __name__ == "__main__":
    global verbose
    verbose = False
    if len(sys.argv) == 3 and sys.argv[2] == '-v':
        verbose = True
    folder_name = sys.argv[1]

    log("Renaming and unpacking '{}'".format(folder_name))

    all_files = list(os.listdir(folder_name))

    # Find all text files with corresponding handin zips
    for txtfile_name in (f for f in all_files if f.lower().endswith('txt')):
        print txtfile_name
        txtfile_fullpath = os.path.join(folder_name, txtfile_name)
        prefix = txtfile_name[:-4]

        # Create a folder to put handins in
        with open(os.path.join(folder_name, txtfile_name), 'r') as txt:
            firstline = txt.readline().split()
            name = ''.join(firstline[1:-1])
            student_nr = firstline[-1]

            newfolder_name = os.path.join(folder_name, '{}_{}'.
                                          format(name, student_nr))
            if not os.path.exists(newfolder_name):
                os.makedirs(newfolder_name)
            matching_file_names = [f for f in all_files
                                   if (f.startswith(prefix)
                                       and not f.endswith('.txt'))]
            if matching_file_names:
                os.rename(txtfile_fullpath, os.path.join(newfolder_name,
                                                         '_bb_description.txt'))
            unpack_or_move_all(matching_file_names, folder_name,
                               newfolder_name)
            log("Done.")


def unpack_or_move_all(list_of_filenames, original_path,
                       destination, recursive=True):
    '''
    Unpack or move all files at original_path/filename to destination folder.
    Recursive is a boolean indicating that unpacked items must also be
    traversed and unpacked if possible.
    '''
    for file_name in list_of_file_names:
        fullpath = os.path.join(original_path, file_name)
        log("Found matching txt and file '{}'".format(matching_file_name),
            nl=False)
        # Zips and rars can be handled similarly
        if matching_file_name.lower().endswith('.zip'):
            zf = zipfile.ZipFile(fullpath)
            zf.extractall(path=destination)
        elif rarfile_present and rarfile.is_rarfile(fullpath):
            rf = rarfile.RarFile(fullpath)
            rf.extractall(path=destination)
        elif tarfile.is_tarfile(fullpath):
            tf = tarfile.open(fullpath)
            tf.extractall(path=destination)
        # 7z is handled differently...
        elif matching_file_name.lower().endswith('.7z'):
            # Call 7z to unpack, yes to all queries
            subprocess.call(['7z', 'e', fullpath,
                             newfolder_name, '-y'])
            os.remove(fullpath)
            log(".. un7zipped")
        else:
            os.rename(fullpath,
                      os.path.join(newfolder_name, matching_file_name))
            log(".. moved")
        # If recursive, check the destination folder for zips/tars/rars/7zs
        if recursive:
            files_to_unpack = [f for f in os.listdir(destination) if
                               f.lower().endswith(
                                   ('.zip', '.tar.gz', '.rar', '.7z'))]
            if files_to_unpack:
                unpack_or_move_all(files_to_unpack, original_path=destination,
                                   destination=destination, recursive=True)
