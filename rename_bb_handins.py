#!/usr/bin/python
'''
Assumes you have unzip, 7z (p7zip-full) and unrar installed.
Also tries to use unidecode to remove special chars from names.

List of features:
    - Creates folders for each handin based on student name + nr
    - Extracts tars/zips/7zs/rars
    - Flattens single-folder handins (from tars, for example)
    - Moves files to handin-folders
    - Uses python logging for user feedback
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
    print "Uses rarfile (https://pypi.python.org/pypi/rarfile/2.2),"\
        + " which currently isn't present!"
    raw_input("Press enter to continue...")
    rarfile_present = False


def try_createfolder(path):
    '''Creates a folder if it does not exist already'''
    if not os.path.exists(path):
        os.makedirs(path)


def try_unpack(file_path, destination, file_handle, msg_success="Success!"):
    '''
    Try to unpack a given rar/zip/tarfile instance, indicate if something
    goes wrong! Returns true if unpacked.
    '''
    # For some reason, cmaps can be unzipped...
    if zipfile.is_zipfile(file_path) and not file_path.endswith('.cmap'):
        file_instance = zipfile.ZipFile(file_path)
        msg_success = " unzipped."
    elif rarfile_present and rarfile.is_rarfile(file_path):
        file_instance = rarfile.RarFile(file_path)
        msg_success = " unrarred."
    elif tarfile.is_tarfile(file_path):
        file_instance = tarfile.open(file_path)
        msg_success = " untarred"
    # 7z is handled differently
    elif file_path.lower().endswith('.7z'):
        # Call 7z to unpack, yes to all queries
        try:
            subprocess.Popen(
                ['7z', 'e', file_path, '-o' + destination, '-y'],
                stdout=open(os.devnull, 'w'))
            os.remove(file_path)
            logging.info(file_handle + " un7zipped.")
        except:
            logging.error("{} Something went wrong!\n\n{}\n".format(
                          file_handle, traceback.format_exc()))
        return True
    else:
        # If we reach here, the file was not zip/tar/rar/7z
        return False

    # If we reach here, it should be zip/etc.. Try to unpack, remove the file.
    try:
        file_instance.extractall(path=destination)
        os.remove(file_path)
        logging.info(file_handle + msg_success)
    except:
        logging.error("{} Something went wrong!\n\n{}\n".format(
            file_handle, traceback.format_exc()))
    return True


def main(source, destination, exhaustive):
    '''
    Main function which checks filetype of input, and unpacks accordingly.
    '''
    # First, determine whether input is a gradebook zip or unpacked folder
    logging.warning("Renaming and unpacking '{}'".format(source))
    if zipfile.is_zipfile(source):
        if not destination:
            logging.warning("Destination not given, using source name.")
            destination = source[:-4]
            try_createfolder(source)
        zf = zipfile.ZipFile(source)
        zf.extractall(path=destination)
        folder_name = destination
        # TODO remove original zipfile? Not really necessary/useful!
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

        # Check whether the current txtfile corresponds to handins!
        with open(os.path.join(folder_name, txtfile_name), 'r') as txt:
            # BB text files have name on the first line
            firstline = txt.readline().split()
            name = ''.join(firstline[1:-1])
            student_nr = firstline[-1]

            # We create handin folders if necessary
            newfolder_name = '{}_{}'.format(name, student_nr)
            # Try to remove special chars (if unidecode is present)
            try:
                from unidecode import unidecode
                newfolder_name = unidecode(unicode(newfolder_name))
            except:
                pass
            newfolder_fullpath = os.path.join(folder_name, newfolder_name)

            # Find all matching files
            file_names = [f for f in all_files
                          if (f.startswith(txtfile_prefix)
                              and not f == txtfile_name)]
            if file_names:
                logging.info("Found content for '{}':".format(txtfile_name))
                try_createfolder(newfolder_fullpath)
                # Unpack all files to the newly created folder
                unpack_or_move_all(file_names,
                                   original_path=folder_name,
                                   txtfile_prefix=txtfile_prefix,
                                   destination=newfolder_fullpath,
                                   exhaustive=exhaustive,
                                   file_level=0)
                # Lastly, move the txtfile (may contain notes!)
                os.rename(txtfile_fullpath,
                          os.path.join(newfolder_fullpath,
                                       '_bb_description.txt'))
            else:
                logging.info("No content for '{}'".format(txtfile_name))
    logging.warning("Done.")


def unpack_or_move_all(list_of_file_names, original_path, txtfile_prefix,
                       destination, exhaustive, file_level):
    '''
    Unpack or move all files at original_path/filename to destination folder.
    exhaustive is a boolean indicating that unpacked items must also be
    traversed and unpacked if possible.
    '''
    for file_name in list_of_file_names:
        file_fullpath = os.path.join(original_path, file_name)

        # If file is macosx folder, remove it
        if file_name == "__MACOSX":
            os.removedirs(file_fullpath)

        file_handle = "  {spaces}'{slash}{name}{dots}{suffix}'".format(
            spaces=('  ' * file_level),
            slash=('./' * file_level),
            name=file_name[:40],
            dots=('...' if len(file_name) > 40 else ''),
            suffix=(file_name[-4:] if len(file_name) > 40 else '')).ljust(50)
        # Zips/rars/tars/7zs can be handled similarly
        if not try_unpack(file_fullpath, destination, file_handle):
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
            logging.info(file_handle + " moved.")

        # Check if destination contains a single folder, if so, flatten
        files_in_destination = list(os.listdir(destination))
        if len(files_in_destination) == 1 and \
                os.path.isdir(os.path.join(destination,
                                           files_in_destination[0])):
            # Get the folders name and path to prepare for flattening
            single_folder_name = files_in_destination[0]
            single_folder_fullpath = os.path.join(destination,
                                                  single_folder_name)

            logging.info("     './{}'".format(single_folder_name).ljust(50) +
                         " flattened.")
            unpack_or_move_all(os.listdir(single_folder_fullpath),
                               original_path=single_folder_fullpath,
                               txtfile_prefix=txtfile_prefix,
                               destination=destination,
                               exhaustive=exhaustive,
                               file_level=file_level + 2)
            os.rmdir(single_folder_fullpath)

        # If exhaustive, check the destination folder for zips/tars/rars/7zs
        if exhaustive:
            files_to_unpack = \
                [f for f in files_in_destination if
                 (f.lower().endswith(('.zip', '.tar.gz', '.7z', '.rar')
                                     if rarfile_present else
                                     ('.zip', '.tar.gz', '.7z')))]
            if files_to_unpack:
                unpack_or_move_all(files_to_unpack, original_path=destination,
                                   txtfile_prefix=txtfile_prefix,
                                   destination=destination, exhaustive=True,
                                   file_level=file_level + 1)

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
    arg_parser.add_argument('-r', '--exhaustive_unpack', action='store_const',
                            const=False, default=True,
                            help="Turn off exhaustive unpacking" +
                            "(why would you ever do this?)")
    args = arg_parser.parse_args()

    logginglevel = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=logginglevel,
                        format='%(message)s')

    main(source=args.source, destination=args.destination,
         exhaustive=args.exhaustive_unpack)
