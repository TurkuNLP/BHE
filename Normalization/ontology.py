"""
Reads the OntoBiotope ontology
"""
from collections import defaultdict
import csv
import settings


def process_concept(concept_dict):
    concept_dict['synonym'] = [list(csv.reader(s, delimiter=' ', quotechar='"'))[0][0] for s in concept_dict['synonym']]
    return concept_dict

def read_ontology():
    if settings.ENTITY_TYPE == 'Habitat':
        return read_biotope_ontology('./data/OntoBiotope_BioNLP-ST-2016.obo')
    else:
        return read_tax_ontology('./data/names.dmp')

def read_biotope_ontology(path):
    with open(path, "r") as infile:
        current_term = None
        for line in infile:
            line = line.strip()
            if not line: continue #Skip empty
            if line == "[Term]":
                if current_term: yield process_concept(current_term)
                current_term = defaultdict(list)
            else: #Not [Term]
                #Only process if we're inside a [Term] environment
                if current_term is None: continue
                key, sep, val = line.partition(":")
                current_term[key].append(val.strip())
        #Add last term
        if current_term is not None:
            yield process_concept(current_term)
            
def read_tax_ontology(path):
    bacteria_ids = set([l.strip() for l in open(settings.BACTERIA_LIST, 'r')])
    
    terms = defaultdict(lambda: defaultdict(list))
    
    with open(path, "r") as infile:
        current_term = None
        for i, line in enumerate(infile):
            #if i % 10000 == 0:
            #    print i
            data = line.replace('\t', '').split('|')
            if not data[0] in bacteria_ids:
                continue
            terms[data[0]]['id'] = [data[0]]
            if data[3] == 'scientific name':
                terms[data[0]]['name'].append(data[1])
            elif data[3] == 'synonym':
                terms[data[0]]['synonym'].append(data[1])
    #import pdb; pdb.set_trace()
    return terms.values()
            
if __name__ == '__main__':
    read_tax_ontology('./data/names.dmp')