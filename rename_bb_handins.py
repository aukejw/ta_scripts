'''
Assumes you have 7z (p7zip-full) and unrar installed.

Automatically extracts zips/rars/7zs (but not yet tarballs) and places
contents in folders based on the corresponding txtfile.
'''

import argparse
import logging
import os
import subprocess
import tarfile
import traceback
import zipfile

rarfile_present = True
try:
    import rarfile
except ImportError:
    print "Uses rarfile (https://pypi.python.org/pypi/rarfile/2.2)"
    rarfile_present = False


def log(msg, nl=True, force=False):
    '''Output based on global var 'verbose' '''
    if (verbose or force) and nl:
        print msg
    elif verbose or force:
        print msg,


def try_createfolder(path):
    '''Creates a folder if it does not exist already'''
    if not os.path.exists(path):
        os.makedirs(path)


def try_unpack(file_path, file_instance, destination, file_handle,
               msg_success="Success!"):
    '''
    Try to unpack a given rar/zip/tarfile instance, indicate if something
    goes wrong!
    '''
    try:
        file_instance.extractall(path=destination)
        os.remove(file_path)
        logging.info(file_handle + msg_success)
    except:
        logging.error("{} Something went wrong!\n\n{}\n\n".format(
            file_handle, traceback.format_exc()))


def main(source, destination, recursive):
    '''
    Main function which checks filetype of input, and unpacks accordingly.
    '''

    # First, determine whether input is a gradebook zip or unpacked folder
    logging.info("Renaming and unpacking '{}'".format(source))
    if zipfile.is_zipfile(source):
        if not destination:
            logging.warning("Destination not given, using source name.")
            destination = source[:-4]
            try_createfolder(source)
        zf = zipfile.ZipFile(source)
        zf.extractall(path=destination)
        # TODO remove original zipfile
        folder_name = destination
    elif os.path.isdir(source):
        folder_name = source
    else:
        logging.error("Source is neither zipfile nor folder! Stopped.")
        return

    # Find all text files with corresponding handin zips
    all_files = list(os.listdir(folder_name))
    for txtfile_name in (f for f in all_files if f.lower().endswith('.txt')):
        txtfile_fullpath = os.path.join(folder_name, txtfile_name)
        txtfile_prefix = txtfile_name[:-4]

        # Create a folder to put handins in
        with open(os.path.join(folder_name, txtfile_name), 'r') as txt:
            # BB text files have name on the first line
            firstline = txt.readline().split()
            name = ''.join(firstline[1:-1])
            student_nr = firstline[-1]

            # Create folders if necessary
            newfolder_name = '{}_{}'.format(name, student_nr)
            newfolder_fullpath = os.path.join(folder_name, newfolder_name)
            try_createfolder(newfolder_fullpath)

            # Find all matching files, then move or unpack
            file_names = [f for f in all_files
                          if (f.startswith(txtfile_prefix)
                              and not f.endswith('.txt'))]
            if file_names:
                log("Found matches for '{}':".format(txtfile_name))
                os.rename(txtfile_fullpath,
                          os.path.join(newfolder_fullpath,
                                       '_bb_description.txt'))
            unpack_or_move_all(file_names, folder_name, txtfile_prefix,
                               newfolder_fullpath, recursive)
    logging.info("Done.")


def unpack_or_move_all(list_of_file_names, original_path, txtfile_prefix,
                       destination, recursive):
    '''
    Unpack or move all files at original_path/filename to destination folder.
    Recursive is a boolean indicating that unpacked items must also be
    traversed and unpacked if possible.
    '''
    for file_name in list_of_file_names:
        file_fullpath = os.path.join(original_path, file_name)
        msg = "     '{}{}{}'".format(file_name[:40],
                                     ('...' if len(file_name) > 40 else ''),
                                     (file_name[-4:] if len(file_name) > 40
                                      else '')).rjust(50)
        # Zips/rars/tars can be handled similarly
        if zipfile.is_zipfile(file_name):
            zf = zipfile.ZipFile(file_fullpath)
            try_unpack(file_fullpath, zf, destination, msg + ".. unzipped")
        elif rarfile_present and rarfile.is_rarfile(file_fullpath):
            rf = rarfile.RarFile(file_fullpath)
            try_unpack(file_fullpath, rf, destination, msg + ".. unrarred")
        elif tarfile.is_tarfile(file_fullpath):
            tf = tarfile.open(file_fullpath)
            try_unpack(file_fullpath, tf, destination, msg + ".. untarred")
        # 7z is handled differently...
        elif file_name.lower().endswith('.7z'):
            # Call 7z to unpack, yes to all queries
            subprocess.Popen(
                ['7z', 'e', file_fullpath, '-o' + destination, '-y'],
                stdout=open(os.devnull, 'w'))
            os.remove(file_fullpath)
            logging.info(msg + ".. un7zipped")
        else:
            # If a file starts with prefix, remove prefix
            if file_name.startswith(txtfile_prefix):
                # Remove the prefix +1 for the added '_'
                file_destination = \
                    os.path.join(destination,
                                 file_name[len(txtfile_prefix) + 1:])
            else:
                file_destination = os.path.join(destination, file_name)
            # And move the file
            os.rename(file_fullpath, file_destination)
            logging.info(msg + ".. moved")

        # If recursive, check the destination folder for zips/tars/rars/7zs
        if recursive:
            files_to_unpack = [f for f in os.listdir(destination) if
                               f.lower().endswith(
                                   ('.zip', '.tar.gz', '.rar', '.7z'))]
            if files_to_unpack:
                unpack_or_move_all(files_to_unpack, original_path=destination,
                                   destination=destination, recursive=True)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Unpacking tool for blackboard gradebooks.",
        epilog=".. I'm in no way responsible for messing up any files!")
    arg_parser.add_argument('source', help='Input folder/zipfile')
    arg_parser.add_argument('-d', '--destination',
                            help='Output folder. Ignored if source is a' +
                            'folder.')
    arg_parser.add_argument('-v', '--verbose', action='store_const',
                            const=True, default=False, help="Verbosity")
    arg_parser.add_argument('-r', '--recursive_unpack', action='store_const',
                            const=False, default=True,
                            help="Turn off recursive unpacking" +
                            "(why would you ever do this?)")
    args = arg_parser.parse_args()

    global verbose   # necessary?
    verbose = args.verbose

    main(source=args.source, destination=args.destination,
         recursive=args.recursive_unpack)
