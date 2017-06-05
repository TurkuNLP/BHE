import sys, gzip
import numpy as np 
import sklearn.metrics as METRICS ; 
from xml.etree import cElementTree as ET 

import TEESDocumentHelper as TH
import GeneralFunctions   as GE

def f_round(number, NP=3):
    NP = str(NP)
    return ('{:.' + NP + 'f}').format (number)
    
def LoadTEESFile_GetTreeRoot (m_FilePathName , ReturnWholeTree=False):
    try:    
        if m_FilePathName.endswith (".xml"):
            tree = ET.parse(m_FilePathName); 
            if ReturnWholeTree:
                return tree;
            else:
                return tree.getroot (); 
        elif m_FilePathName.endswith (".gz"):
            f = gzip.open (m_FilePathName, "rb"); 
            root = ET.fromstring(f.read ()); 
            f.close ();
            return root ; 
        else:
            raise Exception ("unknown file type:" + m_FilePathName.split(".")[-1]); 
    except Exception as E:
        print "Error occurred:" + E.message ; 
        sys.exit(-1); 

def LOADSAVE_save_xml(tree, out_path):
    if out_path.endswith('.gz'):
        out_f = gzip.open(out_path, 'wb')
        tree.write(out_f)
        out_f.close()
    else:
        tree.write(out_path)

def Get_Interaction_Results (tree):
    RES = {} ;     
    for sentence in tree.findall('.//sentence'):
        for interaction in sentence.findall('interaction'):
            interaction_id = interaction.attrib["id"]; 
            interaction_e1 = interaction.attrib["e1"];   
            interaction_e2 = interaction.attrib["e2"];   
            key = (interaction_id,interaction_e1,interaction_e2)
            interaction_type = 1 if interaction.attrib["type"].lower() == "lives_in" else 0 ; 
            RES[key] = interaction_type ; 
    return RES ; 

    
def Evaluate (y_true, y_pred):
    Precision, Recall, FScore, Support = METRICS.precision_recall_fscore_support (y_true, y_pred);
    COUNTS = METRICS.confusion_matrix (y_true , y_pred); 
    TP = COUNTS[1,1];
    TN = COUNTS[0,0];
    FP = COUNTS[0,1]; 
    FN = COUNTS[1,0];
    RES = { 
      "positive" : {"precision":Precision[1] ,"recall":Recall[1] , "f1-score":FScore[1], "support": Support[1]},
      "negative" : {"precision":Precision[0] ,"recall":Recall[0] , "f1-score":FScore[0], "support": Support[0]},
      "total"    : {"f1-macro": np.mean (FScore) , 
                    "f1-weighted": ((FScore[0]*Support[0])+(FScore[1]*Support[1]))/float(Support[0]+Support[1])
                   } ,
      "TP" : TP ,
      "TN" : TN , 
      "FP" : FP , 
      "FN" : FN ,
     }
    return RES

def CompareWithGold (GoldData, PredictedFileAddress):
    GoldKeys = sorted(GoldData.keys()) 
    y_true = np.array ([GoldData[interaction_id] for interaction_id in GoldKeys] , dtype=np.int16)
    PredData = Get_Interaction_Results (LoadTEESFile_GetTreeRoot (PredictedFileAddress, True))
    assert sorted(PredData.keys ()) == GoldKeys
    y_pred = [] 
    for interaction_key in GoldKeys:
        y_pred.append (PredData[interaction_key])
    y_pred = np.array (y_pred , dtype=np.int16)
    EvaluationResult = Evaluate (y_true, y_pred) 
    return EvaluationResult 
    

def AggregateResults (GoldTEESXML,PredFileList,EpochFocus,AggeragationFolder,Description, ShouldWriteBackAggregation):
    import copy as cp ; 
    print "-"*80
    print Description
    print GoldTEESXML
    print "-"*20 
    for idx , fileaddr in enumerate (PredFileList):
        #print idx+1 , fileaddr
        assert "EpochNo"+ str(EpochFocus)+".xml" in fileaddr
        assert GE.FILE_CheckFileExists (fileaddr) == True
    #print "-"*20 
    assert GE.FILE_CheckFileExists (GoldTEESXML) == True
    
    if ShouldWriteBackAggregation:
        if not GE.OS_IsDirectory (AggeragationFolder):
            GE.OS_MakeDir (AggeragationFolder)
        if AggeragationFolder[-1]<>"/":
            AggeragationFolder+="/" 
            
    #Process GOLD
    GoldTree = LoadTEESFile_GetTreeRoot (GoldTEESXML, True) 
    GoldData = Get_Interaction_Results (GoldTree)
    GoldKeys = sorted(GoldData.keys()) 
    y_true = np.array ([GoldData[interaction_id] for interaction_id in GoldKeys] , dtype=np.int16)
    
    PredMetric = [] 
    Agg_results = {} 
    for FileAddress in PredFileList:
        print "/".join (FileAddress.split("/")[-4:])
        PredTree = LoadTEESFile_GetTreeRoot (FileAddress, True) 
        PredData = Get_Interaction_Results (PredTree)
        assert sorted(PredData.keys ()) == GoldKeys
        y_pred = [] 
        for interaction_key in GoldKeys:
            y_pred.append (PredData[interaction_key])
            #Create Key in Agg_results dict if not exists
            if not interaction_key in Agg_results:
                Agg_results[interaction_key] = 0 ;
            #update Agg_results dict ...
            Agg_results[interaction_key]+= PredData[interaction_key] 
                
        y_pred = np.array (y_pred , dtype=np.int16)
        EvaluationResult = Evaluate (y_true, y_pred) 
        PredMetric.append (EvaluationResult["positive"]["f1-score"]) 
         
    print "-"*20 , "\n" , len(PredFileList) , "MEAN : " , f_round (np.mean (PredMetric)) , "STD: " , f_round (np.std  (PredMetric)) , "\n"
    
    Agg_Thresholds_Evaluation = [] 
    for threshold_level in range(1, len(PredFileList)+1):
        y_pred = [] ;
        for interaction_key in GoldKeys:
            if Agg_results[interaction_key] >= threshold_level:
                y_pred.append (1)
            else:
                y_pred.append (0)
        
        y_pred = np.array (y_pred , dtype=np.int16)
        EvaluationResult = Evaluate (y_true, y_pred) 
        print '{:2d}'.format(threshold_level), f_round (EvaluationResult["positive"]["recall"]), f_round(EvaluationResult["positive"]["precision"]), f_round(EvaluationResult["positive"]["f1-score"]) 
        Agg_Thresholds_Evaluation.append ( (threshold_level, EvaluationResult["positive"]["recall"], EvaluationResult["positive"]["precision"], EvaluationResult["positive"]["f1-score"] )  )
    
    Best_Threshold = sorted (Agg_Thresholds_Evaluation , key = lambda x: x[3] , reverse=True)[0]
    print "\n" , f_round (np.mean (PredMetric)) + "\t" + f_round (np.std  (PredMetric)) + "\t"  + '{:2d}'.format(Best_Threshold[0]) + "\t" + f_round (Best_Threshold[1]) + "\t" + f_round (Best_Threshold[2]) + "\t"+ f_round (Best_Threshold[3]) 
    FINAL_RES_STRING = f_round (np.mean (PredMetric)) + ";" + f_round (np.std  (PredMetric)) + ";"  + '{:2d}'.format(Best_Threshold[0]) + ";" + f_round (Best_Threshold[1]) + ";" + f_round (Best_Threshold[2]) + ";"+ f_round (Best_Threshold[3]) 
    
    if ShouldWriteBackAggregation:
        WRITTEN_Agg_Thresholds_Evaluation = [] 
        for threshold_level in range(1, len(PredFileList)+1):
            writeback_agg_results = {}
            for interaction_key in GoldKeys:
                if Agg_results[interaction_key] >= threshold_level:
                    writeback_agg_results[interaction_key] = 1
                else:
                    writeback_agg_results[interaction_key] = 0
            
            gold_tree = cp.deepcopy (GoldTree)
            for interaction_element in gold_tree.findall (".//interaction"):
                interaction_id = interaction_element.attrib["id"]
                interaction_e1 = interaction_element.attrib["e1"]
                interaction_e2 = interaction_element.attrib["e2"]
                key = (interaction_id,interaction_e1,interaction_e2)
                interaction_type = "Lives_In" if writeback_agg_results[key]==1 else "neg" 
                interaction_element.set('type',interaction_type)
            
            wb_filename = "Aggr_Epoch_" + str(EpochFocus) + "_Threshold_" + str(threshold_level) + "_" ;
            if PredFileList[0].split("/")[-1].startswith ("LinComb"):
                wb_filename+= "LinComb"
            else:
                wb_filename+= "Forward"
            wb_filename+= ".xml" 
            PredictedFileAddress = AggeragationFolder + wb_filename
            LOADSAVE_save_xml(gold_tree, PredictedFileAddress) 
            EvaluationResult = CompareWithGold (GoldData, PredictedFileAddress)
            WRITTEN_Agg_Thresholds_Evaluation.append ( (threshold_level, EvaluationResult["positive"]["recall"], EvaluationResult["positive"]["precision"], EvaluationResult["positive"]["f1-score"] )  )            
            print PredictedFileAddress, "    " , '{:2d}'.format(threshold_level), f_round (EvaluationResult["positive"]["recall"]), f_round(EvaluationResult["positive"]["precision"]), f_round(EvaluationResult["positive"]["f1-score"]) 
        assert Agg_Thresholds_Evaluation == WRITTEN_Agg_Thresholds_Evaluation        
    #import pdb ; pdb.set_trace()
    return FINAL_RES_STRING       