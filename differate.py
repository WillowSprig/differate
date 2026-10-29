"""
This script provides functionality to convert Jupyter Notebook files (.ipynb) to Python scripts (.py) and to compare the similarity between files based on their content.
Usage:
        python differate.py [action] [options]
Actions:
        convert     Convert Jupyter Notebook files (.ipynb, code cells only) to Python scripts (.py).
        diff        Compare the similarity between files (many to many), generate a similarity matrix and output diffs to files.
Options:
        -d, --dir DIRECTORY    Directory (one or more) to scan for files to compare. Default is current directory.
        -c, --cell CELLNUM     Number of notebook cell from which to begin similarity check. Default is 0 (compare the whole file).
        -z, --numexc NUMEXC    Number of exercises in class - separate comparison for each. Default is 1.
        -s, --save DIRECTORY   Directory to save results. Default is current directory.
        -f, --filetype FILETYPE    File type to compare. Default is .py.
Examples:
        Convert all .ipynb files in the current directory to .py files:
                python differate.py convert
        Compare the similarity between .py files in the specified directory, starting from code cell #5:
                python differate.py diff -d /path/to/directory -c 5
        Convert and then compare the similarity between .py files in multiple directories:
                python differate.py convert diff -d /path/to/dir1 -d /path/to/dir2 -z 2 -s /path/to/save/results
        Compare files named "Name Surname_1.py" in one directory:
                python differate.py diff -d /path/to/submissions
        Unique parent-folder names are used when available; otherwise files are
        identified by the "Name Surname" prefix of "Name Surname_number".
"""

import json
from glob import glob
from os import path, mkdir
from warnings import warn


def ipynb2py(directory='.'):
        if not isinstance(directory, list):
                files = glob(path.join(directory,'**','*.ipynb'), recursive=True)
        else:
                files = []
                for d in directory:
                        files = files + glob(path.join(d,'**','*.ipynb'), recursive=True)
        for file in files:
                print(f'Converting file {file}...')
                with open(file, 'r', encoding='utf8') as f: #input.ipynb
                        j = json.load(f)
                newfile = path.join(path.dirname(file), path.basename(file).replace('.ipynb', '.py'))
                with open(newfile, 'w', encoding='utf8') as of: #output.py
                        if j["nbformat"] >=4:
                                for i,cell in enumerate(j["cells"]):
                                        if cell["cell_type"] == "code":
                                                of.write("#cell "+str(i)+"\n")
                                                for line in cell["source"]:
                                                        of.write(line)
                                                of.write('\n\n')
                        else:
                                for i,cell in enumerate(j["worksheets"][0]["cells"]):
                                        if cell["cell_type"] == "code":
                                                of.write("#cell "+str(i)+"\n")
                                                for line in cell["input"]:
                                                        of.write(line)
                                                of.write('\n\n')


def get_folder_name(file_path):
        return path.basename(path.dirname(file_path)).split('_')[0]

def get_filename_identity(file_path):
        import re
        match = re.match(r'^(.+?)_(\d+)(.*)$', path.splitext(path.basename(file_path))[0])
        if not match:
                raise ValueError(
                        f'Expected filename to begin with "Name Surname_number": {path.basename(file_path)}')
        return match.group(1)


def get_snippet_to_compare(file_path, cellnum=0):
        with open(file_path, 'r', encoding='utf8') as f:
                if cellnum == 0:
                        return f.readlines()
                        # must return a list to diff line by line (otherwise diffs char by char, when using read())
                else:
                        lines = f.readlines()
                        cells = [line for line in lines if line.startswith("#cell")]
                        if len(cells) == 0:
                                warn(f'Cells not numbered in file {file_path}, returning whole file')
                                return lines
                        elif int(cells[-1].strip()[-1]) < cellnum:
                                warn(f'Cell number {cellnum} not found in file {file_path}, highest number: {cells[-1][-1]}; returning whole file')
                                return lines
                        else:
                                for n, line in enumerate(lines):
                                        if line.startswith("#cell "+str(cellnum)):
                                                return lines[n:]
                                # if not found, iterate to find nearest higher cell number
                                while True:
                                        cellnum+=1
                                        for n, line in enumerate(lines):
                                                if line.startswith("#cell "+str(cellnum)):
                                                        return lines[n:]

def diffdir(directory='.', filetype='.py', numexc=2, cellnum=0, savedir='.'):
        import difflib
        from itertools import combinations
        import pandas as pd
        import numpy as np
        import re
        from matplotlib import pyplot as plt
        if not isinstance(directory, list):
                files = glob(path.join(directory,'**','*'+filetype), recursive=True)
                lab_match = re.search('[lL]ab(\\d+)', directory)
                nlab = int(lab_match.group(1)) if lab_match else None
        else:
                files = []
                nlab = None
                for d in directory:
                        files = files + glob(path.join(d,'**','*'+filetype), recursive=True)
                        lab_match = re.search('[lL]ab(\\d+)', d)
                        if lab_match:
                                tmp_nlab = int(lab_match.group(1))
                                nlab = tmp_nlab if nlab is None else nlab
                                assert nlab == tmp_nlab, 'Compared files must be from the same class'
        filename_mode_done = False
        for z in range(numexc):
                # file = ('Lab'+str(nlab) if nlab is not None else 'Files')+'_zad'+str(z+1)
                file = savedir.replace('/','_').replace('\\','_')+'_zad'+str(z+1)
                folder_files = []
                if nlab is not None:
                        folder_files = [f for f in files if re.search(
                                '[lL]ab'+str(nlab)+'_[zZ]ad'+str(z+1)+'(?!\\d)',
                                path.basename(f))]
                        if not folder_files:
                                print(f"WARNING: no files found for task {z+1}\nSearching for non-numbered Lab files...")
                                folder_files = [f for f in files if re.search(
                                        '[lL]ab'+str(nlab), path.basename(f))]
                                print(f"{len(folder_files)} found")

                folder_names = [get_folder_name(f) for f in folder_files]
                if folder_files and len(set(folder_names)) == len(folder_names):
                        z_files = folder_files
                        names = folder_names
                else:
                        if filename_mode_done:
                                continue
                        filename_files = []
                        filename_names = []
                        for f in files:
                                try:
                                        name = get_filename_identity(f)
                                except ValueError:
                                        continue
                                filename_files.append(f)
                                filename_names.append(name)
                        z_files = filename_files
                        names = filename_names
                        if not z_files and folder_files:
                                raise ValueError(
                                        'Folder names are not unique and no files match "Name Surname_number"')
                        filename_mode_done = bool(z_files)
                if len(set(names)) != len(names):
                        raise ValueError(f'Submission names must be unique for task {z+1}')
                df = pd.DataFrame(np.zeros((len(names),len(names))), columns=names, index=names)
                for (f1, name1), (f2, name2) in combinations(zip(z_files, names), 2):
                        name = (name1, name2)
                        outf = path.join(savedir, '_'.join([file, name[0], name[1]])+'.diff')
                        
                        f1_lines = get_snippet_to_compare(f1, cellnum)
                        f2_lines = get_snippet_to_compare(f2, cellnum)
                        
                        r1 = difflib.SequenceMatcher(None, f1_lines, f2_lines).ratio()
                        r2 = difflib.SequenceMatcher(None, f2_lines, f1_lines).ratio()
                        
                        df.loc[name[0], name[1]] = r1
                        df.loc[name[1], name[0]] = r2

                        diff = difflib.unified_diff(f1_lines, f2_lines)
                        
                        with open(outf, 'w', encoding='utf8') as f:
                                f.writelines(diff)
                hm = draw_heatmap(df)
                plt.savefig(file+'_similarity.png')
                df.to_csv(file+'_similarity.csv')


def draw_heatmap(df):
        from seaborn import heatmap
        rows, columns = df.shape
        figure_width = max(8, columns * 0.75)
        figure_height = max(6, rows * 0.65)
        cell_size = min(
                figure_width / max(columns, 1),
                figure_height / max(rows, 1))
        font_size = max(12, cell_size * 15)

        hm = heatmap(
                df,
                annot=True,
                annot_kws={'size': font_size},
                cmap='magma_r',
                vmin=0,
                vmax=1,
                xticklabels=True,
                yticklabels=True)
        hm.set_xticks([index + 0.5 for index in range(columns)])
        hm.set_yticks([index + 0.5 for index in range(rows)])
        hm.set_xticklabels(df.columns, rotation=90, fontsize=font_size)
        hm.set_yticklabels(df.index, fontsize=font_size)
        
        hm.figure.set_size_inches(figure_width, figure_height)
        hm.figure.tight_layout()
        return hm


def main():
        from argparse import ArgumentParser
        parser = ArgumentParser()
        parser.add_argument('action', choices=['','convert', 'diff'], help='Action to perform', default='', nargs='*')
        parser.add_argument('-d', '--dir', default='.', help='Directory to search for files', nargs='*')
        parser.add_argument('-c', '--cell', default=0, type=int, nargs='?',
                        help='Number of cell from which to begin similarity check')
        parser.add_argument('-z', '--numexc', default=1, type=int, nargs='?', help='Number of excersises')
        parser.add_argument('-s', '--save', default='.', help='Directory to save results', nargs='?')
        parser.add_argument('-f', '--filetype', default='.py', help='File type to compare', nargs='?')
        args = parser.parse_args()

        if not path.isdir(args.save):
                mkdir(args.save)

        if not args.action:
                ipynb2py(directory=args.dir)
                diffdir(directory=args.dir, numexc=args.numexc, cellnum=args.cell, savedir=args.save)
        if 'convert' in args.action:
                ipynb2py(directory=args.dir)
        if 'diff' in args.action:
                diffdir(directory=args.dir, filetype=args.filetype, numexc=args.numexc, cellnum=args.cell,
                        savedir=args.save)

if __name__ == '__main__':
        main()