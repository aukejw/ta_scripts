'''
Assumes you have 7z (p7zip-full) and unrar installed.

Automatically extracts zips/rars/7zs (but not yet tarballs) and places
contents in folders based on the corresponding txtfile.
'''

import os
import sys
import zipfile
import subprocess

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


def unpack(fullpath, file_instance, new_foldername):
    '''Unpack the file! remove file itself!'''
    for file_in_pack in file_instance.namelist():
        file_instance.extract(file_in_pack, foldername)
    os.remove(fullpath)
    log(".. unzipped" if isinstance(file_instance, zipfile.ZipFile)
        else ".. unrarred")


if __name__ == "__main__":
    global verbose
    verbose = False
    if len(sys.argv) == 3 and sys.argv[2] == '-v':
        verbose = True
    foldername = sys.argv[1]

    log("Renaming and unpacking '{}'".format(foldername))

    all_files = list(os.listdir(foldername))

    # Find all text files with corresponding handin zips
    for txtfile_name in (f for f in all_files if f.lower().endswith('txt')):
        print txtfile_name
        txtfile_fullpath = os.path.join(foldername, txtfile_name)
        prefix = txtfile_name[:-4]

        # Create a folder to put handins in
        with open(os.path.join(foldername, txtfile_name), 'r') as txt:
            firstline = txt.readline().split()
            name = ''.join(firstline[1:-1])
            student_nr = firstline[-1]

            new_foldername = os.path.join(foldername, '{}_{}'.
                                          format(name, student_nr))
            if not os.path.exists(new_foldername):
                os.makedirs(new_foldername)

        # Find all files that match
        matching_file_names = [f for f in all_files
                               if (f.startswith(prefix)
                                   and not f.endswith('.txt'))]
        if matching_file_names:
            os.rename(txtfile_fullpath, os.path.join(new_foldername,
                                                     '_bb_description.txt'))
        for matching_file_name in matching_file_names:
            match_fullpath = os.path.join(foldername, matching_file_name)
            log("Found matching txt and file '{}'".format(matching_file_name),
                nl=False)
            # Zips and rars can be handled similarly
            if matching_file_name.lower().endswith('.zip'):
                unpack(match_fullpath, zipfile.ZipFile(match_fullpath),
                       new_foldername)
            elif rarfile_present and rarfile.is_rarfile(match_fullpath):
                unpack(match_fullpath, rarfile.RarFile(match_fullpath),
                       new_foldername)
            # 7z is handled differently...
            elif matching_file_name.lower().endswith('.7z'):
                # Call 7z to unpack, yes to all queries
                subprocess.call(['7z', 'e', match_fullpath,
                                 new_foldername, '-y'])
                os.remove(match_fullpath)
                log(".. un7zipped")
            else:
                os.rename(match_fullpath,
                          os.path.join(new_foldername, matching_file_name))
                log(".. moved")
            # TODO targzs
    log("Done.")
