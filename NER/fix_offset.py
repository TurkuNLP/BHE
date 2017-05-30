#!/usr/bin/python
# -*- coding: utf-8 -*-


import argparse
import codecs


def fix_gtag_offset(filename):
    new_doc = []
    with open(filename + '.idx', 'r') as f:
        mapping = {int(line.split('\t')[1].replace('\n', '')): int(line.split('\t')[0]) for line in f}
    len_text = list(mapping.keys())
    len_text.sort()
    for item in range(len_text[-1]):
        if item not in mapping.keys():
            mapping.setdefault(item, mapping[item-1])
    with open(filename + '.gtag', 'r') as f:
        all_lines = f.readlines()
        for j, line in enumerate(all_lines):
            if line != '\n':
                lines = line.split('\t', 2)
                off_B = mapping[int(lines[0])]
                off_E = mapping[int(lines[1])]
                new_doc.append('\t'.join([str(off_B), str(off_E), lines[2]]))
            else:
                new_doc.append(line)
    with open(filename + '.off', 'w') as f:
        f.write(''.join(new_doc))


def argument_parser():
    parser = argparse.ArgumentParser(description="change the offsets in gtag files to match the original text file offsets")
    parser.add_argument("-f", "--filename", type=str, help="main input folder")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = argument_parser()
    print('fixing offsets...')
    fix_gtag_offset(args.filename)
