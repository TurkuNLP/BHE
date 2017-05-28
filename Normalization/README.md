Before using the normalization:
Download the ontology files from
http://2016.bionlp-st.org/tasks/bb2/OntoBiotope_BioNLP-ST-2016.obo?attredirects=0  (Habitat)
and
https://drive.google.com/open?id=0B5Rh14nCn1JjbTRrX09IZ2w4dlk (Bacteria)
and place the extracted files to the data directory.
The code also requires several Python packages, e.g. scikit-learn and nltk.

Usage of the normalization script:
python normalize.py IN_PATH OUT_PATH ENTITY_TYPE
IN_PATH is the input directory containing the .a1 files with the entities
OUT_PATH is the output directory where results are stored in .a2 files
ENTITY_TYPE has to be either Habitat or Bacteria (case-sensitive!)
