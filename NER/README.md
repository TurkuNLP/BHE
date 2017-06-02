# TurkuBacteriaHabitatExtraction
End-to-End System for Bacteria Habitat Extraction.

Name entity normalization (NER). 

Softwares required for running BHE:NER include NERsuite and Genia Sentence Splitter 

The instruction for installations are provided in the following URLs
- Genia Sentence Splitter (http://www.nactem.ac.uk/y-matsu/geniass/)
- NERsuite, A named entity recognition toolkit (http://nersuite.nlplab.org/)

Prior to running NER pipeline, bash shell script (ner_pipeline.sh) should be edited to specify the directory where the BHE, NERsuites and Genia Sentence Splitter locate.

In addition, the directory of the input data should be also specified.

main_tool=~/BHE
genia_dir=~/geniass
nersuite_dir=~/nersuite-master
in_dir=~/input

After all the settings are done, the bash script can be run by this command line
./ner_pipeline.sh

The result of NER in a1 file format will be written out in a folder called 'output' in the input folder. 
