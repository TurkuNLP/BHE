import BB_Shared ; 

import sys, shutil 
sys.path.append("/home/farmeh/Desktop/PROJECTS/GIT/FLSTM/CODE")

from Helpers import RelationExtractionPipeline; 

BB3EVENTNER_Corpus = {
 "ParseTypes":{
             "basic":{
                "Train" : "",
                "Devel" : "",
                "Test"  : "",
             },

             "nonCollapsed":{
                "Train" : "BB16EN-nonCollapsed-train.xml",
                "Devel" : "BB16EN-nonCollapsed-devel.xml",
                "Test"  : "BB16EN-nonCollapsed-test.xml",
             },
             
             "CCProcessed":{
                "Train" : "BB16EN-CCprocessed-train.xml",
                "Devel" : "BB16EN-CCprocessed-devel.xml",
                "Test"  : "BB16EN-CCprocessed-test.xml",
             }
 }
}

def Get_DevelPred_REParams (TRAIN_FILE , DEVEL_FILE , TEST_FILE):
    RE_PARAMS = RelationExtractionPipeline.FLSTM_RE_PARAMS() ; 
    RE_PARAMS.TrainingSet_Files_List    = [TRAIN_FILE];
    RE_PARAMS.DevelopmentSet_Files_List = [DEVEL_FILE];
    RE_PARAMS.TestSet_Files_Lists       = [TEST_FILE];
    RE_PARAMS.HowManyClassifiers = 15 ; 
    RE_PARAMS.NN_MaxNumberOfEpochs = 10; 
    RE_PARAMS.NN_Keras_batch_size = 10;
    RE_PARAMS.PredictTestSet  = True ; 
    RE_PARAMS.EvaluateTestSet = True ; 
    RE_PARAMS.WriteBackTestSetPredictions = True  ; 
    RE_PARAMS.TestSetPredictionOutputFolder = None; 
    RE_PARAMS.ProcessDevelSetAfterEpochNo = -1 ; #After epoch no X, DevelSet is predicted and evaluated. [Hint: set to -1 to NEVER predict develset]
    RE_PARAMS.ProcessTestSetAfterEpochNo  = 1 ; #After epoch no X, IF needed, Test set is going to be predicted and/or evaluated and/or written-back. [Hint: -1 to Never process EXCEPT the last epoch!]

    RE_PARAMS.TrainingSet_DuplicationRemovalPolicy = "DISCARD"
    RE_PARAMS.DevelopmentSet_DuplicationRemovalPolicy = "DISCARD" 
    RE_PARAMS.TestSet_DuplicationRemovalPolicy = "IGNORE"
    
    return RE_PARAMS ; 

def Get_TestPred_REParams (TRAIN_FILE , DEVEL_FILE , TEST_FILE):
    RE_PARAMS = RelationExtractionPipeline.FLSTM_RE_PARAMS() ; 
    RE_PARAMS.TrainingSet_Files_List    = [TRAIN_FILE,DEVEL_FILE];
    RE_PARAMS.DevelopmentSet_Files_List = [DEVEL_FILE];
    RE_PARAMS.TestSet_Files_Lists       = [TEST_FILE];
    RE_PARAMS.HowManyClassifiers = 15 ; 
    RE_PARAMS.NN_MaxNumberOfEpochs = 5; 
    RE_PARAMS.NN_Keras_batch_size = 10;
    RE_PARAMS.PredictTestSet  = True ; 
    RE_PARAMS.EvaluateTestSet = False ; 
    RE_PARAMS.WriteBackTestSetPredictions = True  ; 
    RE_PARAMS.TestSetPredictionOutputFolder = None; 
    RE_PARAMS.ProcessDevelSetAfterEpochNo = -1 ; #After epoch no X, DevelSet is predicted and evaluated. [Hint: set to -1 to NEVER predict develset]
    RE_PARAMS.ProcessTestSetAfterEpochNo  = 1  ; #After epoch no X, IF needed, Test set is going to be predicted and/or evaluated and/or written-back. [Hint: -1 to Never process EXCEPT the last epoch!]

    RE_PARAMS.TrainingSet_DuplicationRemovalPolicy = "DISCARD"
    RE_PARAMS.DevelopmentSet_DuplicationRemovalPolicy = "DISCARD" 
    RE_PARAMS.TestSet_DuplicationRemovalPolicy = "IGNORE"
    return RE_PARAMS ; 

def OS_MakeDir (FolderAddress):
    if not shutil.os.path.exists(FolderAddress):
        shutil.os.makedirs(FolderAddress)

def CreatePredictionFolders (MainFolder):
    for parse_type in BB3EVENTNER_Corpus["ParseTypes"]:
        OS_MakeDir (MainFolder+parse_type)
        OS_MakeDir (MainFolder+parse_type+"/DEVEL_Preds")
        OS_MakeDir (MainFolder+parse_type+"/DEVEL_Aggregated")
        OS_MakeDir (MainFolder+parse_type+"/TEST_Preds")
        OS_MakeDir (MainFolder+parse_type+"/TEST_Aggregated")
        
if __name__ == "__main__":
    MAIN_IN_FOLDER  = "/home/farmeh/Desktop/DATASETS/BioNLP/BB3_EVEN_NER/BB16EN-gold/" 
    MAIN_OUT_FOLDER = "/home/farmeh/Desktop/PROJECTS/GIT/FLSTM/PROJECTS/BB3_event_NER/" 
    
    PARAM_ConfigFileAddress = MAIN_OUT_FOLDER + "BB3_CONFIG_Binary.json" 
    PARAM_LogFileFolder     = MAIN_OUT_FOLDER + "ZLOGS/"  
    
    CreatePredictionFolders(MAIN_OUT_FOLDER) 
    
    #"basic" , "nonCollapsed", "CCProcessed"
        
    ConsiderParseTypes    = ["nonCollapsed"]
    ConsiderArchitectures = ["BuildArchitecture_SimpleCNN_WPD_EF (200, 300, 100,4,100)"]
                             
    Task = "PRED_TEST" 
    
    SPECIFIC_DEVEL_FILE = None #"/home/farmeh/Desktop/DATASETS/BioNLP/BB3_EVEN_NER/BB16EN-SubOptimal-pred/BB16EN-nonCollapsed-sub-devel-heads.xml" 
    SPECIFIC_TEST_FILE  = "/home/farmeh/Desktop/DATASETS/BioNLP/BB3_EVEN_NER/BB16EN-SubOptimal-pred/BB16EN-nonCollapsed-sub-test-heads.xml" 
    
    for ParseType in ConsiderParseTypes:
        TrainFile  = MAIN_IN_FOLDER + BB3EVENTNER_Corpus["ParseTypes"][ParseType]["Train"]
        DevelFile  = MAIN_IN_FOLDER + BB3EVENTNER_Corpus["ParseTypes"][ParseType]["Devel"]
        TestFile   = MAIN_IN_FOLDER + BB3EVENTNER_Corpus["ParseTypes"][ParseType]["Test"]

        if SPECIFIC_DEVEL_FILE <> None:
            DevelFile  = SPECIFIC_DEVEL_FILE 
        
        if SPECIFIC_TEST_FILE <> None:
            TestFile   = SPECIFIC_TEST_FILE
            
        if Task == "PRED_DEVEL":        
            PredFolder =  MAIN_OUT_FOLDER + ParseType + "/DEVEL_Preds"
            PARAM_LogFileAddress = PARAM_LogFileFolder + "BB_16_DEVELPred_Binary_" + ParseType  + ".log" 
            RE_PARAMS  = Get_DevelPred_REParams (TrainFile,DevelFile,DevelFile) 
            RE_PARAMS.TestSetPredictionOutputFolder = PredFolder 
            RE_PARAMS.WriteBackProcessedTestSet = True 
            RE_PARAMS.WriteBackProcessedTestSet_OutputFileAddress = PredFolder + "/" + "BB16_GOLDDEVEL.xml" 
            
            #Architecture-Specific:             
            RE_PARAMS.NN_MaxNumberOfEpochs = 3; 
            RE_PARAMS.PredictTestSet  = True ; 
            RE_PARAMS.EvaluateTestSet = False; 
            RE_PARAMS.ProcessDevelSetAfterEpochNo = -1 ; #After epoch no X, DevelSet is predicted and evaluated. [Hint: set to -1 to NEVER predict develset]
            RE_PARAMS.ProcessTestSetAfterEpochNo  = 1  ; #After epoch no X, IF needed, Test set is going to be predicted and/or evaluated and/or written-back. [Hint: -1 to Never process EXCEPT the last epoch!]

        else:
            PredFolder =  MAIN_OUT_FOLDER + ParseType + "/TEST_Preds"
            PARAM_LogFileAddress = PARAM_LogFileFolder + "BB_16_TESTPred_Binary_" + ParseType  + ".log" 
            RE_PARAMS  = Get_TestPred_REParams (TrainFile,DevelFile,TestFile) 
            RE_PARAMS.TestSetPredictionOutputFolder = PredFolder 
            RE_PARAMS.WriteBackProcessedTestSet = True 
            RE_PARAMS.WriteBackProcessedTestSet_OutputFileAddress = PredFolder + "/" + "BB16_TEST.xml" 

            RE_PARAMS.NN_MaxNumberOfEpochs = 3
            RE_PARAMS.ProcessTestSetAfterEpochNo  = 2  ;

        RE_PARAMS.ArchitectureBuilderMethodName = ConsiderArchitectures ; 
        
        Pipeline = RelationExtractionPipeline.FLSTM_RE_Pipeline (
            ConfigFileAddress = PARAM_ConfigFileAddress ,
            LogFileAddress    = PARAM_LogFileAddress    , 
            RE_PARAMS         = RE_PARAMS) ; 
        Pipeline.Run(); 
        Pipeline.__exit__ (); 
  

