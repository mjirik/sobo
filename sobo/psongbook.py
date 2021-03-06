#! /usr/bin/python
# -*- coding: utf-8 -*-

# import funkcí z jiného adresáře
import sys
import subprocess
import shlex
import os
import fnmatch
import traceback
#sys.path.append("../src/")

import logging
logger = logging.getLogger(__name__)

import pdb
import pandas as pd
import re
from . import sort
#pdb.set_trace()
#import scipy.io
#mat = scipy.io.loadmat('step0.mat')
from . import inout
from pathlib import Path

#print mat

def genfilelist(dirpath, wildcards='*.txt', structured = True, decode_filenames=False):
    """ Function generates list of files from specific dir

    filesindir(dirpath, wildcard="*.*", startpath=None)

    dirpath: required directory
    wilcard: mask for files
    startpath: start for relative path


    """
    if not Path(dirpath).exists():

        logger.error(f"Path '{dirpath}' does not exist.")
        exit()

    if Path(dirpath).is_file():
        logger.error(f"Path '{dirpath}' should be directory.")
        exit()

    # # dirpath = Path(dirpath)
    #


    filelist = {}
    rootdir = dirpath
    for root, subFolders, files in os.walk(rootdir):
        #pdb.set_trace()
        if structured:
            filesutf8 = []
            # encoding to utf-8

            for fileu in fnmatch.filter(files, wildcards):
                # pdb.set_trace()

                if decode_filenames:
                    fileu = fileu.decode(sys.getfilesystemencoding()).encode('utf8')

                filesutf8.append(fileu)

            #pth = os.path.join(root,fileu)
            dirname = os.path.relpath(root,rootdir)
            filesutf8 = list(sort.sort_filelist_by_author(
                    os.path.join(rootdir, dirname), 
                    filesutf8
            ))
            #fl={'dirname': dirname, 'files':filesutf8}
            #filelist.append(fl)
            filelist[dirname]=filesutf8
        else:
            for file in fnmatch.filter(files, wildcards):
                filelist.append(os.path.join(root,file))
    #        
    # print filelist
    # import ipdb; ipdb.set_trace() #  noqa BREAKPOINT
    

    #filelist = []
    #print dirpath

    #for infile in glob.glob( os.path.join(dirpath, wildcard) ):
    #    if startpath != None:
    #        infile = os.path.relpath(infile, startpath)
    #    filelist.append(infile)
        #print "current file is: " + infile

    # sngbky = {'dirpath'.encode('utf8'): dirpath.encode('utf-8'), 'filelist'.encode('utf-8'):filelist }
    sngbky = {'dirpath': dirpath, 'filelist':filelist }
    return sngbky



def _parse_file(fullfilepath):
    lines = inout.load_file(fullfilepath).splitlines()
    from . import songparser
    song = songparser.SongParser(lines, filename=fullfilepath)
    # import ipdb; ipdb.set_trace() #  noqa BREAKPOINT
    return song


def _gentexfile_for_one(fullfilepath, compact_version=False):
    """
    generate latex string for one file
    :param filepath:
    :param sngbk:
    :param part:
    :return:
    """

    docpsongbook = ""

    song = _parse_file(fullfilepath)

    # title = song.name.decode("utf8") + " - " + song.artist.decode("utf8")
    #title = song.name + " : " + song.artist_preprocessed
    title = song.name + " : " + song.artist
    shorttitle = song.name
    # docpsongbook += "\n{\\nopagebreak[4]"
    if compact_version:
        docpsongbook += "\n\\Needspace*{5\\baselineskip}\n"
    else:
        docpsongbook += "\n\\Needspace*{15\\baselineskip}\n"
    #docpsongbook += "\n\\begin{samepage}\n"
    docpsongbook += "\\subsection{" + title + "}\n"
    # docpsongbook += "\\subsection[" + shorttitle + "]{" + title + "}\n"
    #docpsongbook += '\n\\nopagebreak[3]\n'
    docpsongbook += '\\begin{alltt}\n'
    #pdb.set_trace()
    if compact_version:
        lines = song.lines_no_chords
        # lines = songparser.song_without_chords(lines)
    else:
        lines = song.lines
    from . import songparser
    idin, idout = songparser.get_chord_line_indexes(lines)

    for i in range(len(lines)):
        lineraw = lines[i]

        line = lineraw
        # import ipdb; ipdb.set_trace() #  noqa BREAKPOINT
        if i in idin:
            docpsongbook += "\\textbf{"
        docpsongbook += line

        if i in idin:
            docpsongbook += "}"
        docpsongbook += '\n'
    docpsongbook += '\\end{alltt}\n'

    #docpsongbook += "\\end{samepage}\n"
    # nopagebreak closing
    # docpsongbook += "}"
    if not compact_version:
        docpsongbook += '\\newpage\n'
        # docpsongbook += '\\pagebreak[3]\n'
        pass
    return docpsongbook

def gentexfile(sngbk, filename = 'psongbook.tex', compact_version=False):
    head = u""
    if compact_version:
        head += u"\\documentclass[7pt]{article}\n"
    else:
        head += u"\\documentclass{article}\n"

    head += u'\
\\usepackage{a4wide}\n\
\\usepackage[czech]{babel}\n\
\\usepackage[utf8]{inputenc}\n\
\\usepackage[T1]{fontenc}\n\
\\usepackage{libertine}\n\
\\usepackage{alltt}\n\
\\usepackage{needspace}\n\
\\begin{document}\n\
\\tableofcontents\n\
\\newpage\n\
'

    docpsongbook = head
    #pdb.set_trace()
    sngbkfilelist=sngbk['filelist']
    print("Compact version? ", compact_version)

    for part in sngbkfilelist.keys():
        docpsongbook += "\\section{" + part + "}\n"
        try:

            prt = sngbkfilelist[part]
            for filepath in prt:
                fullfilepath = os.path.join(sngbk['dirpath'],
                                            part)
                fullfilepath = os.path.join(fullfilepath,filepath)
                print("processing file: ", fullfilepath)
                onefile_tex_unicode = _gentexfile_for_one(fullfilepath, compact_version=compact_version)

                try:
                    docpsongbook += onefile_tex_unicode
                except:
                    traceback.print_exc()
                    print("problem with file: ", fullfilepath)


        except:
            traceback.print_exc()
            # import ipdb; ipdb.set_trace() #  noqa BREAKPOINT

    docpsongbook += '\\end{document}\n'

    logger.debug( docpsongbook)

    f = open(filename, 'w', encoding="utf8")
    #text = 'ahoj'

    docpsongbook = replace_latex_bad_character(docpsongbook)

    # import ipdb; ipdb.set_trace() #  noqa BREAKPOINT

    docpsongbook.replace("\ufeff", "")
    f.write(docpsongbook)
    f.close()


def replace_latex_bad_character(text):
    """
    :param text: string or list of strings
    :return:
    """

    if type(text) == list:
        new_text = []
        for line in text:
            new_text.append(_replace_latex_bad_character_one_string(line))
    else:
        new_text = _replace_latex_bad_character_one_string(text)

    return new_text


def _replace_latex_bad_character_one_string(docpsongbook):
    docpsongbook = docpsongbook.replace(u'\u0008', '')
    docpsongbook = docpsongbook.replace("°", '')
    docpsongbook = docpsongbook.replace("_", '\\_')
    docpsongbook = docpsongbook.replace("´", "'")
    docpsongbook = docpsongbook.replace('\xef\xbb\xbf','')
    # hard space into normal space
    docpsongbook = docpsongbook.replace(' ',' ')
    docpsongbook = docpsongbook.replace('$','\$')
    docpsongbook = re.sub(r"(.[^\\])&", r"\1\\&", docpsongbook)
    # docpsongbook = re.sub(r"(.[^\\])\$", r"\1\$", docpsongbook)
    return docpsongbook


def genpdffile(fullfilename):
    
    proc=subprocess.Popen(shlex.split('pdflatex '+fullfilename))
    proc.communicate()
    filename, fileextension = os.path.splitext(fullfilename)
    os.unlink(filename + '.log')


def sngbk_from_file(filename = 'sngbk.yaml'):
    import yaml
    stream = open(filename, 'r')
    sngbk = yaml.load(stream)
    #print sngbk
    return sngbk



def sngbk_to_file(sngbk, filename = 'sngbk.yaml'):
    #import json
    #with open(filename, mode='w') as f:
    #    json.dump(annotation,f)

    # write to yaml

    from ruamel.yaml import YAML
    yaml = YAML()
    # import ipdb; ipdb.set_trace()
    with open(filename, 'w', encoding="utf-8") as f:
        yaml.dump(sngbk, f)
    # f.close


def generate_example(path=""):
    import os
    import os.path as op

    if not os.path.exists(path):
        os.makedirs(path)



    text = 'Saxana - z filmu Saxana\n\
\n\
   A D A   F#mi                   E\n\
1: Saxano, v knihách vázaných v kůži\n\
   A  D A  F#mi     E      A\n\
   Zapsáno kouzel jevíc než dost\n\
   A D A   F#mi                  E\n\
   Saxano, komu dech se z nich úží\n\
   A D A   F#mi     E      A\n\
   Saxano, měl by si říct už dost!\n\
\n\
   A7              C7\n\
   Cizími slovy ti jedna z nich poví\n\
      D7\n\
   Že muži se loví\n\
       F7      G7       E7\n\
   Buď pan admirál nebo král\n\
   A7               C7\n\
   Vem oko soví, pak dvě slzy vdovy\n\
      D7\n\
   To svař a dej psovi\n\
       F7       G7      E7\n\
   Co vyl a byl sám opodál\n\
 \n\
2: Saxano, v knihácha vázaných v kůži \n\
   Zapsáno kouzel je na tisíc \n\
   Saxano, v jedné jediné růži \n\
   Saxano, kouzel je mnohem víc\n\
\n\
   Seď chvíli tiše a pak hledej spíše\n\
   Kde ve všem se píše \n\
   Že tát bude sníh, loňský sníh\n\
   Najdeš tam psáno, jak změnit noc v ráno\n\
   Jak zakrýt ne ano \n\
   A pláč v nocích zlých, změnit v smích \n\
\n\
1: Saxano ... (Jen první část)\n\
'
    sax_fn = op.join(path,"saxana.txt")
    sb_fn = op.join(path,"sngbk.yaml")

    f = open(sax_fn, 'w', encoding="utf-8")
    #text = 'ahoj'
    f.write(text)
    f.close()

    # sngbk = {u'dirpath'.encode('utf8'): path, 'filelist': {u'.'.encode('utf8'):[sax_fn.encode('utf8')]}}
    sngbk = {'dirpath': path, 'filelist': {'.':[sax_fn]}}
    sngbk_to_file(sngbk, filename=sb_fn)


def get_parser(parser=None):
    import argparse
    if parser is None:
        parser = argparse.ArgumentParser(description='Process some chord file...')
    parser.add_argument('sngbk', type=str, default='sngbk.yaml', \
                        nargs='?', \
                        help='file with list of all chord files')
    # parser.add_argument('files', metavar='N', type=str, nargs='+',
    #        help='input text files with song chords')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-c', '--compact-version', action='store_true')
    parser.add_argument('-id', '--inputdir', type=str, default=None, \
                        help='input directory')
    parser.add_argument('-o', '--output', type=str, default='psongbook.tex', \
                        help="output tex file")
    parser.add_argument('-e', '--example', action='store_true', \
                        help='generate example chord file')

    return parser

def main():
    import sys
    import Tkinter

    logger.setLevel(logging.ERROR)
    ch = logging.StreamHandler()
    logger.addHandler(ch)

    logger.debug('input params')

    parser = get_parser()
    args = parser.parse_args()

    #print args
    main_args(args)

def main_args(args):

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.example:
        generate_example()
        sys.exit()

    if args.inputdir is not None:
        sngbky = genfilelist(args.inputdir)
        sngbk_to_file(sngbky, args.sngbk)

        # args.

    sngbk = sngbk_from_file(args.sngbk)
    #print sngbk
    gentexfile(sngbk, args.output, compact_version=args.compact_version)


if __name__ == "__main__":
    main()
