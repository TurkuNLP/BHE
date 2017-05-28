"""
Reads a1 and a2 files and converts them to lists of entity-ID tuples.
"""
import os
import codecs
from collections import defaultdict, Counter
import settings

from nltk.stem.snowball import PorterStemmer
stemmer = PorterStemmer()
from nltk import word_tokenize

def read(path):
    a1_files = [f for f in os.listdir(path) if f.endswith('.a1')]
    a2_files = [f for f in os.listdir(path) if f.endswith('.a2')]
    
    entities = defaultdict(list)
    
    for f in a1_files:
        content = codecs.open(os.path.join(path, f), 'r', 'utf-8')
        doc_entity_tokens = []
        doc_entities = []
        for line in content:
            data = line.strip().split('\t')
            if not data[1].startswith(settings.ENTITY_TYPE):
                continue
            entity_id = data[0]
            entity_span = data[2]
            #if len(entity_span) >= 5 and not entity_span.isupper():
            #    doc_entities.append(entity_span)
            #else:
            #    print 'Too small entity: %s' % entity_span
            #    #entity_expansions = [e for e in doc_entities if entity_span.lower() in ''.join([l[0] for l in e.split()]).lower()]
            #    if not len(doc_entities) == 0:
            #        print 'Entity: %s, expansion: %s' % (entity_span, doc_entities[-1])
            #        entity_span = doc_entities[-1]
                
            entity_tokens = entity_span.split()
            #if not '.' in entity_tokens[0]:
            doc_entity_tokens += [e for e in entity_tokens if not '.' in e]
            span_counter = Counter(doc_entity_tokens)
            if settings.ENTITY_TYPE == 'Habitat':
                entity_span = ' '.join([stemmer.stem(_expand(t, span_counter)) for t in entity_tokens])
            else:
                entity_span = ' '.join([_expand(t, span_counter) for t in entity_tokens])
            
            entities[f.split('.')[0]+'___'+entity_id].append(entity_span)
        
        #print entities.values()
        #import pdb; pdb.set_trace()
        #entities = defaultdict(list)
            
    for f in a2_files:
        content = codecs.open(os.path.join(path, f), 'r', 'utf-8')
        for line in content:
            data = line.strip().split('\t')
            if settings.ENTITY_TYPE == 'Habitat' and not data[1].startswith('OntoBiotope'):
                continue
            elif settings.ENTITY_TYPE == 'Bacteria' and not data[1].startswith('NCBI_Taxonomy'):
                    continue
            data = data[1].split()
            entity_id = data[1].split(':')[1]
            ontology_id = data[2].partition(':')[-1]
            entities[f.split('.')[0]+'___'+entity_id].append(ontology_id)
    return entities

def _expand(token, token_counter):
    if '.' in token:
        #import pdb; pdb.set_trace()
        for t, count in sorted(token_counter.items(), key=lambda x: x[1], reverse=True):
            if t.lower().startswith(token[0].lower()):
                #print "%s expanded to %s" % (token, t)
                return '%s %s' % (token, t)
    return token

if __name__ == '__main__':
    read('./data/BioNLP-ST-2016_BB-cat_train/')
    