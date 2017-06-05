"""
  Code by: Farrokh Mehryary 
           Turku NLP Group, Department of FT, University of Turku, Finland 
           email: farmeh@utu.fi 
  
  This code requires:
           - python: version 2.7.x
           - keras : version 1.2.0
           - theano: version 0.8.2
  

  You should point out the program to where TEES XML files for BB3 (BB-2016) training, development and test set 
  files are located (either BB3-event or BB3-event+NER files). 
  
  You can run the program in two different modes using the --task argument:
   --task predictDevel  : to train on the given training set file, then predicting given development set file
   --task "predictTest  : to train on the given training+development sets files, predicting given test set file
        
  example input arguments: 
    --task predictTest 
    --trainFile /home/user1/BB_Corpora/BB_EVENT_16_BLLIP-BIO_STANFORD-CONVERT-basic_170207/BB_EVENT_16-train.xml
    --develFile /home/user1/BB_Corpora/BB_EVENT_16_BLLIP-BIO_STANFORD-CONVERT-basic_170207/BB_EVENT_16-devel.xml
    --testFile /home/user1/BB_Corpora/BB_EVENT_16_BLLIP-BIO_STANFORD-CONVERT-basic_170207/BB_EVENT_16-test.xml
    
  You can try different parsing and SD conversion, but we recommend using either -basic or -nonCollapsed SD
  conversion of the BLLIP parses. 
"""
import os , sys , argparse 
from Helpers import RelationExtractionPipeline
from Helpers import GeneralFunctions as GF 
import BB3_AggregateResults as AGGR 

def Exit (MSG):
    print MSG, "\n" , "Halting program!" 
    sys.exit(-1)
    
def Get_DevelPred_REParams (TRAIN_FILE , DEVEL_FILE , TestSetPredictionOutputFolder):
    RE_PARAMS = RelationExtractionPipeline.FLSTM_RE_PARAMS() ;
    RE_PARAMS.TrainingSet_Files_List    = [TRAIN_FILE];
    RE_PARAMS.DevelopmentSet_Files_List = [DEVEL_FILE];
    RE_PARAMS.TestSet_Files_Lists       = [DEVEL_FILE];
    RE_PARAMS.HowManyClassifiers   = 15; 
    RE_PARAMS.NN_MaxNumberOfEpochs = 2 ; 
    RE_PARAMS.NN_Keras_batch_size  = 10;
    RE_PARAMS.PredictTestSet  = True ; 
    RE_PARAMS.EvaluateTestSet = True ; 
    RE_PARAMS.WriteBackTestSetPredictions = True  ; 
    RE_PARAMS.TestSetPredictionOutputFolder = TestSetPredictionOutputFolder; 
    RE_PARAMS.ProcessDevelSetAfterEpochNo = -1 ; #After epoch no X, DevelSet is predicted and evaluated. [Hint: set to -1 to NEVER predict develset]
    RE_PARAMS.ProcessTestSetAfterEpochNo  = 2 ; #After epoch no X, IF needed, Test set is going to be predicted and/or evaluated and/or written-back. [Hint: -1 to Never process EXCEPT the last epoch!]
    RE_PARAMS.TrainingSet_DuplicationRemovalPolicy    = "DISCARD"
    RE_PARAMS.DevelopmentSet_DuplicationRemovalPolicy = "DISCARD" 
    RE_PARAMS.TestSet_DuplicationRemovalPolicy        = "IGNORE"
    return RE_PARAMS ; 

def Get_TestPred_REParams (TRAIN_FILE , DEVEL_FILE , TEST_FILE, TestSetPredictionOutputFolder):
    RE_PARAMS = RelationExtractionPipeline.FLSTM_RE_PARAMS() ;
    RE_PARAMS.TrainingSet_Files_List    = [TRAIN_FILE,DEVEL_FILE];
    RE_PARAMS.DevelopmentSet_Files_List = [DEVEL_FILE];
    RE_PARAMS.TestSet_Files_Lists       = [TEST_FILE];
    RE_PARAMS.HowManyClassifiers   = 15; 
    RE_PARAMS.NN_MaxNumberOfEpochs = 2 ; 
    RE_PARAMS.NN_Keras_batch_size  = 10;
    RE_PARAMS.PredictTestSet  = True ; 
    RE_PARAMS.EvaluateTestSet = False ; 
    RE_PARAMS.WriteBackTestSetPredictions = True  ; 
    RE_PARAMS.TestSetPredictionOutputFolder = TestSetPredictionOutputFolder; 
    RE_PARAMS.ProcessDevelSetAfterEpochNo = -1 ; #After epoch no X, DevelSet is predicted and evaluated. [Hint: set to -1 to NEVER predict develset]
    RE_PARAMS.ProcessTestSetAfterEpochNo  = 2 ; #After epoch no X, IF needed, Test set is going to be predicted and/or evaluated and/or written-back. [Hint: -1 to Never process EXCEPT the last epoch!]
    RE_PARAMS.TrainingSet_DuplicationRemovalPolicy    = "DISCARD"
    RE_PARAMS.DevelopmentSet_DuplicationRemovalPolicy = "DISCARD" 
    RE_PARAMS.TestSet_DuplicationRemovalPolicy        = "IGNORE"
    return RE_PARAMS ; 


def Process_Args (args):
    #Check trainFile
    if not GF.FILE_CheckFileExists (args.trainFile):
        Exit ("invalid trainFile at :" + args.trainFile )

    #Check develFile     
    if not GF.FILE_CheckFileExists (args.develFile):
        Exit ("invalid develFile at :" + args.develFile )
    
    #Check testFile        
    if args.task == "predictTest": 
        if args.testFile == None:
            Exit ("no testfile argument is given. testfile is mandatory when task is predictTest." )

        if not GF.FILE_CheckFileExists (args.testFile):
            Exit ("invalid testFile at :" + args.testFile)
            
    #Handle predictionOutputFolder
    predictionOutputFolder = args.predictionOutputFolder 
    if predictionOutputFolder is None:
        print "No specific predictionOutputFolder is defined." 
        current_dir = os.path.dirname(os.path.realpath(__file__))
        predictionOutputFolder = current_dir + "/prediction_output/" 
        print "predictionOutputFolder is set to:" + predictionOutputFolder 
    try:        
        if GF.OS_IsDirectory (predictionOutputFolder):
            print "deleting directory with all of its contents:" + predictionOutputFolder + " ..." 
            GF.OS_RemoveDirectoryWithContent (predictionOutputFolder)
        print "creating predictionOutputFolder:" + predictionOutputFolder + " ..." 
        GF.OS_MakeDir (predictionOutputFolder, False)
    except:
        Exit ("error in creating predictionOutputFolder at :" + predictionOutputFolder)
    args.predictionOutputFolder = str(predictionOutputFolder)
    if args.predictionOutputFolder[-1]<>"/":
        args.predictionOutputFolder += "/" 


    #Handle aggregationOutputFolder
    aggregationOutputFolder = args.aggregationOutputFolder
    if aggregationOutputFolder is None:
        print "No specific aggregationOutputFolder is defined." 
        current_dir = os.path.dirname(os.path.realpath(__file__))
        aggregationOutputFolder = current_dir + "/aggregation_output/" 
        print "aggregationOutputFolder is set to:" + aggregationOutputFolder 
    try:        
        if GF.OS_IsDirectory (aggregationOutputFolder):
            print "deleting directory with all of its contents:" + aggregationOutputFolder + " ..." 
            GF.OS_RemoveDirectoryWithContent (aggregationOutputFolder)
        print "creating aggregationOutputFolder:" + aggregationOutputFolder + " ..." 
        GF.OS_MakeDir (aggregationOutputFolder, False)
    except:
        Exit ("error in creating aggregationOutputFolder at :" + aggregationOutputFolder)
    args.aggregationOutputFolder = str(aggregationOutputFolder)
    if args.aggregationOutputFolder[-1]<>"/":
        args.aggregationOutputFolder += "/" 

    #logFile     
    if args.logFile == None:
        args.logFile = os.path.dirname(os.path.realpath(__file__)) + "/BB3_event_logFile.log" 
        print "logFile is set to:" + args.logFile 
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bacteria Biotope Relation Extraction Pipeline: BB3-event task.')
    parser.add_argument("--task"                   , help= "Task to perform. Choose from: predictDevel or predictTest" , choices=["predictDevel","predictTest"] , required=True)
    parser.add_argument("--trainFile"              , help= "Address of TEES XML training file."   , required=True)
    parser.add_argument("--develFile"              , help= "Address of TEES XML development file.", required=True)
    parser.add_argument("--testFile"               , help= "Address of TEES XML test file.") 
    parser.add_argument("--predictionOutputFolder" , help= "Address of a folder to put prediction files.") 
    parser.add_argument("--aggregationOutputFolder", help= "Address of a folder to put aggregated prediction files.")
    parser.add_argument("--logFile"                , help= "Address for logfile.")
    args = parser.parse_args()
    
    Process_Args (args) 
    
    current_dir = os.path.dirname(os.path.realpath(__file__)) 
    PARAM_ConfigFileAddress = current_dir + "/BB3_CONFIG_Binary.json" 
    if not GF.FILE_CheckFileExists (PARAM_ConfigFileAddress):
            Exit ("Config file not found:" + PARAM_ConfigFileAddress)
    
    PARAM_LogFileAddress = args.logFile 
    
    ArchitectureName = "BuildArchitecture_SimpleCNN_WPD_EF(200,300,100,4,100)"
    if args.task == "predictDevel":
        RE_PARAMS = Get_DevelPred_REParams (args.trainFile, args.develFile, args.predictionOutputFolder) 
        RE_PARAMS.WriteBackProcessedTestSet_OutputFileAddress = args.predictionOutputFolder + "BB16_PROCESSED_GOLDDEVEL.xml" 
    else:
        RE_PARAMS = Get_TestPred_REParams (args.trainFile, args.develFile, args.testFile, args.predictionOutputFolder) 
        RE_PARAMS.WriteBackProcessedTestSet_OutputFileAddress = args.predictionOutputFolder + "BB16_PROCESSED_GOLDTEST.xml" 
        
    RE_PARAMS.WriteBackProcessedTestSet = True 
    RE_PARAMS.ArchitectureBuilderMethodName = [ArchitectureName]
    Pipeline = RelationExtractionPipeline.FLSTM_RE_Pipeline (ConfigFileAddress = PARAM_ConfigFileAddress ,LogFileAddress = PARAM_LogFileAddress , RE_PARAMS=RE_PARAMS) ; 
    Pipeline.Run(); 
    Pipeline.__exit__ (); 

    GoldTEESXML = RE_PARAMS.WriteBackProcessedTestSet_OutputFileAddress
    PredFolder  = args.predictionOutputFolder  + ArchitectureName + "/" 
    AggrFolder  = args.aggregationOutputFolder + ArchitectureName + "/" 
    AGGR.AggregateFolderIntoFolder (GoldTEESXML, PredFolder, AggrFolder)
    
    """
    """