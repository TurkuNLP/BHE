# Turku Bacteria-Habitat Relation Extraction

Author: Farrokh Mehryary
        Turku NLP Group, Department of FT, University of Turku, Finland 
        email: farmeh@utu.fi 
  
  This code requires:
           -python: version 2.7.x
           -keras : version 1.2.0
           -theano: version 0.8.2
  
  You should point out the program to where TEES XML files for the BB3 (BB-2016) training, development (and test) sets
  are located (either for BB3-event or BB3-event+NER tasks). 
  
  You can run the program in two different modes using the --task argument:
   --task predictDevel  : to train on the given training set file, then predicting given development set file
   --task predictTest   : to train on the given training+development sets files, predicting given test set file
        
  example input arguments: 
    --task predictTest 
    --trainFile /home/user1/BB_Corpora/BB_EVENT_16_BLLIP-BIO_STANFORD-CONVERT-basic_170207/BB_EVENT_16-train.xml
    --develFile /home/user1/BB_Corpora/BB_EVENT_16_BLLIP-BIO_STANFORD-CONVERT-basic_170207/BB_EVENT_16-devel.xml
    --testFile /home/user1/BB_Corpora/BB_EVENT_16_BLLIP-BIO_STANFORD-CONVERT-basic_170207/BB_EVENT_16-test.xml
    
  You may try different parsings and SD conversions, but we recommend using either -basic or -nonCollapsed SD
  conversion of the BLLIP parses. 
