import numpy as np ; 
import GeneralFunctions as GF ; 

class FLSTM_NetworkInputGenerator:
    def __init__(self, lp , PROGRAM_Halt , Configs , wv):
        self.lp = lp ; 
        self.PROGRAM_Halt = PROGRAM_Halt ;
        self.Configs = Configs ; 
        self.wv = wv ; 


    def word_features(self, word):
        "code by Sampo:" 
        """Return array of binary surface form features for given word."""
        word = word.encode('utf-8')
        features = []
        # "is", "has" and "startswith" features for alnum, digit, etc.
        for test in (str.isalnum, str.isalpha, str.isdigit, str.islower,
             str.istitle, str.isupper):
          features.append(1 if test(str(word)) else 0)
          features.append(1 if any(c for c in word if test(str(c))) else 0)
          features.append(1 if test(str(word[0])) else 0)
        return features

    def Create_FeatureMatrix (self, Sentences):
        wv = self.wv ; 
        Method = self.Configs["ExampleGeneration"]["Method"] ;    
        self.lp (["-"*40+"NETWORK INPUT GENERATION"+"-"*40 , "-"*40+"CREATING FEATURE MATRIX" , "MAIN METHOD: SDP" , "SECOND METHOD: " + Method, "-"*40]); 

        if not Method in ["M1","M2"]:
            self.PROGRAM_Halt ("SUCH SECONDARY METHOD IS NOT IMPLEMENTED YET. CHECK CONFIG FILE."); 
            
        if self.Configs["ExampleGeneration"]["SetAllBagsLengthsEqual"]:
            if Method == "M1":
                MaxBAGLength = self.Configs["ExampleGeneration"]["M1_Bags_MaxLength"];
            elif Method == "M2":
                MaxBAGLength = self.Configs["ExampleGeneration"]["M2_Bags_MaxLength"];
            
            #Discarding sentences which have a pair with bag length exceeding the length. 
            S = Sentences ;
            Sentences = [];
            for sentence in S:
                SENTENCE_OKAY = True ;
                for pair in sentence["PAIRS"]:
                    if pair.has_key("BAGS"):
                        if Method == "M1":
                            c1 = len (pair["BAGS"]["M1_Before"][0]) <= MaxBAGLength ;
                            c2 = len (pair["BAGS"]["M1_Middle"][0]) <= MaxBAGLength ;
                            c3 = len (pair["BAGS"]["M1_After"][0])  <= MaxBAGLength ;
                        elif Method == "M2":
                            c1 = len (pair["BAGS"]["M2_ForeBetween"][0])  <= MaxBAGLength ;
                            c2 = len (pair["BAGS"]["M2_Between"][0])      <= MaxBAGLength ;
                            c3 = len (pair["BAGS"]["M2_BetweenAfter"][0]) <= MaxBAGLength ;
    
                        if (not c1) or (not c2) or (not c3):
                            SENTENCE_OKAY = False ;
                            break; 
                            
                if SENTENCE_OKAY:
                    Sentences.append (sentence);
            
            if len(S)<>len(Sentences):
                self.lp (["-------------------------------- IMPORTANT --------------------------------" , 
                          "According to param <SetAllBagsLengthsEqual>, those sentences which have pair(s) with bag(s) of length greater than:" + str(MaxBAGLength) + " ARE EXCLUDED!" ,
                          "============================== NUMBER OF SENTENCES BEFORE FILTERING:" + str(len(S)) , 
                          "============================== NUMBER OF SENTENCES AFTERR FILTERING:" + str(len(Sentences))])
               
        M1_Before, M1_Middle , M1_After , M2_ForeBetween , M2_Between , M2_BetweenAfter = GF.CorpusHelper.CalculateMaxLengthForAllBags (Sentences) ; 
        
        LPMSG = ["-"*80, "-"*30+"   IMPORTANT INFORMATION     "+"-"*30,
                 "Since there might be some relations in the sentences that there is no path between their candidate entities, those will be excluded!" , "" ,
                 "Checking VALID EXAMPLE COUNT:"];
                 
        #<<<CRITICAL>>>
        POS_NEG_DICT  , CLASS_TP_DICT , Total_Example_CNT = GF.CorpusHelper.HowManyRelationsWithShortestPathInDataset (Sentences); 
        LPMSG.append ("POSITIVE NEGATIVE STATISTICS:"); 
        LPMSG.append ("\t" + str (POS_NEG_DICT));
        LPMSG.append ("-"*30); 
        LPMSG.append ("CLASS DISTRIBUTION STATISTICS:"); 
        for _tempkey in sorted(list(CLASS_TP_DICT.keys())):
            LPMSG.append ("\t" + _tempkey + " : " + str(CLASS_TP_DICT[_tempkey])); 
        LPMSG.append ("-"*30); 
        LPMSG.append ("<<<FINAL>>> NUMBER OF EXAMPLES THAT WILL BE USED FOR FEATURE CREATION:"+ str (Total_Example_CNT));
        LPMSG.append ("-"*80)
        self.lp (LPMSG) ; 
        
        if self.Configs["ClassificationType"]== "binary":
            y = np.zeros (Total_Example_CNT, dtype=np.int16); 
            y_reverse = None #TODO: How should I handle reverse relations in case of binary classification? False ? 
            y_coarse  = None #No coarse label in case of binary classification
            y_binary  = None #Why do you need y_binary? y is binary itself ...
            
        else: #multiclass
            #y: normal multiclass softmax 
            HowManyColumnsForOneHotEncoding = len (self.Configs["OneHotEncodingForMultiClass"]); 
            y = np.zeros ((Total_Example_CNT, HowManyColumnsForOneHotEncoding),dtype=np.int16); 
            
            #y_coarse: directionless softmax
            HowManyColumnsForCoarseOneHotEncoding = len (self.Configs["OneHotEncodingForCoarseMultiClass"]); 
            y_coarse = np.zeros ((Total_Example_CNT, HowManyColumnsForCoarseOneHotEncoding),dtype=np.int16); 
            
            #y_binary: positive/negative
            y_binary = np.zeros (Total_Example_CNT, dtype=np.int16); 
            
            #y_reverse:
            if self.Configs["ExampleGeneration"]["Generate_Reversed_SDP_Features"]==True:
                y_reverse = np.zeros ((Total_Example_CNT, HowManyColumnsForOneHotEncoding),dtype=np.int16); 
            else:
                y_reverse = None
                
            
        SENTENCE_INDEX = np.zeros (Total_Example_CNT); #for pairs .. so, if sentence one has 3 examples and sentence two has four --> 1112222 
        WORD_FEATURE_SIZE = len (self.word_features("test")) ; 
    
        PAIR_TRACKING = [] ; #<<<CRITICAL>>> for tracking and writing back prediction results ... 
        
        if Method == "M1":
            self.lp ("Different MAX of Bags-Length: " + str(M1_Before) + "\t" + str(M1_Middle) + "\t" + str(M1_After)); 
            if self.Configs["ExampleGeneration"]["SetAllBagsLengthsEqual"]==True:
                M1_Before = M1_Middle = M1_After = MaxBAGLength ;
                self.lp (["According to set parameter 'SetAllBagsLengthsEqual', setting all bag sizes to the max:", 
                          "ALL Bags-Length: " + str(M1_Before) + "\t" + str(M1_Middle) + "\t" + str(M1_After)]); 
            #Matrices for word_indices_in_w2v model. each row: a sentence, each column: a word_index in sentence. 
            x1_words = np.zeros ((Total_Example_CNT, M1_Before), dtype = np.int64) ; 
            x2_words = np.zeros ((Total_Example_CNT, M1_Middle), dtype = np.int64) ; 
            x3_words = np.zeros ((Total_Example_CNT, M1_After) , dtype = np.int64) ; 
            #Matrices for postags. each row: a sentence, each column: a word_index in sentence. 
            x1_postags = np.zeros ((Total_Example_CNT, M1_Before), dtype = np.int64) ; 
            x2_postags = np.zeros ((Total_Example_CNT, M1_Middle), dtype = np.int64) ; 
            x3_postags = np.zeros ((Total_Example_CNT, M1_After) , dtype = np.int64) ; 
            #Matrices for word features: 
            x1_features = np.zeros ((Total_Example_CNT, M1_Before , WORD_FEATURE_SIZE) , dtype = np.int64)
            x2_features = np.zeros ((Total_Example_CNT, M1_Middle , WORD_FEATURE_SIZE) , dtype = np.int64)
            x3_features = np.zeros ((Total_Example_CNT, M1_After  , WORD_FEATURE_SIZE) , dtype = np.int64)
            
        elif Method == "M2":
            self.lp ("Different MAX of Bags-Length: " + str(M2_ForeBetween) + "\t" + str(M2_Between) + "\t" + str(M2_BetweenAfter)); 
            if self.Configs["ExampleGeneration"]["SetAllBagsLengthsEqual"]==True:
                M2_ForeBetween = M2_Between = M2_BetweenAfter = MaxBAGLength ; 
                self.lp (["According to set parameter 'SetAllBagsLengthsEqual', setting all bag sizes to the max:",
                          "ALL Bags-Length: " + str(M2_ForeBetween) + "\t" + str(M2_Between) + "\t" + str(M2_BetweenAfter)]) ;
            #Matrices for word_indices_in_w2v model. each row: a sentence, each column: a word_index in sentence. 
            x1_words   = np.zeros ((Total_Example_CNT, M2_ForeBetween) , dtype = np.int64) ; 
            x2_words   = np.zeros ((Total_Example_CNT, M2_Between    ) , dtype = np.int64) ; 
            x3_words   = np.zeros ((Total_Example_CNT, M2_BetweenAfter), dtype = np.int64) ; 
            #Matrices for postags. each row: a sentence, each column: a word_index in sentence. 
            x1_postags = np.zeros ((Total_Example_CNT, M2_ForeBetween) , dtype = np.int64) ; 
            x2_postags = np.zeros ((Total_Example_CNT, M2_Between    ) , dtype = np.int64) ; 
            x3_postags = np.zeros ((Total_Example_CNT, M2_BetweenAfter), dtype = np.int64) ; 
            #Matrices for word features: 
            x1_features = np.zeros ((Total_Example_CNT, M2_ForeBetween , WORD_FEATURE_SIZE) , dtype = np.int64)
            x2_features = np.zeros ((Total_Example_CNT, M2_Between     , WORD_FEATURE_SIZE) , dtype = np.int64)
            x3_features = np.zeros ((Total_Example_CNT, M2_BetweenAfter, WORD_FEATURE_SIZE) , dtype = np.int64)
        
        #<<<CRITICAL>>> Optimal setting of MAX SDP Length ... 
        Requested_MaxSDPLength = self.Configs["ExampleGeneration"]["SDP_MAXLEN_BECAREFUL"] ; 
        if Requested_MaxSDPLength == None:
            MaxSDPLength = MaxBAGLength ; 
            self.lp ("[WARNING]:SDP_MAXLEN_BECAREFUL is not defined in the config file, hence it is set to:" + str(MaxBAGLength)); 
        else:
            Corpus_MaxSDPLength = GF.CorpusHelper.ReturnMAXSDPLength (Sentences); 
            if Corpus_MaxSDPLength > Requested_MaxSDPLength:
                MSG = ["[WARNING]: Requested SDP_MAXLEN_BECAREFUL is "+str(Requested_MaxSDPLength) + "."];
                MSG.append ("Which is less than real maximum SDP length in the corpus: " + str(Corpus_MaxSDPLength));
                MSG.append ("Hences, setting: SDP_MAXLEN_BECAREFUL = " + str(Corpus_MaxSDPLength))
                self.lp (MSG);
                MaxSDPLength = Corpus_MaxSDPLength ; 
            else:
                MaxSDPLength = Requested_MaxSDPLength ; 
                self.lp ("SDP_MAXLEN_BECAREFUL is set to " + str(Requested_MaxSDPLength)) ; 
                
        #SDP Features    
        sp_words   = np.zeros ((Total_Example_CNT, MaxSDPLength), dtype = np.int64) ; 
        sp_postags = np.zeros ((Total_Example_CNT, MaxSDPLength), dtype = np.int64) ; 
        sp_edgetgs = np.zeros ((Total_Example_CNT, MaxSDPLength-1), dtype = np.int64) ;#<<<CRITICAL>>> Dependency maxlen should be word-1 for interleaving
        
        #REVERSE-SDP Features
        if self.Configs["ExampleGeneration"]["Generate_Reversed_SDP_Features"]==True:
            rev_sp_words   = np.zeros ((Total_Example_CNT, MaxSDPLength), dtype = np.int64) ; 
            rev_sp_postags = np.zeros ((Total_Example_CNT, MaxSDPLength), dtype = np.int64) ; 
            rev_sp_edgetgs = np.zeros ((Total_Example_CNT, MaxSDPLength-1), dtype = np.int64) ;#<<<CRITICAL>>> Dependency maxlen should be word-1 for interleaving
        else:
            rev_sp_words   = None
            rev_sp_postags = None
            rev_sp_edgetgs = None
            
        NFRV = (wv.vectors.shape[0])-1 ; #Not Found Return Value = Index of last embedding (row) in the model matrix
        
        def GetWordIndexInTheModel (word , wv , not_found_return_value):
            if not word in wv:
                #return not_found_return_value ; #CRITICAL CRITICAL CRITICAL CRITICAL CRITICAL .... 
                lowerw = word.lower(); 
                if lowerw in wv:
                    idx=wv[lowerw]
                    return idx if idx < (wv.max_rank_mem - 1) else not_found_return_value ; 
                else:
                    return not_found_return_value ; 
            else:
                idx=wv[word]
                return idx if idx < (wv.max_rank_mem - 1) else not_found_return_value ; 
        
        #OLD: example_pair_entity_feature = np.zeros ((Total_Example_CNT,6), dtype=np.int64) ;
        #NEW:
        example_pair_entity_feature = np.zeros ((Total_Example_CNT,2*len(self.Configs["OneHotEncodingForValidEnityTypesForRelations"])), dtype=np.int64) ;
        
        # DO in PARALLEL:
        #   - START FILTERING OUT SENTENCES WITHOUT SDP
        #   - START CREATING FEATURES ...
        seen_pair_count = 0 ; 
        for Sentence_Index , S in enumerate (Sentences):
            #<<<CRITICAL>>>: Skip Sentences without any interactions
            for pair in S["PAIRS"]:
                #<<<CRITICAL>>>: Skip pairs that don't have a SDP for any reason (e.g., parsing break)
                if (pair.has_key("BAGS")) and (pair.has_key("SHORTEST_PATH_F")):
                    if pair["SHORTEST_PATH_F"] == None:
                        continue ; 
                    
                    e1_type = S["ENTITIES"][pair["E1"]]["TYPE"]; 
                    e2_type = S["ENTITIES"][pair["E2"]]["TYPE"]; 
                    
                    #Tracking: for later writing-back the prediction results into XML
                    _e1tp = e1_type.capitalize()
                    _e2tp = e2_type.capitalize()
                    PAIR_TRACKING.append ( (S["ID"] , pair["ID"] , pair["E1"] , pair["E2"], _e1tp , _e2tp) )
                    
                    e1_startidx = S["ENTITIES"][pair["E1"]]["CHAROFFSETS"][0]
                    e2_startidx = S["ENTITIES"][pair["E2"]]["CHAROFFSETS"][0]
                    
                    #CRITICAL CRITICAL CRITICAL CRITICAL CRITICAL .... 
                    if e2_startidx > e1_startidx:
                        #Convension ... F[0:N-1]: ALWAYS Second entity in sentence , F[N:N+N-1]: ALWAYS First Entity In sentence ... 
                        e1_type , e2_type = e2_type , e1_type 
                    
                    """ OLD :                        
                    if e1_type == "bacteria":
                        example_pair_entity_feature[seen_pair_count,0]=1
                    elif e1_type == "habitat":
                        example_pair_entity_feature[seen_pair_count,1]=1
                    elif e1_type == "geographical":
                        example_pair_entity_feature[seen_pair_count,2]=1
                    else:
                        print "ERRROR IN ENTITY TYPE!!!" ; 
                        sys.exit (-1);
                        
                    if e2_type == "bacteria":
                        example_pair_entity_feature[seen_pair_count,3]=1
                    elif e2_type == "habitat":
                        example_pair_entity_feature[seen_pair_count,4]=1
                    elif e2_type == "geographical":
                        example_pair_entity_feature[seen_pair_count,5]=1
                    else:
                        print "ERRROR IN ENTITY TYPE!!!" ; 
                        sys.exit (-1);
                    """ 
                    # NEW: 
                    e1_tp , e2_tp = e1_type.lower() , e2_type.lower() ;
                    if (not e1_tp in self.Configs["OneHotEncodingForValidEnityTypesForRelations"]) or (not e2_tp in self.Configs["OneHotEncodingForValidEnityTypesForRelations"]):
                        self.PROGRAM_Halt ("INVALID ENTITY TYPE:" + e1_tp + ". Check Config file!"); 
                    ETP1_COLUMN_IDX = self.Configs["OneHotEncodingForValidEnityTypesForRelations"][e1_tp] ; 
                    ETP2_COLUMN_IDX = len(self.Configs["OneHotEncodingForValidEnityTypesForRelations"]) + self.Configs["OneHotEncodingForValidEnityTypesForRelations"][e2_tp] ; 
                    example_pair_entity_feature[seen_pair_count, ETP1_COLUMN_IDX] = 1 ;
                    example_pair_entity_feature[seen_pair_count, ETP2_COLUMN_IDX] = 1 ; 
                    
                    #Shortest Path Features ... 
                    _sp_w    = np.array ([GetWordIndexInTheModel (w,wv,NFRV) for w in pair["SHORTEST_PATH_F"][0]], dtype=np.int64) ;
                    _sp_ptgs = np.array (pair["SHORTEST_PATH_F"][1]);
                    _sp_dtgs = np.array (pair["SHORTEST_PATH_F"][2]);
                    
                    #Reverse Shortest Path Features ...
                    if self.Configs["ExampleGeneration"]["Generate_Reversed_SDP_Features"]==True:
                        _rev_sp_w    = np.array ([GetWordIndexInTheModel (w,wv,NFRV) for w in pair["SHORTEST_PATH_F_REV"][0]], dtype=np.int64) ;
                        _rev_sp_ptgs = np.array (pair["SHORTEST_PATH_F_REV"][1]);
                        _rev_sp_dtgs = np.array (pair["SHORTEST_PATH_F_REV"][2]);
    
                    if Method=="M1":
                        x1_b = np.array ([GetWordIndexInTheModel (w,wv,NFRV) for w  in pair["BAGS"]["M1_Before"][0]] , dtype=np.int64) ;
                        x2_b = np.array ([GetWordIndexInTheModel (w,wv,NFRV) for w  in pair["BAGS"]["M1_Middle"][0]] , dtype=np.int64) ;
                        x3_b = np.array ([GetWordIndexInTheModel (w,wv,NFRV) for w  in pair["BAGS"]["M1_After"] [0]] , dtype=np.int64) ;
                        x1_posb = np.array (pair["BAGS"]["M1_Before"][1] , dtype = np.int16);
                        x2_posb = np.array (pair["BAGS"]["M1_Middle"][1] , dtype = np.int16);
                        x3_posb = np.array (pair["BAGS"]["M1_After"][1]  , dtype = np.int16);
                        x1_feat = np.array ([self.word_features(word) for word in pair["BAGS"]["M1_Before"][0]] , dtype=np.int64)
                        x2_feat = np.array ([self.word_features(word) for word in pair["BAGS"]["M1_Middle"][0]] , dtype=np.int64)
                        x3_feat = np.array ([self.word_features(word) for word in pair["BAGS"]["M1_After"][0]] , dtype=np.int64)
                        
                    elif Method=="M2":
                        x1_b = np.array ([GetWordIndexInTheModel (w,wv,NFRV) for w  in pair["BAGS"]["M2_ForeBetween"][0]]  , dtype=np.int64) ;
                        x2_b = np.array ([GetWordIndexInTheModel (w,wv,NFRV) for w  in pair["BAGS"]["M2_Between"][0]]      , dtype=np.int64) ;
                        x3_b = np.array ([GetWordIndexInTheModel (w,wv,NFRV) for w  in pair["BAGS"]["M2_BetweenAfter"][0]] , dtype=np.int64) ;
                        x1_posb = np.array (pair["BAGS"]["M2_ForeBetween"][1]  , dtype = np.int16);
                        x2_posb = np.array (pair["BAGS"]["M2_Between"][1]      , dtype = np.int16);
                        x3_posb = np.array (pair["BAGS"]["M2_BetweenAfter"][1] , dtype = np.int16);
                        x1_feat = np.array ([self.word_features(word) for word in pair["BAGS"]["M2_ForeBetween"][0]]  , dtype=np.int64)
                        x2_feat = np.array ([self.word_features(word) for word in pair["BAGS"]["M2_Between"][0]]      , dtype=np.int64)
                        x3_feat = np.array ([self.word_features(word) for word in pair["BAGS"]["M2_BetweenAfter"][0]] , dtype=np.int64)
    
                    #Critical                
                    if self.Configs["ExampleGeneration"]["PadVectorsFromLeft"]==True:
                        try:
                            x1_words[seen_pair_count, x1_words.shape[1]-len(x1_b):] = x1_b;
                            x2_words[seen_pair_count, x2_words.shape[1]-len(x2_b):] = x2_b; 
                            x3_words[seen_pair_count, x3_words.shape[1]-len(x3_b):] = x3_b;

                            x1_postags[seen_pair_count, x1_postags.shape[1]-len(x1_posb):] = x1_posb ; 
                            x2_postags[seen_pair_count, x2_postags.shape[1]-len(x2_posb):] = x2_posb ; 
                            x3_postags[seen_pair_count, x3_postags.shape[1]-len(x3_posb):] = x3_posb ; 

                            if (len(x1_feat) > 0): x1_features[seen_pair_count][x1_features.shape[1]-x1_feat.shape[0]:] = x1_feat; 
                            if (len(x2_feat) > 0): x2_features[seen_pair_count][x2_features.shape[1]-x2_feat.shape[0]:] = x2_feat; 
                            if (len(x3_feat) > 0): x3_features[seen_pair_count][x3_features.shape[1]-x3_feat.shape[0]:] = x3_feat; 
                            
                            sp_words   [seen_pair_count, sp_words.shape[1]  -len(_sp_w):]    = _sp_w;
                            sp_postags [seen_pair_count, sp_postags.shape[1]-len(_sp_ptgs):] = _sp_ptgs ; 
                            sp_edgetgs [seen_pair_count, sp_edgetgs.shape[1]-len(_sp_dtgs):] = _sp_dtgs ; 
                            
                            if self.Configs["ExampleGeneration"]["Generate_Reversed_SDP_Features"]==True:
                                rev_sp_words   [seen_pair_count, rev_sp_words.shape[1]  -len(_rev_sp_w):] = _rev_sp_w;
                                rev_sp_postags [seen_pair_count, rev_sp_postags.shape[1]-len(_rev_sp_ptgs):] = _rev_sp_ptgs ; 
                                rev_sp_edgetgs [seen_pair_count, rev_sp_edgetgs.shape[1]-len(_rev_sp_dtgs):] = _rev_sp_dtgs ; 
                                
                        except Exception as E:
                            self.PROGRAM_Halt ("Exception: " + E.message)

                    else:
                        x1_words[seen_pair_count,0:len(x1_b)] = x1_b
                        x2_words[seen_pair_count,0:len(x2_b)] = x2_b
                        x3_words[seen_pair_count,0:len(x3_b)] = x3_b
        
                        x1_postags[seen_pair_count,0:len(x1_posb)] = x1_posb
                        x2_postags[seen_pair_count,0:len(x2_posb)] = x2_posb
                        x3_postags[seen_pair_count,0:len(x3_posb)] = x3_posb

                        if (len(x1_feat) > 0): x1_features[seen_pair_count][0:x1_feat.shape[0]] = x1_feat 
                        if (len(x2_feat) > 0): x2_features[seen_pair_count][0:x2_feat.shape[0]] = x2_feat  
                        if (len(x3_feat) > 0): x3_features[seen_pair_count][0:x3_feat.shape[0]] = x3_feat  

                        sp_words   [seen_pair_count, 0:len(_sp_w):]    = _sp_w
                        sp_postags [seen_pair_count, 0:len(_sp_ptgs):] = _sp_ptgs 
                        sp_edgetgs [seen_pair_count, 0:len(_sp_dtgs):] = _sp_dtgs 
                    
                        if self.Configs["ExampleGeneration"]["Generate_Reversed_SDP_Features"]==True:
                            rev_sp_words   [seen_pair_count, 0:len(_rev_sp_w):]    = _rev_sp_w
                            rev_sp_postags [seen_pair_count, 0:len(_rev_sp_ptgs):] = _rev_sp_ptgs 
                            rev_sp_edgetgs [seen_pair_count, 0:len(_rev_sp_dtgs):] = _rev_sp_dtgs 

                    #<<<CRITICAL>>>
                    if self.Configs["ClassificationType"]== "binary":
                        y [seen_pair_count] = 1 if (pair["POSITIVE"]==True) else 0 ; 
                        
                    else: #MULTICLASS:
                        #Positive/Negative:
                        y_binary [seen_pair_count] = 1 if (pair["POSITIVE"]==True) else 0 ; 
                        
                        if pair["POSITIVE"]==False:
                            y        [seen_pair_count,0]=1;#index zero is always for negative class(es)
                            y_coarse [seen_pair_count,0]=1;#index zero is always for negative class(es)
                            
                            #<<<CRITICAL>>> <<<CRITICAL>>> The class that is defined as negative, will never has direction!                             
                            #Hence, for both forward and backward networks, will have [1,0,0,0,...,0] as coded Y_labels. 
                            if self.Configs["ExampleGeneration"]["Generate_Reversed_SDP_Features"]==True:
                                y_reverse[seen_pair_count,0]=1;#index zero is always for negative class(es)

                        else:
                            class_label = pair["CLASS_TP"] ; 
                            OneHotIndex = self.Configs["OneHotEncodingForMultiClass"][class_label]; 
                            y[seen_pair_count, OneHotIndex] = 1 ;

                            lbl_coarse = class_label.split("(e1,e2)")[0].split("(e2,e1)")[0] ;
                            OneHotIndex = self.Configs["OneHotEncodingForCoarseMultiClass"][lbl_coarse]; 
                            y_coarse[seen_pair_count, OneHotIndex] = 1 ; 

                            if self.Configs["ExampleGeneration"]["Generate_Reversed_SDP_Features"]==True:
                                if "(e1,e2)" in class_label:
                                    rev_lbl = class_label.replace ("(e1,e2)" , "(e2,e1)"); 
                                    OneHotIndex = self.Configs["OneHotEncodingForMultiClass"][rev_lbl]; 
                                elif "(e2,e1)" in class_label:
                                    rev_lbl = class_label.replace ("(e2,e1)" , "(e1,e2)"); 
                                    OneHotIndex = self.Configs["OneHotEncodingForMultiClass"][rev_lbl]; 
                                else:
                                    OneHotIndex = self.Configs["OneHotEncodingForMultiClass"][class_label]; #Class is not directional !
                                
                                y_reverse[seen_pair_count, OneHotIndex] = 1 ; 
                                            
                            
                    SENTENCE_INDEX[seen_pair_count] = Sentence_Index;
                    seen_pair_count+=1 ; 
        print "done." ; 
    
        return SENTENCE_INDEX , [x1_words,x2_words,x3_words] , [x1_postags,x2_postags,x3_postags] , [x1_features,x2_features,x3_features] , \
               example_pair_entity_feature , PAIR_TRACKING , \
               [sp_words,sp_postags,sp_edgetgs] , [rev_sp_words,rev_sp_postags,rev_sp_edgetgs] , \
               y , y_reverse , y_coarse , y_binary; 


#--------------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------
    

    def Get_Data_ALL_FROM_Sentences (self,Sentences): 

        RES = self.Create_FeatureMatrix (Sentences) ; 
        
        SENTENCE_INDEX              = RES[0]
        WORDS_MATRICES              = RES[1]
        POSTAGS_MATRICES            = RES[2]
        FEATURE_MATRICES            = RES[3]
        example_pair_entity_feature = RES[4]
        PAIR_TRACKING               = RES[5]
        SP_FEATURES                 = RES[6]
        SP_FEATURES_REV             = RES[7]
        y                           = RES[8]
        y_reverse                   = RES[9]
        y_coarse                    = RES[10]
        y_binary                    = RES[11]
        
        return {"Configs"         : self.Configs, 
                "Sentences"       : Sentences ,
                "SENTENCE_INDEX"  : SENTENCE_INDEX, 
                "split_log"       : "100% one chunk" , 
                "DS"              :
                    {
                      "Word_Matrices"               : WORDS_MATRICES,
                      "PosTag_Matrices"             : POSTAGS_MATRICES, 
                      "WordFeature_Matrices"        : FEATURE_MATRICES, 
                      "example_pair_entity_feature" : example_pair_entity_feature , 
                      "SP_FEATURES"                 : SP_FEATURES , 
                      "SP_FEATURES_REV"             : SP_FEATURES_REV , 
                      "y_vector"                    : y , 
                      "y_vector_reverse"            : y_reverse , 
                      "y_vector_coarse"             : y_coarse ,
                      "y_vector_binary"             : y_binary 
                    } ,
                "PAIR_TRACKING" : PAIR_TRACKING ,     
        }

 
