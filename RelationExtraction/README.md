# Turku Bacteria-Habitat Relation Extraction

Author: Farrokh Mehryary<br>
        Turku NLP Group, Department of FT, University of Turku, Finland<br>
        email: farmeh@utu.fi<br> 
  <br>
  This code requires:<br>
           -python: version 2.7.x<br>
           -keras : version 1.2.0<br>
           -theano: version 0.8.2<br>
  <br>
  <br>You should download the built <i>word2vec</i> model from http://evexdb.org/pmresources/vec-space-models/PubMed-and-PMC-w2v.bin and place it in your local disk. Then, specify its address in <b>BB3_CONFIG_Binary.json</b> file in the source repository.<br>
  
  You should point out the program to where TEES XML files for the BB3 (BB-2016) training, development (and test) sets
  are located (either for BB3-event or BB3-event+NER tasks). 
  <br>
  You can run the program in two different modes using the --task argument:<br>
   --task predictDevel  : to train on the given training set file, then predicting given development set file<br>
   --task predictTest   : to train on the given training+development sets files, predicting given test set file<br>
  <br>
  example input arguments:<br>
python BB3_event_pipeline.py --task predictTest --trainFile /home/user1/BB_Corpora/BB_EVENT_16_BLLIP-BIO_STANFORD-CONVERT-basic_170207/BB_EVENT_16-train.xml --develFile /home/user1/BB_Corpora/BB_EVENT_16_BLLIP-BIO_STANFORD-CONVERT-basic_170207/BB_EVENT_16-devel.xml --testFile /home/user1/BB_Corpora/BB_EVENT_16_BLLIP-BIO_STANFORD-CONVERT-basic_170207/BB_EVENT_16-test.xml
<br><br>
  You may try different parsings and SD conversions, but we recommend using either <b>-basic</b> or <b>-nonCollapsed</b> SD
  conversion of the BLLIP parses. 
