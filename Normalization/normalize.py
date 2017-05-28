"""
TFIDF based baseline normalization.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score
from sklearn.metrics.pairwise import cosine_similarity
from ontology import read_ontology
import numpy
from write import write
from read import read
import settings
import sys

from nltk.stem.snowball import PorterStemmer
stemmer = PorterStemmer()
from nltk import word_tokenize

from baseline import build_tfidf
            
def normalize(in_path, out_path):
    print 'Reading concept data'
    concepts = list(read_ontology())
    
    concept_ids, concept_names, concept_map, concept_vectors, tfidf_vectorizer = build_tfidf(concepts)
    reverse_concept_map = {concept_ids[i]:concept_names[i] for i in range(len(concept_names))}
    print 'Making predictions'
    
    devel_data = read(in_path)
    
    devel_tuples = []
    for entity_id, data in devel_data.items():
        entity_span = data[0]
        for ann in data[1:]:
            devel_tuples.append((entity_id, entity_span, ann))
    devel_entity_ids = [d[0] for d in devel_tuples]
    devel_spans = [d[1] for d in devel_tuples]
    
    # Acronym expansion
    if settings.ENTITY_TYPE == 'Bacteria':
        from collections import defaultdict
        doc_entities = defaultdict(list)
        for i, entity_span in enumerate(devel_spans):
            if len(entity_span) >= 5 and not entity_span.isupper():
                doc_entities[devel_entity_ids[i].split('___')[0]].append(entity_span)
        
        for i, entity_span in enumerate(devel_spans):
            if len(entity_span) < 5 or entity_span.isupper():
                #print 'Too small entity: %s' % entity_span
                entity_vect = tfidf_vectorizer.transform([entity_span])
                prev_entities = doc_entities[devel_entity_ids[i].split('___')[0]]
                if len(prev_entities) > 0:
                    prev_entity_acronyms = [''.join([l[0] for l in e.split()]) for e in prev_entities]
                    doc_vects = tfidf_vectorizer.transform(prev_entity_acronyms)
                    best_hit = numpy.argmax(cosine_similarity(entity_vect, doc_vects), axis=1)[0]
                    new_span = doc_entities[devel_entity_ids[i].split('___')[0]][best_hit]
                    #print 'Entity: %s, expansion: %s' % (entity_span, new_span)
                    devel_spans[i] = new_span
    
    devel_vectors = tfidf_vectorizer.transform(devel_spans)
    sims = cosine_similarity(devel_vectors, concept_vectors)
    devel_hits = numpy.argmax(sims, axis=1)
    predicted_labels = [concept_ids[i] for i in devel_hits]

    write(list(zip(devel_entity_ids, predicted_labels)), out_path)
    
if __name__ == '__main__':
    settings.ENTITY_TYPE = sys.argv[3]
    normalize(sys.argv[1], sys.argv[2])