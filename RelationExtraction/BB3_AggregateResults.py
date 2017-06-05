import sys, gzip 
from xml.etree import cElementTree as ET 

import Helpers.GeneralFunctions   as GE

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


def AggregateResults (GoldTEESXML,PredFileList,EpochFocus,AggeragationFolder,Description):
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
    
    if not GE.OS_IsDirectory (AggeragationFolder):
        GE.OS_MakeDir (AggeragationFolder)
    if AggeragationFolder[-1]<>"/":
        AggeragationFolder+="/" 
            
    #Process GOLD
    GoldTree = LoadTEESFile_GetTreeRoot (GoldTEESXML, True) 
    GoldData = Get_Interaction_Results (GoldTree)
    GoldKeys = sorted(GoldData.keys()) 
    
    print "\nINPUT FILES:" 
    Agg_results = {} 
    for idx , FileAddress in enumerate(PredFileList):
        print idx+1 , "/".join (FileAddress.split("/")[-4:])
        PredTree = LoadTEESFile_GetTreeRoot (FileAddress, True) 
        PredData = Get_Interaction_Results (PredTree)
        assert sorted(PredData.keys ()) == GoldKeys
        for interaction_key in GoldKeys:
            #Create Key in Agg_results dict if not exists
            if not interaction_key in Agg_results:
                Agg_results[interaction_key] = 0 ;
            #update Agg_results dict ...
            Agg_results[interaction_key]+= PredData[interaction_key] 

    print ""
    
    for threshold_level in range(1, len(PredFileList)+1):
        writeback_agg_results = {}
        for interaction_key in GoldKeys:
            if Agg_results[interaction_key] >= threshold_level:
                writeback_agg_results[interaction_key] = 1
            else:
                writeback_agg_results[interaction_key] = 0
        
        gold_tree = cp.deepcopy (GoldTree)
        #remove all parse info
        for sentence_element in gold_tree.findall('.//sentence'):
            for analayses_element in sentence_element.findall("analyses"):
                sentence_element.remove(analayses_element)

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
        print "\nThreshold:" +str(threshold_level), "File: " + PredictedFileAddress 
        LOADSAVE_save_xml(gold_tree, PredictedFileAddress) 
    
def AggregateFolderIntoFolder (GoldTEESXML,PredFolder,AggrFolder):
    print "Running aggregation algorithm ..." 
    print "GoldTEESXML      :"  + GoldTEESXML + "\n"
    print "Prediction Folder:"  + PredFolder  + "\n"
    print "Aggregation Folder:" + AggrFolder  
    print "-" * 80 
    
    for EpochFocus in range(1,20):
        FilesList_ForwardOnly , FilesList_LinComb = [] , [] 
        AllFiles = sorted (GE.GetAllFilesPathAndNameWithExtensionInFolder (PredFolder, "xml"))
        for fileaddr in AllFiles:
            if "_EpochNo" + str(EpochFocus) in fileaddr:
                if fileaddr.split("/")[-1].startswith ("LinComb_"):
                    FilesList_LinComb.append (fileaddr)
                else:
                    FilesList_ForwardOnly.append (fileaddr)
        
        for idx , FocusPredictedFiles in enumerate ([FilesList_ForwardOnly,FilesList_LinComb]):
            if FocusPredictedFiles == []:
                continue ; 
            
            PredTp = "Forward" if idx==0 else "Linear_Combination" 
            Description = "PredType    : " + PredTp + "\n" + \
                          "EpochNo     : " + str(EpochFocus)
            
            AggregateResults (GoldTEESXML,FocusPredictedFiles,EpochFocus,AggrFolder,Description)
