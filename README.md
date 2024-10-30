## differate

A script to convert Jupyter Notebook files (.ipynb) to Python scripts (.py) and to compare the similarity between files based on their content.

### Usage:
    python differate.py [action] [options]
### Actions:
    convert     Convert Jupyter Notebook files (.ipynb, code cells only) to Python scripts (.py).
    diff        Compare the similarity between files (many to many), generate a similarity matrix and output diffs to files.
### Options:
    -d, --dir DIRECTORY    Directory (one or more) to scan for files to compare. Default is current directory.
    -c, --cell CELLNUM     Number of notebook cell from which to begin similarity check. Default is 0 (compare the whole file).
    -z, --numexc NUMEXC    Number of exercises in class - separate comparison for each. Default is 1.
    -s, --save DIRECTORY   Directory to save results. Default is current directory.
    -f, --filetype FILETYPE    File type to compare. Default is .py.
### Examples:
Convert all .ipynb files in the current directory to .py files:

    python differate.py convert
Compare the similarity between .py files in the specified directory, starting from code cell #5:

    python differate.py diff -d /path/to/directory -c 5
Convert and then compare the similarity between .py files in multiple directories:

    python differate.py convert diff -d /path/to/dir1 -d /path/to/dir2 -z 2 -s /path/to/save/results
