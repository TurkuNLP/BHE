#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import codecs
import os
import sys

def merge_entities(entity_path, out_path):
    """
    Merges Suwisa's separate .a1 files.
    """
    if not os.path.exists(out_path):
        os.makedirs(out_path)
        
    a1_files = [f for f in os.listdir(os.path.join(entity_path, 'bacteria')) if f.endswith('.a1')]
    for f in a1_files:
        entities = []
        for path in ['bacteria', 'habitat', 'geographical']:
            entities += [e.split('\t') for e in codecs.open(os.path.join(entity_path, path, f), 'r', 'utf-8')]
        min_id = min([int(e[0][1:]) for e in entities])
        for i, e in enumerate(entities):
            e[0] = 'T%s' % (min_id+i)
        with codecs.open(os.path.join(out_path, f), 'w', 'utf-8') as out_f:
            for e in entities:
                out_f.write('\t'.join(e))



def argument_parser():
    parser = argparse.ArgumentParser(description="merge predicted entities for all types (habitat, geographical, bacteria)")
    parser.add_argument("-i", "--in_folder", type=str, help="input folder")
    parser.add_argument("-o", "--out_folder", type=str, help="output folder")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = argument_parser()
    merge_entities(args.in_folder, args.out_folder)
                                                                                                                                                        
