# Dynamic-Dictionary
Repository for COSI 175A Assignment 1

This assignment is to write a dynamic dictionary compressor (and a corresponding decompressor), 
that has two encoding options, FC (first character) and CM (current match), 
and three deletion options, FREEZE (simply stop adding entries when the dictionary fills);
RESTART (reset the dictionary whenever it is full and compression drops off according to some criterion you choose),
and LRU (least recent used).

To compress or decompress, please cd into the directory where compressor.py is in and execute:
python compressor.py [update=] [delete=] [file_name=] [dict_size=]
options: update=fc/cm, delete=freeze/restart/lru
         file_name=file under test_files with the end .txt
         dict_size=number > 256
e.g. python compressor.py update=fc delete=lru file_name=bib.txt dict_size=64000

This would compress the target file from test_files and output .zip file to the directory named compressed_files,
and then decompress the compressed file and output file_name_de.txt file to the directory named decompressed_files.
If no file_name specified, then all files under test_files will be compressed and decompressed.

My compressor just use the basic dynamic dictionary algorithm from slides.
Except that:
1. When reading from original file and writing to decompressed file using encoding='latin-1' in python

2. I implement LRU by using double-linked list which can make time complexity of access and replace both O(1)

3. I use dict data structure to store the dictionary to improve compressing and decompressing speed
