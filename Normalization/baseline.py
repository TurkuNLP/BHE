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

from nltk.stem.snowball import PorterStemmer
stemmer = PorterStemmer()
from nltk import word_tokenize
    
def build_tfidf(concepts):
    if settings.ENTITY_TYPE == 'Habitat':
        vectorizer = TfidfVectorizer(ngram_range=(1,3), analyzer='char')
    else:
        vectorizer = TfidfVectorizer(ngram_range=(1,3), analyzer='char')
    
    concept_ids = []
    concept_names = []
    concept_map = {}
    for i, concept in enumerate(concepts):
        #if i % 10000 == 0:
        #    print i
        c_id = concept['id'][0]
        names = concept['name']
        synonyms = concept['synonym']
        
        for n in names + synonyms:
            concept_ids.append(c_id)
            concept_names.append(n)
            #if n in concept_map:
            #    print 'Warning: %s already on dictionary' % n
            concept_map[n] = c_id
    
    if settings.ENTITY_TYPE == 'Habitat':
        concept_vectors = vectorizer.fit_transform([' '.join([stemmer.stem(w) for w in word_tokenize(c)]) for c in concept_names])
    else:
        concept_vectors = vectorizer.fit_transform(concept_names)
    
    return concept_ids, concept_names, concept_map, concept_vectors, vectorizer
        
def predict():
    print 'Reading concept data'
    concepts = list(read_ontology())
    
    concept_ids, concept_names, concept_map, concept_vectors, tfidf_vectorizer = build_tfidf(concepts)
    reverse_concept_map = {concept_ids[i]:concept_names[i] for i in range(len(concept_names))}
    print 'Making predictions'
    
    devel_data = read('./data/BioNLP-ST-2016_BB-cat_dev/')
    
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
    
    devel_concepts = [d[2] for d in devel_tuples]
    
    devel_vectors = tfidf_vectorizer.transform(devel_spans)
    sims = cosine_similarity(devel_vectors, concept_vectors)
    devel_hits = numpy.argmax(sims, axis=1)
    predicted_labels = [concept_ids[i] for i in devel_hits]
    print 'Baseline accuracy: %s' % accuracy_score(devel_concepts, predicted_labels)
    #unmatched = 0
    #for threshold in [0.6]:
    #    print threshold
    #    predicted_labels = [concept_ids[i] for i in devel_hits]
    #    prev_id = None
    #    for i in range(len(devel_spans)):
    #        if numpy.max(sims[i,:]) < threshold:
    #            if devel_entity_ids[i].split('___')[0] == prev_id:
    #                print devel_spans[i], devel_spans[i-1]
    #                predicted_labels[i] = predicted_labels[i-1]
    #                unmatched += 1
    #            #import pdb; pdb.set_trace()
    #        prev_id = devel_entity_ids[i].split('___')[0]
    #    print "Unmatched: %s" % unmatched
    #    print 'Baseline accuracy: %s' % accuracy_score(devel_concepts, predicted_labels)
    #for i in range(len(predicted_labels)):
    #    if predicted_labels[i] != devel_concepts[i]:
    #        print devel_spans[i], '\t',  concept_names[devel_hits[i]], '\t', reverse_concept_map[devel_concepts[i]]
    #print len(devel_data)
    write(list(zip(devel_entity_ids, predicted_labels)), './devel-baseline/')
    
    
    #FIXME: Bad variable names
    #devel_data = read('./data/BioNLP-ST-2016_BB-cat_test/')
    devel_data = read('./final_test/')
    
    devel_tuples = []
    for entity_id, data in devel_data.items():
        entity_span = data[0]
        devel_tuples.append((entity_id, entity_span))
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
    
    #write(list(zip(devel_entity_ids, predicted_labels)), './test-baseline/')
    write(list(zip(devel_entity_ids, predicted_labels)), './final_test/')
    
    #import pdb; pdb.set_trace()
    # 4. Write predictions in a2 format
    
if __name__ == '__main__':
    predict()