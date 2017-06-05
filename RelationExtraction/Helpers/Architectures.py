class FLSTM_RE_Architectures:
    def __init__ (self, TrainingData, wv, lp, PROGRAM_Halt, Configs, RandomSeed=None):
        self.TD = TrainingData
        self.wv           = wv 
        self.lp           = lp
        self.PROGRAM_Halt = PROGRAM_Halt
        self.Configs      = Configs 
        self.model = None ; 
        self.Reset_WhichFeatureToUse(); 
        import SharedVariables as SV ; 
        self.POSEmb_VocabSize = len(SV.PENN_TB_POS_TAGS)+1 ;   #Position 0 for padding
        self.DTEmb_VocabSize  = len(SV.STANFORD_DEPTP_TAGS)+1 ;#Position 0 for padding
        
        MSG = ["Initializing FLSTM_RE_Architectures object."]; 
        if RandomSeed==None:
            import datetime ; 
            RandomSeed = datetime.datetime.now().microsecond;
            MSG.append ("   - RANDOM SEED IS <<<NOT>>> GIVEN! SETTING AUTOMATICALLY:" + str(RandomSeed)); 
        else:
            MSG.append ("   - RANDOM_SEED IS GIVEN :" + str(RandomSeed)); 
            
        self.RandomSeed = RandomSeed ;
        self.lp (MSG); 
            
    def Reset_WhichFeatureToUse (self):
        self.WhichFeaturesToUse = {
            "Bags_WordEmbeddings_B1"        : False , 
            "Bags_WordEmbeddings_B2"        : False , 
            "Bags_WordEmbeddings_B3"        : False , 
            "Bags_PosTagEmbeddings_B1"      : False , 
            "Bags_PosTagEmbeddings_B2"      : False , 
            "Bags_PosTagEmbeddings_B3"      : False , 
            "Bags_WordShapeFeatures_B1"     : False ,
            "Bags_WordShapeFeatures_B2"     : False ,
            "Bags_WordShapeFeatures_B3"     : False ,
            "PairEntityFeatures"            : False , 
            "Forward_SDP_WordEmbeddings"    : False , 
            "Forward_SDP_PosTagEmbeddings"  : False , 
            "Forward_SDP_DTEmbeddings"      : False , 
            "Backward_SDP_WordEmbeddings"   : False , 
            "Backward_SDP_PosTagEmbeddings" : False , 
            "Backward_SDP_DTEmbeddings"     : False , 
        }
        self.WhichOutputsToPredit = {
            "y_vector"                      : False , 
            "y_vector_reverse"              : False , 
            "y_vector_coarse"               : False , 
            "y_vector_binary"               : False ,
        }
        self.model = None ; 
        
    def BuildArchitecture_BioNLPST2016_Paper (self):
        #<<<CRITICAL>>> : Setting np random seed everytime BEFORE IMPORTING FROM KERAS!
        self.lp ("Building Neural Network Model. RandomSeed:" + str(self.RandomSeed) + "  , Please wait ..."); 
        import numpy as np ; 
        np.random.seed (self.RandomSeed) ; 
        from keras.models import Model ; 
        from keras.layers import Input, LSTM, Embedding, Dense, Dropout, merge ; 
        #END OF <<<CRITICAL>>>
        
        self.Reset_WhichFeatureToUse(); 
        self.WhichFeaturesToUse["PairEntityFeatures"]           =True; 
        self.WhichFeaturesToUse["Forward_SDP_WordEmbeddings"]   =True;
        self.WhichFeaturesToUse["Forward_SDP_PosTagEmbeddings"] =True;
        self.WhichFeaturesToUse["Forward_SDP_DTEmbeddings"]     =True; 
        self.WhichOutputsToPredit["y_vector"]                   =True; 
        
        max_features      = self.wv.vectors.shape[0]
        wv_embedding_size = self.wv.vectors.shape[1]

        #Inputs        
        MODEL_INPUT_SDP_W = Input (shape=(self.TD["Forward_SDP_WordEmbeddings"].shape[1],)  , name="Forward_SDP_WordEmbeddings"); 
        MODEL_INPUT_SDP_P = Input (shape=(self.TD["Forward_SDP_PosTagEmbeddings"].shape[1],), name="Forward_SDP_PosTagEmbeddings"); 
        MODEL_INPUT_SDP_D = Input (shape=(self.TD["Forward_SDP_DTEmbeddings"].shape[1],)    , name="Forward_SDP_DTEmbeddings" ); 
        MODEL_INPUT_EP    = Input (shape=(self.TD["PairEntityFeatures"].shape[1],)          , name="PairEntityFeatures"); 
        
        #Embeddings
        MODEL_E1 = Embedding(input_dim = max_features , output_dim = wv_embedding_size , input_length=self.TD["Forward_SDP_WordEmbeddings"].shape[1]   , weights=[self.wv.vectors], mask_zero=True , trainable=True)(MODEL_INPUT_SDP_W); 
        MODEL_E2 = Embedding(input_dim = self.POSEmb_VocabSize , output_dim = 90       , input_length=self.TD["Forward_SDP_PosTagEmbeddings"].shape[1] , init='uniform'           , mask_zero=True , trainable=True)(MODEL_INPUT_SDP_P);
        MODEL_E3 = Embedding(input_dim = self.DTEmb_VocabSize  , output_dim = 350      , input_length=self.TD["Forward_SDP_DTEmbeddings"].shape[1]     , init='uniform'           , mask_zero=True , trainable=True)(MODEL_INPUT_SDP_D);
        
        #LSTM
        MODEL_LSTM1 = LSTM(output_dim=128, activation='sigmoid')(MODEL_E1) 
        MODEL_LSTM2 = LSTM(output_dim=128, activation='sigmoid')(MODEL_E2) 
        MODEL_LSTM3 = LSTM(output_dim=128, activation='sigmoid')(MODEL_E3) 

        #Merge
        MODEL_MERGE = merge([MODEL_LSTM1, MODEL_LSTM2, MODEL_LSTM3, MODEL_INPUT_EP], mode='concat', concat_axis=-1)
        
        #Dense
        MODEL_DENSE_1 = Dense(output_dim=128, activation='sigmoid')(MODEL_MERGE)
        MODEL_DROP_1  = Dropout(0.5)(MODEL_DENSE_1) 

        if self.Configs["ClassificationType"] == "binary":
            MODEL_OUTPUT  = Dense(1, init='uniform', activation='sigmoid' , name="y_vector")(MODEL_DROP_1)
        else:
            NumberOfClassesInMultiClassification = len (self.Configs["OneHotEncodingForMultiClass"])
            MODEL_OUTPUT  = Dense(NumberOfClassesInMultiClassification, activation='softmax' , name="y_vector")(MODEL_DROP_1)
            
        self.model = Model(input=[MODEL_INPUT_SDP_W, MODEL_INPUT_SDP_P, MODEL_INPUT_SDP_D, MODEL_INPUT_EP], output=[MODEL_OUTPUT]); 
        return self.model , self.WhichFeaturesToUse , self.WhichOutputsToPredit;

    def BuildArchitecture_SimpleCNN_WPD (self,POSE_dim, DTE_dim, PARAM_nb_filter,PARAM_filter_length,PARAM_DD):
        #<<<CRITICAL>>> : Setting np random seed everytime BEFORE IMPORTING FROM KERAS!
        self.lp ("Building Neural Network Model. RandomSeed:" + str(self.RandomSeed) + "  , Please wait ..."); 
        import numpy as np ; 
        np.random.seed (self.RandomSeed) ; 
        from keras.models import Model ; 
        from keras.layers import Input, Embedding, Dense, Dropout, merge , Conv1D 
        from KerasHelpers import ZeroMaskingLayer;
        from keras.layers.pooling import GlobalMaxPooling1D 
        #END OF <<<CRITICAL>>>
        
        self.Reset_WhichFeatureToUse(); 
        self.WhichFeaturesToUse["Forward_SDP_WordEmbeddings"]   =True;
        self.WhichFeaturesToUse["Forward_SDP_PosTagEmbeddings"] =True;
        self.WhichFeaturesToUse["Forward_SDP_DTEmbeddings"]     =True; 
        self.WhichOutputsToPredit["y_vector"]                   =True; 
        
        max_features      = self.wv.vectors.shape[0]
        wv_embedding_size = self.wv.vectors.shape[1]

        #Inputs        
        MODEL_INPUT_SDP_W = Input (shape=(self.TD["Forward_SDP_WordEmbeddings"].shape[1],)  , dtype='int32' , name="Forward_SDP_WordEmbeddings"); 
        MODEL_INPUT_SDP_P = Input (shape=(self.TD["Forward_SDP_PosTagEmbeddings"].shape[1],), dtype='int32' , name="Forward_SDP_PosTagEmbeddings"); 
        MODEL_INPUT_SDP_D = Input (shape=(self.TD["Forward_SDP_DTEmbeddings"].shape[1],)    , dtype='int32' , name="Forward_SDP_DTEmbeddings" ); 
        
        #Embeddings
        MODEL_E1 = Embedding(input_dim = max_features , output_dim = wv_embedding_size , input_length=self.TD["Forward_SDP_WordEmbeddings"].shape[1]   , weights=[self.wv.vectors], mask_zero=True , trainable=True)(MODEL_INPUT_SDP_W); 
        MODEL_E2 = Embedding(input_dim = self.POSEmb_VocabSize , output_dim = POSE_dim , input_length=self.TD["Forward_SDP_PosTagEmbeddings"].shape[1] , init='uniform'           , mask_zero=True , trainable=True)(MODEL_INPUT_SDP_P);
        MODEL_E3 = Embedding(input_dim = self.DTEmb_VocabSize  , output_dim = DTE_dim  , input_length=self.TD["Forward_SDP_DTEmbeddings"].shape[1]     , init='uniform'           , mask_zero=True , trainable=True)(MODEL_INPUT_SDP_D);
        
        #ZeroMasking:
        MODEL_E1 = ZeroMaskingLayer.ZeroMaskedEntries(name="ZeroMsk1")(MODEL_E1)                
        MODEL_E2 = ZeroMaskingLayer.ZeroMaskedEntries(name="ZeroMsk2")(MODEL_E2)                
        MODEL_E3 = ZeroMaskingLayer.ZeroMaskedEntries(name="ZeroMsk3")(MODEL_E3)                
        
        #CONV Layers ...
        #PARAM_nb_filter = 100 
        #PARAM_filter_length = 3 
        MODEL_E1 = Conv1D(nb_filter=PARAM_nb_filter, filter_length=PARAM_filter_length, border_mode='valid', activation='relu') (MODEL_E1) 
        MODEL_E2 = Conv1D(nb_filter=PARAM_nb_filter, filter_length=PARAM_filter_length, border_mode='valid', activation='relu') (MODEL_E2) 
        MODEL_E3 = Conv1D(nb_filter=PARAM_nb_filter, filter_length=PARAM_filter_length, border_mode='valid', activation='relu') (MODEL_E3) 
        
        #Max-pool my brother! do a max-pool !
        MODEL_E1 = (GlobalMaxPooling1D ())(MODEL_E1) 
        MODEL_E2 = (GlobalMaxPooling1D ())(MODEL_E2) 
        MODEL_E3 = (GlobalMaxPooling1D ())(MODEL_E3) 
        
        #Merge
        MODEL_MERGE = merge([MODEL_E1, MODEL_E2, MODEL_E3], mode='concat', concat_axis=-1)
        
        #Dense
        MODEL_DENSE_1 = Dense(output_dim=PARAM_DD, activation='sigmoid')(MODEL_MERGE)
        MODEL_DROP_1  = Dropout(0.5)(MODEL_DENSE_1) 

        if self.Configs["ClassificationType"] == "binary":
            MODEL_OUTPUT  = Dense(1, init='uniform', activation='sigmoid' , name="y_vector")(MODEL_DROP_1)
        else:
            NumberOfClassesInMultiClassification = len (self.Configs["OneHotEncodingForMultiClass"])
            MODEL_OUTPUT  = Dense(NumberOfClassesInMultiClassification, activation='softmax' , name="y_vector")(MODEL_DROP_1)
            
        self.model = Model(input=[MODEL_INPUT_SDP_W, MODEL_INPUT_SDP_P, MODEL_INPUT_SDP_D], output=[MODEL_OUTPUT]); 
        return self.model , self.WhichFeaturesToUse , self.WhichOutputsToPredit;

    def BuildArchitecture_SimpleCNN_WPD_EF (self,POSE_dim, DTE_dim, PARAM_nb_filter,PARAM_filter_length,PARAM_DD):
        #<<<CRITICAL>>> : Setting np random seed everytime BEFORE IMPORTING FROM KERAS!
        self.lp ("Building Neural Network Model. RandomSeed:" + str(self.RandomSeed) + "  , Please wait ..."); 
        import numpy as np ; 
        np.random.seed (self.RandomSeed) ; 
        from keras.models import Model ; 
        from keras.layers import Input, Embedding, Dense, Dropout, merge , Conv1D 
        from KerasHelpers import ZeroMaskingLayer;
        from keras.layers.pooling import GlobalMaxPooling1D 
        #END OF <<<CRITICAL>>>
        
        self.Reset_WhichFeatureToUse(); 
        self.WhichFeaturesToUse["PairEntityFeatures"]           =True; 
        self.WhichFeaturesToUse["Forward_SDP_WordEmbeddings"]   =True;
        self.WhichFeaturesToUse["Forward_SDP_PosTagEmbeddings"] =True;
        self.WhichFeaturesToUse["Forward_SDP_DTEmbeddings"]     =True; 
        self.WhichOutputsToPredit["y_vector"]                   =True; 
        
        max_features      = self.wv.vectors.shape[0]
        wv_embedding_size = self.wv.vectors.shape[1]

        #Inputs        
        MODEL_INPUT_SDP_W = Input (shape=(self.TD["Forward_SDP_WordEmbeddings"].shape[1],)  , dtype='int32' , name="Forward_SDP_WordEmbeddings"); 
        MODEL_INPUT_SDP_P = Input (shape=(self.TD["Forward_SDP_PosTagEmbeddings"].shape[1],), dtype='int32' , name="Forward_SDP_PosTagEmbeddings"); 
        MODEL_INPUT_SDP_D = Input (shape=(self.TD["Forward_SDP_DTEmbeddings"].shape[1],)    , dtype='int32' , name="Forward_SDP_DTEmbeddings" ); 
        MODEL_INPUT_EP    = Input (shape=(self.TD["PairEntityFeatures"].shape[1],)          , name="PairEntityFeatures"); 
        
        #Embeddings
        MODEL_E1 = Embedding(input_dim = max_features , output_dim = wv_embedding_size , input_length=self.TD["Forward_SDP_WordEmbeddings"].shape[1]   , weights=[self.wv.vectors], mask_zero=True , trainable=True)(MODEL_INPUT_SDP_W); 
        MODEL_E2 = Embedding(input_dim = self.POSEmb_VocabSize , output_dim = POSE_dim , input_length=self.TD["Forward_SDP_PosTagEmbeddings"].shape[1] , init='uniform'           , mask_zero=True , trainable=True)(MODEL_INPUT_SDP_P);
        MODEL_E3 = Embedding(input_dim = self.DTEmb_VocabSize  , output_dim = DTE_dim  , input_length=self.TD["Forward_SDP_DTEmbeddings"].shape[1]     , init='uniform'           , mask_zero=True , trainable=True)(MODEL_INPUT_SDP_D);
        
        #ZeroMasking:
        MODEL_E1 = ZeroMaskingLayer.ZeroMaskedEntries(name="ZeroMsk1")(MODEL_E1)                
        MODEL_E2 = ZeroMaskingLayer.ZeroMaskedEntries(name="ZeroMsk2")(MODEL_E2)                
        MODEL_E3 = ZeroMaskingLayer.ZeroMaskedEntries(name="ZeroMsk3")(MODEL_E3)                
        
        #CONV Layers ...
        #PARAM_nb_filter = 100 
        #PARAM_filter_length = 3 
        MODEL_E1 = Conv1D(nb_filter=PARAM_nb_filter, filter_length=PARAM_filter_length, border_mode='valid', activation='relu') (MODEL_E1) 
        MODEL_E2 = Conv1D(nb_filter=PARAM_nb_filter, filter_length=PARAM_filter_length, border_mode='valid', activation='relu') (MODEL_E2) 
        MODEL_E3 = Conv1D(nb_filter=PARAM_nb_filter, filter_length=PARAM_filter_length, border_mode='valid', activation='relu') (MODEL_E3) 
        
        #Max-pool my brother! do a max-pool !
        MODEL_E1 = (GlobalMaxPooling1D ())(MODEL_E1) 
        MODEL_E2 = (GlobalMaxPooling1D ())(MODEL_E2) 
        MODEL_E3 = (GlobalMaxPooling1D ())(MODEL_E3) 
        
        #Merge
        MODEL_MERGE = merge([MODEL_E1, MODEL_E2, MODEL_E3, MODEL_INPUT_EP], mode='concat', concat_axis=-1)
        
        #Dense
        MODEL_DENSE_1 = Dense(output_dim=PARAM_DD, activation='sigmoid')(MODEL_MERGE)
        MODEL_DROP_1  = Dropout(0.5)(MODEL_DENSE_1) 

        if self.Configs["ClassificationType"] == "binary":
            MODEL_OUTPUT  = Dense(1, init='uniform', activation='sigmoid' , name="y_vector")(MODEL_DROP_1)
        else:
            NumberOfClassesInMultiClassification = len (self.Configs["OneHotEncodingForMultiClass"])
            MODEL_OUTPUT  = Dense(NumberOfClassesInMultiClassification, activation='softmax' , name="y_vector")(MODEL_DROP_1)
            
        self.model = Model(input=[MODEL_INPUT_SDP_W, MODEL_INPUT_SDP_P, MODEL_INPUT_SDP_D, MODEL_INPUT_EP], output=[MODEL_OUTPUT]); 
        return self.model , self.WhichFeaturesToUse , self.WhichOutputsToPredit;
