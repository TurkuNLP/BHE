"""
Writes predictions to a2 files.
"""
import codecs
import os
import settings

def write(predictions, path):
    if not os.path.exists(path):
        os.makedirs(path)
    for counter, (eid, ann) in enumerate(sorted(predictions)):
        f, e = eid.split('___')
        f = f+'.a2'
        counter = _counter_offset(os.path.join(path, f))
        fi = codecs.open(os.path.join(path, f), 'a', 'utf-8')
        
        if settings.ENTITY_TYPE == 'Habitat':
            n_string = 'N%s	OntoBiotope Annotation:%s Referent:%s\n' % (counter, e, ann)
        else:
            n_string = 'N%s	NCBI_Taxonomy Annotation:%s Referent:%s\n' % (counter, e, ann)
        fi.write(n_string)
        fi.close()

def _counter_offset(filepath):
    try:
        return len(codecs.open(filepath, 'r', 'utf-8').readlines()) + 1
    except:
        return 1