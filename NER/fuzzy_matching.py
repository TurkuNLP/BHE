"""
Fuzzy matching dictionary features for habitat.
"""
import argparse
import codecs
import os
import sys
import numpy
from sklearn.metrics.pairwise import cosine_similarity

import settings
from ontology import read_ontology
from baseline import build_tfidf

from nltk.stem.snowball import PorterStemmer
stemmer = PorterStemmer()

def get_concepts():
    concepts = list(read_ontology())
    return build_tfidf(concepts)

def add_features(f, token_column, concept_data):
    concept_ids, concept_names, concept_map, concept_vectors, tfidf_vectorizer = concept_data
    in_file = codecs.open(f, 'r', 'utf-8')
    if settings.ENTITY_TYPE == 'Habitat':
        out_file = codecs.open(f+'.fuzzy', 'w', 'utf-8')
    else:
        out_file = codecs.open(f+'.buzzy', 'w', 'utf-8')
    
    
    tokens = [l.strip().split('\t')[token_column] for l in codecs.open(f, 'r', 'utf-8') if not (l.startswith('[SEP]') or l == '\n')]
    if settings.ENTITY_TYPE == 'Habitat':
        tokens = [stemmer.stem(t) for t in tokens]
    token_vectors = tfidf_vectorizer.transform(tokens)
    # Doing the cosine similarity in smaller batches reduces memory footprint
    max_hits = []
    step_size = 1000
    for i in range(0, token_vectors.shape[0], step_size):
        if i + step_size > token_vectors.shape[0]:
            end = token_vectors.shape[0]
        else:
            end = i + step_size
        print end
        hits = numpy.max(cosine_similarity(token_vectors[i:end], concept_vectors), axis=1)
        max_hits += list(hits)
    
    for i, line in enumerate(in_file):
        if line == '\n' or line.startswith('[SEP]'):
            out_file.write(line)
            continue
        
        max_hit = max_hits.pop(0)
        
        if settings.ENTITY_TYPE == 'Habitat':
            new_line = line.strip() + '\tBiotope:%.2f\n' % max_hit
        else:
            new_line = line.strip() + '\tBacteria:%.2f\n' % max_hit
        
        out_file.write(new_line)

        
def argument_parser():
    parser = argparse.ArgumentParser(description="merge predicted entities for all types (habitat, geographical, bacteria)")
    parser.add_argument("-i", "--in_folder", type=str, help="input folder")
    parser.add_argument("-e", "--entity", type=str, help="entity type, either Bacteria or Habitat")
    parser.add_argument("-c", "--column", type=str, help="column of the files")
    parser.add_argument("-f", "--file_extension", type=str, help="file extension")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = argument_parser()
    path = args.in_folder
    entity_type = args.entity
    col = args.column
    file_ext = args.file_extension
    settings.ENTITY_TYPE = entity_type
    
    concept_data = get_concepts()
    for f in os.listdir(path):
        if f.endswith(file_ext):
            add_features(os.path.join(path, f), int(col), concept_data)
