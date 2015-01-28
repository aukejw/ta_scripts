ta_scripts
==========

Blackboard is a wonderful system, but it does not quite work the way I want it to... Relevant: https://xkcd.com/1319/

rename_bb_handins.py is a script for automatically unpacking blackboard gradebooks.
Assumes you have unzip, 7z (p7zip-full) and unrar installed.
Also tries to use unidecode to remove special chars from names.
List of features:

    - Creates folders for each handin based on student name + nr
    - Extracts tars/zips/7zs/rars
    - Flattens single-folder handins (from tars, for example)
    - Moves files to handin-folders
    - Uses python logging for user feedback
    
Example call:

    python rename_bb_handins.py gradebook.zip -d Assignment2 -v 
