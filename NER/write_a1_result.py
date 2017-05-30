#!/usr/bin/python3
# -*- coding: utf-8 -*-

import glob
import argparse
import codecs
# import normalize_bacteria as norm_org


def rewrite_entity(new_ent, file_ext):
    file_ent_dict = {'.bac': 'Bacteria ', '.hab': 'Habitat ', '.geo': 'Geographical '}
    offsets = []
    ent_line = new_ent.split("\n")
    offset = [[line.split('\t')[0], line.split('\t')[1]] for line in ent_line if line != '']
    tokens = [line.split('\t')[2] for line in ent_line if line != '']
    off_str = []
    txt_str = ''
    for i, item in enumerate(offset):
        if i == 0:
            off_str.append([item[0], item[1]])
            txt_str += tokens[i]
        else:
            dist = int(item[0]) - int(off_str[-1][1])
            if dist == 1:
                txt_str += ' ' + tokens[i]
                off_str[-1][1] = item[1]
            elif dist == 0:
                txt_str += tokens[i]
                off_str[-1][1] = item[1]
            else:
                off_str.append([item[0], item[1]])
                txt_str += ' ' + tokens[i]
    off_text = file_ent_dict[file_ext]
    for item in off_str:
        off_text += " ".join(item) + ";"
    return off_text.rsplit(";", 1)[0], txt_str


def load_prediction(filename, file_ext):
    ent_list = set([])
    entity = file_ext[-3].upper() + file_ext[-2:]
    new_ent = ''
    result = ''
    with open(filename, 'r') as f:
        for line in f:
            if line != '\n':
                lines = line.split('\t')
                if 'B-{}\n'.format(entity) in lines:
                    if new_ent != '':
                        off_text, txt_str = rewrite_entity(new_ent, file_ext)
                        result = '\t'.join([off_text, txt_str]) + '\n'
                        ent_list.add(result)
                    new_ent = line
                elif 'I-{}\n'.format(entity) in lines:
                    new_ent += line
        if new_ent != '':
            off_text, txt_str = rewrite_entity(new_ent, file_ext)
            result = '\t'.join([off_text, txt_str]) + '\n'
            ent_list.add(result)
    ent_list = list(ent_list)
    return ent_list


def write_a1_ner(filename, v, file_ext, tag_file):
    file_ent_dict = {'.bac': 'Bacteria ', '.hab': 'Habitat ', '.geo': 'Geographical '}
    dir_ent_dict = {'.bac': '/bacteria', '.hab': '/habitat', '.geo': '/geographical'}
    sub_folder = dir_ent_dict[file_ext].lower()
    a1_file = filename.replace('.txt' + tag_file + file_ext, '.a1')
    utf8_file = a1_file.replace('temp', 'input').replace('a1', 'txt')
    with codecs.open(utf8_file, 'r', 'utf-8') as x:
        utf8_doc = x.read()
    j = 0
    text_1 = []
    i = 1
    if v !=['']:
        sort_v = sorted(v, key=lambda x:int(x.split()[1]))
        for item in sort_v:
            offsets = item.split("\n")[0].split("\t")[0].split(';')
            all_offset = [item.split()[-2:] for item in offsets]
            new_text = ' '.join([utf8_doc[int(offB):int(offE)] for offB, offE in all_offset])
            norm_ent = 'T{}\t{}\n'.format(str(i+int(j)), item)
            old_text = item.strip('\n').split('\t')[-1]
            if norm_ent not in text_1:
                new_norm = norm_ent.replace('\n', '\t' + new_text + '\n')
                if "\n" in utf8_doc[int(all_offset[0][0]):int(all_offset[-1][-1])]:
                    print(new_norm)
                text_1.append(new_norm)
                i += 1
    print a1_file
    with codecs.open(a1_file.replace('temp', 'temp' + dir_ent_dict[file_ext]), 'w', 'utf-8') as f:
        f.write(''.join(text_1))

            
def argument_parser():
    parser = argparse.ArgumentParser(description="F1 performance evaluation")
    parser.add_argument("-f", "--filename", type=str, help="main input folder")
    parser.add_argument("-e", "--file_ext", type=str, help="file extension for entity")
    parser.add_argument("-t", "--tag_file", default='.txt.off', type=str, help="file extension of tagged file")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = argument_parser()
    ent_list = load_prediction(args.filename, args.file_ext)
    write_a1_ner(args.filename, ent_list, args.file_ext, args.tag_file)
