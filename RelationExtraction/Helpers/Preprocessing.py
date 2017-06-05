import networkx as nx ; 
import xml.etree.cElementTree as et   ; 
import copy 
from itertools import product , combinations, combinations_with_replacement
import SharedVariables as PRJ_SharedVariables ; 
#import TEESDocumentHelper ; 
            
class FLSTM_Preprocessor:
    def __init__(self, lp , PROGRAM_Halt , Configs , wv):
        self.lp = lp ; 
        self.PROGRAM_Halt = PROGRAM_Halt ;
        self.Configs = Configs ; 
        self.wv = wv ; 
        self.NotFoundPOSTags = set() ; 
        self.NotFoundDTTags_Mapped = set(); 
        self.NotFoundDTTags_NotMapped = set(); 
        
    def LoadTEESFile_GetTreeRoot (self,m_FilePathName):
        self.lp (["Loading TEES file from address and getting Root:" , m_FilePathName])
        try:    
            if m_FilePathName.endswith (".xml"):
                tree = et.parse(m_FilePathName); 
                root = tree.getroot (); 
                self.lp ("sucessfully loaded and Root retrieved.")
                return root ; 
            elif m_FilePathName.endswith (".gz"):
                import gzip ; 
                f = gzip.open (m_FilePathName, "rb"); 
                root = et.fromstring(f.read ()); 
                f.close ();
                self.lp ("sucessfully loaded and Root retrieved.")
                return root ; 
            else:
                raise Exception ("unknown file type:" + m_FilePathName.split(".")[-1]); 
        except Exception as E:
            self.PROGRAM_Halt ("Error occurred:" + E.message);


    def HasPotentialInteraction (self, sentence_element):
        promissing_entities = [e.attrib for e in sentence_element.findall(".//entity") if e.attrib["type"].lower() in self.Configs["ValidEnityTypesForRelations"]]                        
                                
        if len(promissing_entities)==0:
            return False ; 
        
        elif len(promissing_entities) == 1:
            #let's check if this only entity can interact with itself 
            this_entity_tp = promissing_entities[0]["type"].lower()
            if not (this_entity_tp in self.Configs["SelfInteractingEntities"]):
                return False ;  

        all_existing_entity_types = set ([e["type"].lower() for e in promissing_entities])
    
        #for example [bacteria-habitat],[bacteria,geographical], 
        #then at least one pair should exist in all types. 
        #but if we have only habitat and geographical entities, then there is no negative!
        for type1,type2 in self.Configs["ListOf_ValidInteractingPairEntityTypes"]:
            if (type1 in all_existing_entity_types) and (type2 in all_existing_entity_types):
                return True ; 
        
        return False ; 
        
    def ProcessRoot (self, Root, DuplicationRemovalPolicy):
        if (Root == None):
            self.PROGRAM_Halt ("Root is None"); 
        
        if DuplicationRemovalPolicy <> None:
            self.lp (["-"*80, "-"*80 , "-"*80 , "[WARNING]: FILE-SPECIFIC Duplication Removal Policy: " + DuplicationRemovalPolicy , "-"*80, "-"*80 , "-"*80])
        else:
            self.lp (["*"*80, "*"*80 , "*"*80 , "[WARNING]: NO FILE-SPECIFIC Duplication Removal Policy" , "*"*80, "*"*80 , "*"*80])
            
        LOCAL_DocumentCount = len (Root.findall (".//document"));
        if LOCAL_DocumentCount == 0:
            self.PROGRAM_Halt ("No document element found in the root."); 
        
        #Critical ... in which element in XMLTree interactions are defined ...
        LOCAL_InteractionElementName = self.Configs["InteractionElementName"] ; 
        #Critical ... in which attribute of the interaction element, class type is given ...
        LOCAL_InteractionElementClassAttributeName = self.Configs["InteractionElementClassAttributeName"] ; 

        #1-Gathering Corpus info:
        LOCAL_TotalCorpusRootAnalysisResult = {
            "NumberOfDocuments"                   : LOCAL_DocumentCount ,
            "Number_Of_Sentences"                 : 0 , 
            "Number_Of_Sentences_WithInteraction" : 0 , 
            "Number_Of_Sentences_WithoutInteraction": 0 , 
            "Documents_Sentences_Distribution" : [] , 
            "Interaction_Types" : {} , 
        }
        
        for document_element in Root.findall (".//document"):
            sentence_w_ineraction = 0   ;
            sentence_wo_interaction = 0 ; 
            for sentence_element in document_element.findall (".//sentence"):
                if (len(sentence_element.findall (".//" + LOCAL_InteractionElementName)) > 0):
                    sentence_w_ineraction += 1 ;
                else:
                    sentence_wo_interaction += 1 ; 
                
                for interaction_element in sentence_element.findall (".//" + LOCAL_InteractionElementName):
                    interaction_tp = interaction_element.attrib[LOCAL_InteractionElementClassAttributeName].lower(); 
                    if interaction_tp in LOCAL_TotalCorpusRootAnalysisResult["Interaction_Types"]:
                        LOCAL_TotalCorpusRootAnalysisResult["Interaction_Types"][interaction_tp] += 1 ;
                    else:
                        LOCAL_TotalCorpusRootAnalysisResult["Interaction_Types"][interaction_tp] = 1  ;
                        
            LOCAL_TotalCorpusRootAnalysisResult["Documents_Sentences_Distribution"].append ((sentence_w_ineraction, sentence_wo_interaction));
        
        LOCAL_TotalCorpusRootAnalysisResult["Number_Of_Sentences"] = sum([a+b for (a,b) in LOCAL_TotalCorpusRootAnalysisResult["Documents_Sentences_Distribution"]])
        LOCAL_TotalCorpusRootAnalysisResult["Number_Of_Sentences_WithInteraction"]    = sum ([a for (a,b) in LOCAL_TotalCorpusRootAnalysisResult["Documents_Sentences_Distribution"]])
        LOCAL_TotalCorpusRootAnalysisResult["Number_Of_Sentences_WithoutInteraction"] = sum ([b for (a,b) in LOCAL_TotalCorpusRootAnalysisResult["Documents_Sentences_Distribution"]])
        
        LP = ["PROCESSING ROOT:" , "-"*40 , \
              "BASIC Document Statistics:" , "-"*20 , \
              "NumberOfDocuments                     :" + str(LOCAL_TotalCorpusRootAnalysisResult["NumberOfDocuments"]) , \
              "Number_Of_Sentences                   :" + str(LOCAL_TotalCorpusRootAnalysisResult["Number_Of_Sentences"]),\
              "Number_Of_Sentences_WithInteraction   :" + str(LOCAL_TotalCorpusRootAnalysisResult["Number_Of_Sentences_WithInteraction"]) , \
              "Number_Of_Sentences_WithoutInteraction:" + str(LOCAL_TotalCorpusRootAnalysisResult["Number_Of_Sentences_WithoutInteraction"]), "" ,\
              "Documents_Sentences_Distribution - Sorted based on Sentences with interaction descendingly " , "-" , \
              str(sorted (LOCAL_TotalCorpusRootAnalysisResult["Documents_Sentences_Distribution"] , key = lambda a:a[0] , reverse=True)) , "" ,\
              "Interaction_Types (Including any cross-sentences or invalid interactions):","-"*10];
        for _tempkey in sorted(list(LOCAL_TotalCorpusRootAnalysisResult["Interaction_Types"].keys())):
            LP.append ("\t" + _tempkey + ":" + str(LOCAL_TotalCorpusRootAnalysisResult["Interaction_Types"][_tempkey]));
        LP.append ("-"*20); 
        self.lp (LP); 
        
        #2-Checking interaction types:         
        self.lp  ("Checking compatibility of relation types between given TEES file and config file ...") ; 

        LOCAL_AllInteractionTypesInXML = set (i.lower() for i in LOCAL_TotalCorpusRootAnalysisResult["Interaction_Types"].keys()) ; 
        LOCAL_AllValidInteractionTypesInConfigFile = self.Configs["CLASSES"]["Negative"] | self.Configs["CLASSES"]["Positive"] ; 
        DIFF = LOCAL_AllInteractionTypesInXML.difference (LOCAL_AllValidInteractionTypesInConfigFile) ; 
        if len(DIFF) <> 0:
            self.PROGRAM_Halt ("Unknown interaction type in TEES file which is not defined in config:" + str(DIFF)) ; 

        DIFF = LOCAL_AllValidInteractionTypesInConfigFile.difference (LOCAL_AllInteractionTypesInXML); 
        if len(DIFF) <> 0:
            if self.Configs["ExecutionParameters"]["DoNotAskAnyQuestions"] == False:
                MSG = ["-"*30,"-"*30 , "WARNING:", "-"*8 , "These interaction types are found inside the Config file but the TEES file does not include any such." , "------>" , str(DIFF)] ; 
                MSG.append ("<<<CRITICAL>>> WARNING: IF YOU ARE DOING MULTICLASS CLASSIFICATION, THERE WILL BE CORRESPONDING COLUMN(s) in <<<y_vector>>> for this (these)!!!") ;
                MSG.append ("SHOULD CONTINUE ? (Y/N)")
                self.lp (MSG); 
                res = raw_input("").lower() ; 
                while not res in ["y" , "n"]:
                    res = raw_input("").lower() ; 
                    self.lp (MSG) ;
                if res == "n":
                    self.PROGRAM_Halt ("Halting program requested.")
                else:
                    self.lp ("CONTINUEING AS REQUESTED ....")
            else:
                MSG = ["-"*30,"-"*30 , "<<<CRITICAL>>><<<WARNING>>>:", "-"*8 , "These interaction types are found inside the Config file but the TEES file does not include any such." , "------>" , str(DIFF)] ; 
                MSG.append ("<<<WARNING>>>: IF YOU ARE DOING MULTICLASS CLASSIFICATION, THERE WILL BE CORRESPONDING COLUMN(s) in <<<y_vector>>> for this (these)!!!") ;
                self.lp (MSG); 
                
        #Moved to the end of function, because we delete some sentences from the tree ... 
        #  TEESXMLHelper = TEESDocumentHelper.FLSTM_TEESXMLHelper (self.Configs , self.lp , self.PROGRAM_Halt) ; 
        #  TEESXMLHelper.TREEOPERATION_CheckIfAllPossibleRelationsExist (Root); 
        
        #3- Checking if short sentences should be removed from corpus ...
        LOCAL_MAX_SENTENCE_LENGTH = 100000000000 ; #Set to a very big number ...
        if self.Configs["ExampleGeneration"]["MAX_SENTENCE_LENGTH"]>0:
            LOCAL_MAX_SENTENCE_LENGTH =self.Configs["ExampleGeneration"]["MAX_SENTENCE_LENGTH"] 
            if self.Configs["ExecutionParameters"]["DoNotAskAnyQuestions"] == False:
                MSG = ["-"*30,"-"*30 , "<<<CRITICAL>>> [WARNING]:", "-"*8 , "According to config file, all sentences longer than " + str(LOCAL_MAX_SENTENCE_LENGTH) + " will be eliminated from this corpus!" , "SHOULD CONTINUE ? (Y/N)"] ; 
                self.lp (MSG); 
                res = raw_input("").lower() ; 
                while not res in ["y" , "n"]:
                    res = raw_input("").lower() ; 
                    self.lp (MSG) ;
                if res == "n":
                    self.PROGRAM_Halt ("Halting program requested.");
                else:
                    self.lp (["","","",""," ----- CRITICAL WARNING: FILTERING-OUT ALL SENTENCES WITH LENGTH LONGER THAN :" + str (LOCAL_MAX_SENTENCE_LENGTH) + " ------------" , "","","",""]); 
            else:
                MSG = ["-"*30,"-"*30 , "<<<CRITICAL>>> [WARNING]:", "-"*8 , "According to config file, all sentences longer than " + str(LOCAL_MAX_SENTENCE_LENGTH) + " will be eliminated from this corpus!" , "SHOULD CONTINUE ? (Y/N)"] ; 
                                    
        #4- Getting info from file ...
        self.lp (["-"*80, "Getting sentences information from file." , "IMPORTANT: Sentences without interactions will be discarded!" , "-"*80]);
        Sentences = [] ;
        Discarded_Sentences = {"Sentences" : [] , "interaction_types": {}};
        Discarded_Entity_Types = set ([]) ; 
        Discarded_Interactions = [] ; 
        SelfInteractionRelations = [] ;
        Discarded_SelfInteractionRelations = [] ; 
        
        Duplicate_Interactions_Counter = 0 
        CrossSentence_Interactions_Counter = 0 
        
        for document_element in Root.findall (".//document"):
            DOC_ID = document_element.attrib["id"] ; 
            for sentence_element in document_element.findall (".//sentence"):

                HasInteraction = self.HasPotentialInteraction (sentence_element) 
                
                #if sentence_element.attrib["id"]=="BB_EVENT_16.d52.s7":
                #    import pdb ; 
                #    pdb.set_trace()
                #<<<CRITICAL>>> 
                #1-Discard sentences with length bigger than maximum
                if len (sentence_element.attrib["text"]) > LOCAL_MAX_SENTENCE_LENGTH:
                    Discarded_Sentences["Sentences"].append ( (sentence_element.attrib , "MAX_LEN"));
                    for interaction in sentence_element.findall (".//" + LOCAL_InteractionElementName):
                        interaction_tp = interaction.attrib[LOCAL_InteractionElementClassAttributeName].lower();
                        if interaction_tp in Discarded_Sentences["interaction_types"]:
                            Discarded_Sentences["interaction_types"][interaction_tp]+=1 ;
                        else:
                            Discarded_Sentences["interaction_types"][interaction_tp]=1 ;
                    continue; 
                
                #<<<CRITICAL>>> 
                #<<<CRITICAL>>>: We first discard sentences without any possible interactions, 
                #                THEN we check for parsing. Because, we don't care about sentences that do not have 
                #                any possible interactions, but we do care if a sentence HAS potential interactions BUT NO PARSING! 
                #2-Should Discard sentences without interactions? Should generate as negatives if there is any potential negative? 
                if sentence_element.find ("./" + LOCAL_InteractionElementName) == None:
                    if self.Configs["ExampleGeneration"]["ActionON_MissingRelations"] <> "GENERATEASNEGATIVES":
                        #Discarded_Sentences["Sentences"].append ( (sentence_element.attrib , "NO INTERACTION - NO NEGATIVE GEN REQUESTED"));
                        continue; #Since no negative generation is requested, and since it has no interaction ---> discard sentence ...
                    
                    else: 
                        #negative generation is requested, hence, let's check if there are any promissing pair of entities exists for 
                        #negative generation. if not, then discard sentence.
                        if not HasInteraction:
                            #Discarded_Sentences["Sentences"].append ( (sentence_element.attrib , "NO ANY TYPE OF POSSIBLE INTERACTION"));
                            continue ; 


                #<<<CRITICAL>>> 
                #3-Discard sentences with broken parse IF REQUESTED.
                if self.Configs["RemoveSentenceIfNoParseExists"]:
                    if (sentence_element.find (".//analyses") == None) or \
                       (sentence_element.find (".//analyses/parse") == None) or \
                       ("stanford"  in sentence_element.find (".//analyses/parse").attrib and sentence_element.find (".//analyses/parse").attrib["stanford"].lower() <> 'ok') or \
                       ("dep-parse" in sentence_element.find (".//analyses/parse").attrib and sentence_element.find (".//analyses/parse").attrib["dep-parse"].lower() <> 'ok') or \
                       (len(sentence_element.findall (".//analyses/parse/dependency")) < 1) :
                           Discarded_Sentences["Sentences"].append ( (sentence_element.attrib , "PARSE"));
                           for interaction in sentence_element.findall (".//" + LOCAL_InteractionElementName):
                               interaction_tp = interaction.attrib[LOCAL_InteractionElementClassAttributeName].lower();
                               if interaction_tp in Discarded_Sentences["interaction_types"]:
                                   Discarded_Sentences["interaction_types"][interaction_tp]+=1 ;
                               else:
                                   Discarded_Sentences["interaction_types"][interaction_tp]=1 ;
                           continue; 

                #3-Getting Sentence Info:
                S = {};
                sentence_attrib = sentence_element.attrib ; 
                S["DOC_ID"]= DOC_ID ; 
                S["ID"]   = sentence_attrib["id"] ; 
                S["TEXT"] = sentence_attrib["text"] ;
    
                #3-1: getting entities:
                Entities_Refs = sentence_element.findall (".//entity"); 
                if len(Entities_Refs)==0:
                    self.PROGRAM_Halt ("Sentence with interaction but no entity:" + str(sentence_attrib)) ; 
                S["ENTITIES"] = {} ; 
                for entity_ref in Entities_Refs:
                    entity_attrib = entity_ref.attrib ; 
                    E_Type = entity_attrib["type"].lower() ; 
                    if not E_Type in self.Configs["ValidEnityTypesForRelations"]:
                        Discarded_Entity_Types.add (E_Type); 
                        continue ; 
    
                        
                    if not "," in entity_attrib["charOffset"]:
                        #for AIMed, HPRD50 , IEPA , LLL:
                        ORIGOFFSETS = [ [int(entity_attrib["charOffset"].split("-")[0]) , int(entity_attrib["charOffset"].split("-")[1] )] ] ; 
                    else:
                        #for BioInfer:
                        #print "ENTITY WITH MORE THAN ONE OFFSET ...." , len(Sentences)
                        ORIGOFFSETS = [] ; 
                        for charoffset in entity_attrib["charOffset"].split(","):
                            ORIGOFFSETS.append ([int(x) for x in charoffset.split("-")]) ; 
                    #try:
                    headOffset = [int (n) for n in entity_attrib["headOffset"].split("-")] ;
                    #except:
                    #    import pdb ; 
                    #    pdb.set_trace () 
                        
                    entity = {
                        "ID"            : entity_attrib["id"], 
                        "CHAROFFSETS"   : headOffset  , #<<<CRITICAL>>> WE ALWAYS USE HEAD OFFSET FOR CHAROFFSET !!!! critical critical critical
                        "HEADOFFSET"    : headOffset  ,
                        "TEXT"          : entity_attrib["text"], 
                        "TYPE"          : E_Type ,
                        "ORIGOFFSETS"   : ORIGOFFSETS 
                    }
                    S["ENTITIES"][entity_attrib["id"]] = entity;
                    
                #3-2: getting pairs (interactions):
                #getting PAIRS AND INTERACTIONS: (For ANTTI STYLE Converted 5PPI)
                S["PAIRS"] = [] ;
                DuplicatePairsRecognition = set() 
                
                for pair_ref in sentence_element.findall ("./" + LOCAL_InteractionElementName):
                    pair_attrib = pair_ref.attrib ; 
                    pair_type = pair_attrib[LOCAL_InteractionElementClassAttributeName].lower() ; 
                    
                    #check entities exist or not
                    e1 , e2 = pair_attrib["e1"] , pair_attrib["e2"] ; 
                    if (not e1 in S["ENTITIES"]) or (not e2 in S["ENTITIES"]):
                        #<<<CRITICAL>>>                                
                        """
                        important comment: 
                        for two different reasons, an interaction might be discarded here.
                        (1): one/both of the interaction entities did not belong to ValidEnityTypesForRelations,
                             so, those entities are not added to S["ENTITIES"], and now the relation should be 
                             discarded itself. 
                        
                        (2): one of the entities of the interaction belongs to other sentences. 
                             hence, it is a cross-sentence interaction which we don't support at the moment.
                        
                        """
                        try: #can we find both Entities in THISSS sentence? If yes, then maybe, problem is their Types ...
                        #,["Bacteria","Geographical"]
                            this_i_e1_tp = sentence_element.find (".//entity[@id='"+e1+"']").attrib["type"].lower() 
                            this_i_e2_tp = sentence_element.find (".//entity[@id='"+e2+"']").attrib["type"].lower() 
                            self.lp (["[WARNING]: DISCARDING interaction because of invalid entity TYPE.",
                                      "id: " + pair_attrib["id"] ,
                                      "e1: " + pair_attrib["e1"] + "  e1_tp:" + this_i_e1_tp, 
                                      "e2: " + pair_attrib["e2"] + "  e2_tp:" + this_i_e2_tp
                                    ])
                            continue ;
                            
                        except: #No! we couldn't find ... so this is a cross sentence!
                            if self.Configs["ExampleGeneration"]["ActionON_CrossSentenceExamples"] == "HALT":
                                self.PROGRAM_Halt ("Corresponding entity for the given interaction is not found:" + str(pair_attrib)) 
                            elif self.Configs["ExampleGeneration"]["ActionON_CrossSentenceExamples"] == "DISCARD":
                                CrossSentence_Interactions_Counter += 1
                                self.lp (["[WARNING]: DISCARDING cross-sentence interaction.", "id: " + pair_attrib["id"] , "e1: " + pair_attrib["e1"] , "e2: " + pair_attrib["e2"]])
                                continue ;
                            else:
                                self.PROGRAM_Halt ("Error in ExampleGeneration/ActionON_CrossSentenceExamples. Check Config File.") 
                    
                    #check if it is a valid relation or should be discared ...
                    if (not [S["ENTITIES"][e1]["TYPE"] , S["ENTITIES"][e2]["TYPE"]] in self.Configs["ListOf_ValidInteractingPairEntityTypes"]) and \
                       (not [S["ENTITIES"][e2]["TYPE"] , S["ENTITIES"][e1]["TYPE"]] in self.Configs["ListOf_ValidInteractingPairEntityTypes"]):
                        Discarded_Interactions.append(pair_attrib); 
                        continue; #Go to next interaction ... this is not okay!
                        
                    #Check if self interacting entity:
                    if e1 == e2:
                        SelfInteractionType = S["ENTITIES"][e1]["TYPE"] ; 
                        if not SelfInteractionType in self.Configs["SelfInteractingEntities"]:
                            Discarded_SelfInteractionRelations.append ((sentence_attrib["id"] , pair_attrib["id"] , SelfInteractionType));
                            continue; 
                        else:
                            SelfInteractionRelations.append ((sentence_attrib["id"] , pair_attrib["id"] , SelfInteractionType)); 
                    
                    #<<<CRITICAL>>>        
                    if pair_type in self.Configs["CLASSES"]["Negative"]:
                        positive=False;
                        class_tp=None ;
                    elif pair_type in self.Configs["CLASSES"]["Positive"]:
                        positive=True;
                        class_tp=pair_type ; 
                    else:
                        self.PROGRAM_Halt ("Unknown class type for interaction:" + pair_type + "\n" + str(pair_attrib)); 
                        
                    pair = {
                        "ID"       : pair_attrib["id"], 
                        "E1"       : e1 , 
                        "E2"       : e2 ,
                        "POSITIVE" : positive, 
                        "CLASS_TP" : class_tp,
                        "GENERATED": False, #this is not an artificial negative ... 
                    };
                    
                    _pair_representation = frozenset([e1,e2,pair_type])
                    if not _pair_representation in DuplicatePairsRecognition:
                        DuplicatePairsRecognition.add(_pair_representation)
                        S["PAIRS"].append (pair); 
                        
                    else:
                        Duplicate_Interactions_Counter += 1 

                        if DuplicationRemovalPolicy == None:
                            #Select Action based on what is specified in the config file 
                            Action = self.Configs["ExampleGeneration"]["ActionON_DuplicateRelations"] 
                        else:
                            #Select Action based on what is wanted. Used for Set-Specific actions. E.g., Discard on training, ignore on test-set
                            Action = DuplicationRemovalPolicy 
                            
                        if Action == "HALT":
                            MSG = "Halt request on Duplicate Relation Dectection:" + "\n" + \
                                  "Document_Id: " + S["DOC_ID"] + "\n" + \
                                  "Sentence_Id: " + S["ID"] + "\n" + \
                                  "Interaction: " + pair_attrib["id"] + "\n" + \
                                  "Duplicate  : " + str(_pair_representation) ; 
                            self.PROGRAM_Halt (MSG)

                        elif Action == "DISCARD":
                            MSG = "DISCARDING Duplicate Relation :" + "\n" + \
                                  "Document_Id: " + S["DOC_ID"] + "\n" + \
                                  "Sentence_Id: " + S["ID"] + "\n" + \
                                  "Interaction: " + pair_attrib["id"] + "\n" + \
                                  "Duplicate  : " + str(_pair_representation) ; 
                            self.lp (MSG)
                        
                        elif Action == "IGNORE":                             
                            MSG = "Ignoring BUT ADDING Duplicate Relation :" + "\n" + \
                                  "Document_Id: " + S["DOC_ID"] + "\n" + \
                                  "Sentence_Id: " + S["ID"] + "\n" + \
                                  "Interaction: " + pair_attrib["id"] + "\n" + \
                                  "Duplicate  : " + str(_pair_representation) ; 
                            self.lp (MSG)
                            S["PAIRS"].append (pair); 
                            
                        else:
                            self.PROGRAM_Halt ("Unknown action for duplicate relation detection:" + Action)
                            
    
                #3-3: getting Tokens
                TOKENS = [] ; 
                for token in sentence_element.findall ("./analyses/tokenization/token"):
                    token_id = token.attrib["id"] 
                    token_charoffset_beg = int(token.attrib["charOffset"].split("-")[0])
                    token_charfofset_end = int(token.attrib["charOffset"].split("-")[1])-1
                    token_text = token.attrib["text"];
                    token_POS  = token.attrib["POS"] ;
                    TOKENS.append ((token_id, token_text, token_POS , (token_charoffset_beg, token_charfofset_end)))
                S["TOKENS_INFO"] = TOKENS ; 
                
                #3-4: getting Parse info 
                PARSE_EDGES = [] ; 
                for parse_edge in sentence_element.findall ("./analyses/parse/dependency"):
                    d_id = parse_edge.attrib["id"];
                    d_t1 = parse_edge.attrib["t1"];
                    d_t2 = parse_edge.attrib["t2"];
                    d_tp = parse_edge.attrib["type"];
                    PARSE_EDGES.append ((d_id, d_t1, d_t2 , d_tp)) ; 
                S["PARSE_EDGES"] = PARSE_EDGES; 
                
                if (len(S["PAIRS"]) > 0) or HasInteraction:
                    Sentences.append (S); 
            
                     
        if len(Discarded_Entity_Types) > 0:
            self.lp (["*"*80,"[INFO]: DISCARDED ENTITIES WITH UNVALID TYPES  :" , "-"*55 , "These are discarded due to Config file." , \
                             str(Discarded_Entity_Types) , "*"*80]) ;
        
        if len(Discarded_Sentences["Sentences"]) > 0:
            self.lp (["*"*80,"[INFO]: DISCARDED SENTENCES THAT HAVE (valid/invalid) RELATIONS:" , "-"*55 , \
                             "Number of discarded sentences:" + str(len(Discarded_Sentences["Sentences"])) , \
                             "Info about relations         :" + str(Discarded_Sentences["interaction_types"]) , \
                             "*"*80, "PRESS ENTER TO CONTINUE" \
                     ]);
                     
            MSG = ["*"*80,"[INFO]: DISCARDED sentences with details:", "-"*20] ; 
            for s_attrib , cause in Discarded_Sentences["Sentences"]:
                MSG.append ( s_attrib["id"] + "\tCause:" + cause );
            MSG.extend (["*"*80 , "PRESS ENTER TO CONTINUE"])    
            self.lp (MSG)    
            
        if len(Discarded_Interactions) > 0:
            MSG = ["*"*80, "[INFO]: DISCARDED RELATIONS DUE TO USING INVALID ENTITY TYPES: " , "-"*55]; 
            MSG.append ("COUNT :" + str(len(Discarded_Interactions))); 
            MSG.append ("-"*20); 
            for i in Discarded_Interactions:
                MSG.append (i); 
            MSG.extend (["*"*80 , "PRESS ENTER TO CONTINUE"])    
            self.lp (MSG) ; 
        
        if len(Discarded_SelfInteractionRelations) >0:
            MSG = ["*"*80,"[INFO]: DISCARDED SELF-INTERACTION RELATIONS DUE NOT ALLOWED IN CONFIG FILE: " , "-"*55]; 
            MSG.append ("COUNT :" + str(len(Discarded_SelfInteractionRelations))); 
            MSG.append ("-"*20); 
            for i in Discarded_SelfInteractionRelations:
                MSG.append (i);
            MSG.extend (["*"*80 , "PRESS ENTER TO CONTINUE"])    
            self.lp (MSG) ; 
            
        if len(SelfInteractionRelations)>0:
            MSG = ["*"*80,"[INFO]: KEPT SELF-INTERACTION RELATIONS DUE:" , "-"*55]; 
            MSG.append ("COUNT :" + str(len(SelfInteractionRelations))); 
            MSG.append ("-"*20); 
            for i in SelfInteractionRelations:
                MSG.append (i);
            MSG.extend (["*"*80 , "PRESS ENTER TO CONTINUE"])    
            self.lp (MSG) ; 
        
        if Duplicate_Interactions_Counter > 0:
            MSG = ["*"*80,"[INFO]: Duplicate Interactions found:" , "-"*55 , "Count of (extra) duplicates found in file:" + str(Duplicate_Interactions_Counter) , "*"*80]
            self.lp (MSG)

        if CrossSentence_Interactions_Counter >0:
            MSG = ["*"*80,"[INFO]: Cross-Sentence Interactions found:" , "-"*55 , "Count of Cross-Sentence Interactions found in file:" + str(CrossSentence_Interactions_Counter) , "*"*80]
            self.lp (MSG)
            
        # I am not sure whether removing discarded sentences from tree is needed anymore or not
        # It was here when I was running 
        #        TEESXMLHelper = TEESDocumentHelper.FLSTM_TEESXMLHelper (self.Configs , self.lp , self.PROGRAM_Halt) ; 
        #        TEESXMLHelper.TREEOPERATION_CheckIfAllPossibleRelationsExist (r); 
        # Hence, I wanted to delete irrelevant sentences before doing sanity check on the tree. 

        if len(Discarded_Sentences) >0:
            #import copy ; 
            #r = copy.deepcopy (Root);
            self.lp ("[INFO]: Removing Discarded Sentences from XML Tree.") ; 
            r = Root ; 
            ID_OF_SENTENCES = [] ; 
            ID_OF_SENTENCES = [s_attrib["id"] for s_attrib , cause in Discarded_Sentences["Sentences"]] ;
            for document_element in r.findall (".//document"):
                for sentence_element in document_element.findall (".//sentence"):
                    if sentence_element.attrib["id"] in ID_OF_SENTENCES:
                        document_element.remove (sentence_element); 
                        
        #<<<CRITICAL>>>
        #<<<CRITICAL>>>
        #import pdb ; 
        #pdb.set_trace()                                
        self.LOWLEVEL_SanityCheckIfAllPossiblePairsExist_GenerateAsNegativesIfRequested (Sentences)

        for st in Sentences:
            assert len(st["PAIRS"])>=0 ; 
            
        return Sentences , LOCAL_TotalCorpusRootAnalysisResult ; 
        
    def LOWLEVEL_SanityCheckIfAllPossiblePairsExist_GenerateAsNegativesIfRequested (self, Sentences):
        if Sentences == []:
            return [];
            
        C_ActionON_MissingRelations              = self.Configs["ExampleGeneration"]["ActionON_MissingRelations"] 
        C_ValidEnityTypesForRelations            = self.Configs["ValidEnityTypesForRelations"]
        C_ListOf_ValidInteractingPairEntityTypes = self.Configs["ListOf_ValidInteractingPairEntityTypes"]
    
        for sentence in Sentences:
            NEGATIVE_ID = 0 
            sentence_id = sentence["ID"]
            entities_by_type = {}
    
            NEW_PAIRS = copy.deepcopy(sentence["PAIRS"]) 
            for p in NEW_PAIRS:
                p["GENERATED"]=False 
                
            #type-checking for entities + building dict of entities_by_type ...        
            for e_id in sentence["ENTITIES"]:
                e_tp = sentence["ENTITIES"][e_id]["TYPE"]
                if not e_tp in C_ValidEnityTypesForRelations:
                    self.PROGRAM_Halt ("Invalid entity type in sentence_id:"+sentence_id+" entity_id:"+e_id+" entity type:"+e_tp) ;
                if e_tp in entities_by_type:
                    entities_by_type[e_tp].append(e_id)
                else:
                    entities_by_type[e_tp]= [e_id]
            
            #getting all interactions in the sentence:
            all_pairs = [] 
            for p in sentence["PAIRS"]:
                all_pairs.append ((p["E1"],p["E2"])) 
            
            #actuall process
            for interacting_entitytype_pair in C_ListOf_ValidInteractingPairEntityTypes:
                type1=interacting_entitytype_pair[0];
                type2=interacting_entitytype_pair[1];
                if (not type1 in entities_by_type) or (not type2 in entities_by_type):
                    #- for example habitat-geographical is valid, but THIS sentence does not have any geographical entitiy. 
                    #- In the case of self-interacting entities, we have type1=type2=x, and if x is not in entities_by_type, there will be no interaction.
                    continue; 
    
                
                Entity_Type1_List = entities_by_type[type1]
                Entity_Type2_List = entities_by_type[type2]
                # If type1 <> type2 (like bacteria and habitat):
                #     It IS ALREADY VERIFIED in previous if that we have at least 1 corresponding entity for each entity, 
                #     because both bacteria and habitate has been seen in entities_by_type. 
                #     hence we should take their product. [b1]*[h1,h2] --> [b1,h1] , [b1,h2]
                #
                # If type 1 == type2:
                #   --> Entity_Type1_List = Entity_Type2_List = ["d1","d2","d3"]
                #   (1) If cannot self-interact, then:
                #       - USE itertools.combinations (["d1","d2","d3"],2)  ---> [('d1', 'd2'), ('d1', 'd3'), ('d2', 'd3')]
                #       - DO NOT USE permutations because itertools.permutations (["d1","d2","d3"],2) --> [('d1', 'd2'), ('d1', 'd3'), ('d2', 'd1'), ('d2', 'd3'), ('d3', 'd1'), ('d3', 'd2')]
                #
                #   (2) If can self-interact, then itertools.combinations_with_replacement (["d1","d2","d3"],2) --> 
                #         [('d1', 'd1'), ('d1', 'd2'), ('d1', 'd3'), ('d2', 'd2'), ('d2', 'd3'), ('d3', 'd3')]
                #
                          
                if type1 <>  type2: #for example, bacteria-habitat--> ALL bacteria-habitat pairs should be in the XML for the sentence
                    PossibleRelations = product (Entity_Type1_List , Entity_Type2_List);
                
                else: # for example, drug-drug: 
                    if not type1 in self.Configs["SelfInteractingEntities"]: # only drug A can interact with drug B. So either (A,B) or (B,A) should be in the XML but not (A,A)
                        PossibleRelations =  combinations (Entity_Type1_List , 2) 
                        # note: if len(Entity_Type1_List)==1 then combinations (["d1"],2)] --> [] which is great! 
    
                    else: #for example, a drug can interact with itself ... (A,A) should be in the file, as well as (A.B) or (B,A)
                        PossibleRelations =  combinations_with_replacement (Entity_Type1_List , 2) 
                        # note: if len(Entity_Type1_List)==1 then combinations_with_replacement (["d1"],2) --> [('d1', 'd1')] which is great! 
    
                for candidate_pair in PossibleRelations:
                    if (not (candidate_pair[0],candidate_pair[1]) in all_pairs) and (not (candidate_pair[1],candidate_pair[0]) in all_pairs):
                        if C_ActionON_MissingRelations <> "GENERATEASNEGATIVES":
                            MSG  = "Necessary relation is missing for sentence:" + sentence_id + "\n" ; 
                            MSG+=  "either " + str ((candidate_pair[0],candidate_pair[1])) + "  or  " + str ((candidate_pair[1],candidate_pair[0])) + "should be in XML.\n" ; 
                            MSG+=  "entity types: (" + type1 + "," + type2 + ")." ; 
                            self.PROGRAM_Halt (MSG); 
                        else:
                            e1_id , e1_tp = (candidate_pair[0], sentence["ENTITIES"][candidate_pair[0]]["TYPE"])
                            e2_id , e2_tp = (candidate_pair[1], sentence["ENTITIES"][candidate_pair[1]]["TYPE"])
                            
                            #<<<CRITICAL>>>
                            if e1_tp == type1: #Always look at config file ... Bacteria-Habitat --> E1:Bac, E2:Hab
                                E1 = {"ID": e1_id , "TP": e1_tp}
                                E2 = {"ID": e2_id , "TP": e2_tp}
                            else:
                                E1 = {"ID": e2_id , "TP": e2_tp}
                                E2 = {"ID": e1_id , "TP": e1_tp}
                            
                            PAIR = {
                                 "ID": sentence_id+".i.ANeg"+str(NEGATIVE_ID),
                                 "E1": E1["ID"],
                                 "E2": E2["ID"],
                                 "POSITIVE" : False, 
                                 "CLASS_TP" : None,
                                 "GENERATED": True,
                            }
    
                            #<<<CRITICAL>>> 
                            NEGATIVE_ID+=1 
                            NEW_PAIRS.append (PAIR)
                            all_pairs.append ((E1["ID"],E2["ID"])) 
                            #END OF <<<CRITICAL>>>
                            
                            MSG = ["Creating artificial negative:" , 
                                   "sentence_id:" + sentence_id,
                                   "ID         :" + PAIR["ID"], 
                                   "E1         :" + E1["ID"] + "\tTYPE:" + E1["TP"], 
                                   "E2         :" + E2["ID"] + "\tTYPE:" + E2["TP"], 
                                   "more info  :" + type1 + "," + type2
                                   ]
                            self.lp(MSG)
            #<<<CRITICAL>>>
            sentence["PAIRS"] = NEW_PAIRS 
        
        
    def BuildBagsOfFeatures (self, Sentences):
        self.lp (["-"*80,"-"*80,"-"*80,"-"*20+"    BUILDING BAGS OF WORDS    "+"-"*30]); 
        for sentence in Sentences:
            # IMPORTANT: There can be some ISOLATED-components (nodes not connected to others) in the graph.
            DependencyParseGraph = self.LOWLEVEL_MakeDependencyParseGraphForOneSentence (sentence) ; 

            for pair in sentence["PAIRS"]:
                #IMPORTANT: MULTI-TOKEN ENTITIES ARE ALREADY RESOLVED TO THEIR SYNTACTIC [HEAD] SINGLE-TOKENS ...
                e1_charoffsets = sentence["ENTITIES"][pair["E1"]]["CHAROFFSETS"] ; 
                e2_charoffsets = sentence["ENTITIES"][pair["E2"]]["CHAROFFSETS"] ; 
                
                #<<<CRITICAL>>> VERY VERY VERY CRITICAL PART OF CODE ... sometimes offsets of the e2 is less than e1. <<<CRITICAL>>>
                if e2_charoffsets[0] < e1_charoffsets[0]:
                    (e1_charoffsets , e2_charoffsets) = (e2_charoffsets , e1_charoffsets) ;
                    
                e1_bgn , e1_end = e1_charoffsets[0] , e1_charoffsets[1]-1 ; #VERYYYYYYYYYYY CRITICAL ... 
                e2_bgn , e2_end = e2_charoffsets[0] , e2_charoffsets[1]-1 ; #VERYYYYYYYYYYYYYY CRITICAL ...
                
                h1_bgn,h1_end = sentence["ENTITIES"][pair["E1"]]["HEADOFFSET"][0] , sentence["ENTITIES"][pair["E1"]]["HEADOFFSET"][1]-1
                h2_bgn,h2_end = sentence["ENTITIES"][pair["E2"]]["HEADOFFSET"][0] , sentence["ENTITIES"][pair["E2"]]["HEADOFFSET"][1]-1
                
                TOKENS_INFO = sentence["TOKENS_INFO"] ; 
                pair["BAGS"] = {
                      "M1_Before"      : self.LOWLEVEL_GetTokensAndPosTags_From_To_CharOffsets (TOKENS_INFO , 0      , e1_end                 , True  , True ) ,
                      "M1_Middle"      : self.LOWLEVEL_GetTokensAndPosTags_From_To_CharOffsets (TOKENS_INFO , e1_bgn , e2_end                 , True  , True ) , 
                      "M1_After"       : self.LOWLEVEL_GetTokensAndPosTags_From_To_CharOffsets (TOKENS_INFO , e2_bgn , len (sentence["TEXT"]) , True  , True ) , 
                      "M2_ForeBetween" : self.LOWLEVEL_GetTokensAndPosTags_From_To_CharOffsets (TOKENS_INFO , 0      , e2_end                 , True  , True ) , 
                      "M2_Between"     : self.LOWLEVEL_GetTokensAndPosTags_From_To_CharOffsets (TOKENS_INFO , e1_bgn , e2_end                 , True  , True ) , 
                      "M2_BetweenAfter": self.LOWLEVEL_GetTokensAndPosTags_From_To_CharOffsets (TOKENS_INFO , e1_bgn , len (sentence["TEXT"]) , True  , True ) , 
                      "FullSentence"   : self.LOWLEVEL_GetTokensAndPosTags_From_To_CharOffsets (TOKENS_INFO , 0      , len (sentence["TEXT"]) , True  , True ) , 
                      #"FullSentenceC"  : self.LOWLEVEL_GetTokensAndPosTags_FullSentenceCoding  (TOKENS_INFO , h1_bgn, h1_end , h2_bgn, h2_end) , 
                               }
                pair["SHORTEST_PATH_F"] = self.LOWLEVEL_GenerateShortestPathFeatures (sentence, pair , DependencyParseGraph , ReverseDirection = False);
                
                if self.Configs["ExampleGeneration"]["Generate_Reversed_SDP_Features"]==True:
                    pair["SHORTEST_PATH_F_REV"] = self.LOWLEVEL_GenerateShortestPathFeatures (sentence, pair , DependencyParseGraph , ReverseDirection = True); 

    def LOWLEVEL_MakeDependencyParseGraphForOneSentence (self, sentence):
        G = nx.MultiDiGraph () ; 
        for token_info in sentence["TOKENS_INFO"]:
            G.add_node (token_info[0] , POS = token_info[2] , TXT = token_info[1]);
        
        for edge_info in sentence["PARSE_EDGES"]:
            G.add_edge (edge_info[1] , edge_info[2] , TYPE= edge_info[-1]);
        return G ; 


    def LOWLEVEL_GetTokensAndPosTags_From_To_CharOffsets (self, TOKENS_INFO , charoff_beg, charoff_end , include_start , include_end):
        T , P = [] , [] ; #Tokens , POSIDX ... 

        if (include_start==True and include_end==True):
            for index , token_info in enumerate(TOKENS_INFO):
                #IsLastToken = (index == (len(TOKENS_INFO)-1)); 
                if (token_info[-1][0] >= charoff_beg) and (token_info[-1][0] <= charoff_end):
                    T.append (token_info[1]);#token itself
                    P.append (self.LOWLEVEL_GetPOSTAG_Coding (token_info[2]));#POS_TAG_IDX 

        elif (include_start==False and include_end==True):
            for index , token_info in enumerate(TOKENS_INFO):
                #IsLastToken = (index == (len(TOKENS_INFO)-1)); 
                if (token_info[-1][0] > charoff_beg) and (token_info[-1][0] <= charoff_end):
                    T.append (token_info[1]);#token itself
                    P.append (self.LOWLEVEL_GetPOSTAG_Coding (token_info[2]));#POS_TAG_IDX 
    
        elif (include_start==True and include_end==False):
            for index , token_info in enumerate(TOKENS_INFO):
                #IsLastToken = (index == (len(TOKENS_INFO)-1)); 
                if (token_info[-1][0] >= charoff_beg) and (token_info[-1][0] < charoff_end):
                    T.append (token_info[1]);#token itself
                    P.append (self.LOWLEVEL_GetPOSTAG_Coding (token_info[2]));#POS_TAG_IDX 
    
        elif (include_start==False and include_end==False):
            for index , token_info in enumerate(TOKENS_INFO):
                #IsLastToken = (index == (len(TOKENS_INFO)-1)); 
                if (token_info[-1][0] > charoff_beg) and (token_info[-1][0] < charoff_end):
                    T.append (token_info[1]);#token itself
                    P.append (self.LOWLEVEL_GetPOSTAG_Coding (token_info[2]));#POS_TAG_IDX 
    
        return T , P ;     

    def LOWLEVEL_GetTokensAndPosTags_FullSentenceCoding (self, TOKENS_INFO , foeh_start, foeh_end , soeh_start , soeh_end):
        #foeh_start  : first occuring entity head start
        #foeh_end    : first occuring entity head end
        #soeh_start  : second occuring entity head start
        #soeh_end    : second occuring entity head end    
        #coding: 1111123333334555555
        T , P , C = [] , [] , [] #Tokens , POSIDX , CODING

        #<<<CRITICAL>>>
        if soeh_start < foeh_start:
            foeh_start , soeh_start = soeh_start , foeh_start
            foeh_end   , soeh_end   = soeh_end   , foeh_end
            
        for index , token_info in enumerate(TOKENS_INFO):
            #IsLastToken = (index == (len(TOKENS_INFO)-1)); 
            T.append (token_info[1]);#token itself
            P.append (self.LOWLEVEL_GetPOSTAG_Coding (token_info[2]));#POS_TAG_IDX 
            token_start = token_info[-1][0]
            token_end   = token_info[-1][1]
            
            if (token_end < foeh_start):
                C.append (1)
            
            elif (token_start == foeh_start) and (token_end == foeh_end):
                C.append (2)

            elif (token_start > foeh_end) and (token_end < soeh_start):
                C.append (3)

            elif (token_start == soeh_start) and (token_end == soeh_end):
                C.append (4)
            
            elif (token_start > soeh_end):
                C.append (5)
        
        assert len(T) == len(C)
        
        return T,P,C

    def LOWLEVEL_GetPOSTAG_Coding (self, PosTag):
        if PosTag in PRJ_SharedVariables.PENN_TB_POS_TAGS:
            return PRJ_SharedVariables.PENN_TB_POS_TAGS[PosTag][0]; 
        else:
            self.NotFoundPOSTags.add (PosTag); 
            return PRJ_SharedVariables.PENN_TB_POS_TAGS["ADDED_OTHER"][0]


    def LOWLEVEL_Get_Stanford_DPTAG_Coding (self, DPTag , Forward_Direction):
        #S = DPTag + "   " + str(Forward_Direction) 
        
        use_direction  = self.Configs["ExampleGeneration"]["Directional_Dependency_Types"]
        use_general_dt = self.Configs["ExampleGeneration"]["Use_General_prep_prepc_conj_DT"]
        
        if use_general_dt:
            DPTag_prefix = DPTag.split ("_")[0] ; 
            if DPTag_prefix in ["prep" , "prepc" , "conj"]:
                DPTag = DPTag_prefix 
        
        if not use_direction:
            DPTag = "R_" + DPTag 
        else:
            if Forward_Direction:
                DPTag = "R_" + DPTag 
            else:
                DPTag = "L_" + DPTag 

        #self.lp (S+ "    >>> " + DPTag) ; 
                
        if DPTag in PRJ_SharedVariables.STANFORD_DEPTP_TAGS:
            return PRJ_SharedVariables.STANFORD_DEPTP_TAGS[DPTag][0]
            
        elif DPTag.split("_")[0] in PRJ_SharedVariables.STANFORD_DEPTP_TAGS:
            self.NotFoundDTTags_Mapped.add (DPTag)
            return PRJ_SharedVariables.STANFORD_DEPTP_TAGS[ DPTag.split("_")[0] ][0] 

        else:
            self.NotFoundDTTags_NotMapped.add (DPTag)
            return PRJ_SharedVariables.STANFORD_DEPTP_TAGS["ADDED_OTHER"][0]
            
    
    def LOWLEVEL_GenerateShortestPathFeatures (self, sentence, pair , DependencyParseGraph , ReverseDirection):
        #Initialization        
        HaltIfNoShortestPath = self.Configs["ExampleGeneration"]["HaltIfNoSDP"] ; 
        wv = self.wv ; 
        G = nx.MultiGraph (DependencyParseGraph); 
        GD = DependencyParseGraph ; 
        SP_FEATURE_WORDS , SP_FEATURE_POSTGS , SP_FEATURE_EDGE_DPTGS = [] , [] , [] ; 
        
        #Function to get HeadTokenID
        def GetHeadTokenID (E_ID):
            H_bgn = sentence["ENTITIES"][E_ID]["HEADOFFSET"][0];
            H_end = sentence["ENTITIES"][E_ID]["HEADOFFSET"][1];
            for token_info in sentence["TOKENS_INFO"]:
                token_bgn = token_info[-1][0];
                token_end = token_info[-1][1];
                if (token_bgn >= H_bgn) and (token_end <= H_end):
                    return token_info[0];
            self.PROGRAM_Halt ("HEAD_TOKEN_ID_NOT_FOUND! SID:" + sentence["ID"] + "\n" + str(pair));
        
        #What Policy should be used to generate SDP:
        #TODO: ADD Functionality to find shortest path from ?
        # For BioNLP ST: always from E1 to E2, and because in BB TEES E1 is always Bacteria and B2 is always LOCATION then no problem! This is what we wanted for paper.
        SDP_DIRECTION = self.Configs["ExampleGeneration"]["SDP_DIRECTION"].lower(); 
        if not SDP_DIRECTION in ["from_e1value_to_e2value" , "from_e2value_to_e1value"]:
            self.PROGRAM_Halt ("SDP_DIRECTION METHOD : " + SDP_DIRECTION + " IS NOT IMPLEMENTED YET!");
            
        if SDP_DIRECTION == "from_e1value_to_e2value":
            E1_ID = pair["E1"]; # ---> i.e, BB_EVENT_16.d34.s0.e3
            E2_ID = pair["E2"];
        elif SDP_DIRECTION == "from_e2value_to_e1value":
            E1_ID = pair["E2"]; # ---> i.e, BB_EVENT_16.d34.s0.e3
            E2_ID = pair["E1"];
        else:
            self.PROGRAM_Halt ("SDP_DIRECTION METHOD : " + SDP_DIRECTION + " IS NOT IMPLEMENTED YET!");
            
        #<<<CRITICAL>>>: Regardless of the policy, ReverseDirection will always generate features in the Reverse Direction!
        if ReverseDirection==True:
            E1_ID , E2_ID = E2_ID , E1_ID #<<<CRITICAL>>>
            
        #Now policy and direction are handled , lets get headtokens and start generating features ... oh lah lah! :D             
        E1_Head_Token_ID = GetHeadTokenID (E1_ID); #---> e.i., bt_14
        E2_Head_Token_ID = GetHeadTokenID (E2_ID);
        
        #assert int(E1_Head_Token_ID.split("_")[-1]) > int(E2_Head_Token_ID.split("_")[-1]) ; 
        
        E1_TYPE = sentence["ENTITIES"][E1_ID]["TYPE"].lower() ; 
        E2_TYPE = sentence["ENTITIES"][E2_ID]["TYPE"].lower() ; 
        
        TOKENS_DICT = {}; 
        for token_info in sentence["TOKENS_INFO"]:
            TOKENS_DICT[token_info[0]] = token_info ; # id --> info ...
        
        
        try:
            SHORTEST_PATH = nx.shortest_path (G, source = E1_Head_Token_ID , target= E2_Head_Token_ID); 
        except:
            self.lp ("[WARNING]: No Shortest-Path for sentence-id: " + str(sentence["ID"]) + "  pair-id: " + str(pair["ID"])); 
            if HaltIfNoShortestPath:
                #print "line 479" ;                 
                #import pdb ; 
                #pdb.set_trace (); 
                self.PROGRAM_Halt ("No Shortest Path !!! - \nsource: " + str(E1_Head_Token_ID)+"\ntarget: "+str(E2_Head_Token_ID));
            else:
                return None ; 
            
        def SpecialTreatmentForTwoEntities (token_id, E_TYPE, SP_FEATURE_WORDS):
            token_TEXT = TOKENS_DICT[token_id][1] ; 
            if not token_TEXT in wv:
                if E_TYPE in self.Configs["ExampleGeneration"]["ReplaceVectorForEntityTypeIfTokenNotFound_Dict"]:
                    REPLACEMENT_TXT = self.Configs["ExampleGeneration"]["ReplaceVectorForEntityTypeIfTokenNotFound_Dict"][E_TYPE];
                    SP_FEATURE_WORDS.append (REPLACEMENT_TXT);
                    self.lp ("REPLACEMENT -------------------- " + token_TEXT + " >>> " + REPLACEMENT_TXT) ; 
                else:
                    SP_FEATURE_WORDS.append (token_TEXT);#add the word itself. Will be mapped to unknown shared vector later!
            else:
                idx=wv[token_TEXT]; 
                if idx >= (wv.max_rank_mem - 1):
                    if E_TYPE in self.Configs["ExampleGeneration"]["ReplaceVectorForEntityTypeIfTokenNotFound_Dict"]:
                        REPLACEMENT_TXT = self.Configs["ExampleGeneration"]["ReplaceVectorForEntityTypeIfTokenNotFound_Dict"][E_TYPE];
                        SP_FEATURE_WORDS.append (REPLACEMENT_TXT);
                        self.lp ("REPLACEMENT -------------------- " + token_TEXT + " >>> " + REPLACEMENT_TXT) ; 
                    else:
                        SP_FEATURE_WORDS.append (token_TEXT);#add the word itself. Will be mapped to unknown shared vector later!
                else:
                    SP_FEATURE_WORDS.append (token_TEXT);

        for token_id in SHORTEST_PATH:
            #SHOULD WE CHANGE BACTERIA IF NOT IN THE MODEL ? for example "Salmonellae" ---> "bacteria" ... 
            #CRITICAL ..... 
            if (token_id == E1_Head_Token_ID):
                SpecialTreatmentForTwoEntities (token_id, E1_TYPE, SP_FEATURE_WORDS);
            
            elif (token_id == E2_Head_Token_ID):
                SpecialTreatmentForTwoEntities (token_id, E2_TYPE, SP_FEATURE_WORDS);

            else:
                SP_FEATURE_WORDS.append ( TOKENS_DICT[token_id][1] ); #WORD ITSELF
            
            SP_FEATURE_POSTGS.append(self.LOWLEVEL_GetPOSTAG_Coding (TOKENS_DICT[token_id][2]));
        
        for i in range(len(SHORTEST_PATH)-1):
            #<<<CRITICAL>>>
            if GD.has_edge (SHORTEST_PATH[i] , SHORTEST_PATH[i+1]):
                Forward_Direction = True
                edge_type = GD.edge[SHORTEST_PATH[i]][SHORTEST_PATH[i+1]][0]["TYPE"];#<<<CRITICAL>>>

            elif GD.has_edge(SHORTEST_PATH[i+1],SHORTEST_PATH[i]):
                Forward_Direction = False
                edge_type = GD.edge[SHORTEST_PATH[i+1]][SHORTEST_PATH[i]][0]["TYPE"];#<<<CRITICAL>>> sometimes, in reverse path there is another edge ...
                #example : ('t4', 't10', {'TYPE': 'rcmod'}), ('t4', 't0', {'TYPE': 'nsubj'})

            else:
                self.PROGRAM_Halt ("Error in finding dependenct type direction!\n"+str(GD.edges())) ; 
                
            SP_FEATURE_EDGE_DPTGS.append (self.LOWLEVEL_Get_Stanford_DPTAG_Coding(edge_type, Forward_Direction)) ; 

        return SP_FEATURE_WORDS , SP_FEATURE_POSTGS , SP_FEATURE_EDGE_DPTGS ; 

    def CalculateNumberOfExamplesPerSentence (self, Sentences):
        TOTAL_POSITIVES = 0 ;
        TOTAL_NEGATIVES = 0 ; 
        for S in Sentences:
            NumberOfExamples = {"negatives":0} ; 
            if (len(S["ENTITIES"])==0) or (len(S["PAIRS"])==0): #Second condition for those sentences that have one entity but self interaction which are apparently discarded in ANTTI work ...
                S["NumberOfExamples"] = NumberOfExamples; 
            else:
                for pair in S["PAIRS"]:
                    if pair.has_key("BAGS"):
                        if pair["SHORTEST_PATH_F"] <> None:
                            if pair["POSITIVE"] == True:
                                if self.Configs["ClassificationType"]=="binary":

                                    if NumberOfExamples.has_key("positives"):
                                        NumberOfExamples["positives"]+=1 ; 
                                    else:
                                        NumberOfExamples["positives"]=1 ; 

                                else:
                                    CLASS_TP = pair["CLASS_TP"];
                                    if NumberOfExamples.has_key(CLASS_TP):
                                        NumberOfExamples[CLASS_TP]+=1 ; 
                                    else:
                                        NumberOfExamples[CLASS_TP]=1 ; 
                            else:
                                NumberOfExamples["negatives"]+=1;
                
                S["NumberOfExamples"] = NumberOfExamples; 
                TOTAL_POSITIVES += sum (S["NumberOfExamples"][t] for t in S["NumberOfExamples"] if t <> "negatives");
                TOTAL_NEGATIVES += S["NumberOfExamples"]["negatives"];
        self.lp (["-"*50 , "Calculating Number of Examples per sentence." , "-"*20, 
                  "EXAMPLE STATISTICS:", 
                  "NUMBER OF POSITIVES : " + str(TOTAL_POSITIVES) ,
                  "NUMBER OF NEGATIVES : " + str(TOTAL_NEGATIVES) , 
                  "TOTAL               : " + str(TOTAL_POSITIVES + TOTAL_NEGATIVES) , "-"*50]) ;
    
    def CalculateDocumentWiseStatistics (self, Sentences , PrintStatistics = False):
        docs = {}; 
        for sentence in Sentences:
            if docs.has_key(sentence["DOC_ID"]):
                docs[sentence["DOC_ID"]].append (sentence);
            else:
                docs[sentence["DOC_ID"]] = [sentence];

        docs_info = {}; 
        for doc_id in docs:
            docs_info[doc_id] = {"Interactions":{} , "Sentences":{} , "Sentence_Count":0};
            for sentence in docs[doc_id]:
                HAS_RELATION = False ; 
                for pair in sentence["PAIRS"]:
                    if pair["SHORTEST_PATH_F"] <> None:
                        HAS_RELATION = True ; 
                        if not sentence["ID"] in docs_info[doc_id]["Sentences"]:
                            docs_info[doc_id]["Sentences"][sentence["ID"]] = {} ; 

                        if self.Configs["ClassificationType"] == "binary":
                            if pair["POSITIVE"]==True:
                                if docs_info[doc_id]["Interactions"].has_key("Positives"):
                                    docs_info[doc_id]["Interactions"]["Positives"]+=1;
                                else:
                                    docs_info[doc_id]["Interactions"]["Positives"]=1;
                                
                                if docs_info[doc_id]["Sentences"][sentence["ID"]].has_key("Positives"):
                                    docs_info[doc_id]["Sentences"][sentence["ID"]]["Positives"]+=1 ;
                                else:
                                    docs_info[doc_id]["Sentences"][sentence["ID"]]["Positives"]=1 ;

                            else:
                                if docs_info[doc_id]["Interactions"].has_key("Negatives"):
                                    docs_info[doc_id]["Interactions"]["Negatives"]+=1;
                                else:
                                    docs_info[doc_id]["Interactions"]["Negatives"]=1;

                                if docs_info[doc_id]["Sentences"][sentence["ID"]].has_key("Negatives"):
                                    docs_info[doc_id]["Sentences"][sentence["ID"]]["Negatives"]+=1 ;
                                else:
                                    docs_info[doc_id]["Sentences"][sentence["ID"]]["Negatives"]=1 ;

                        else: #multiclass
                            if pair["CLASS_TP"]==None:
                                if docs_info[doc_id]["Interactions"].has_key("Negatives"):
                                    docs_info[doc_id]["Interactions"]["Negatives"]+=1;
                                else:
                                    docs_info[doc_id]["Interactions"]["Negatives"]=1;
                                
                                if docs_info[doc_id]["Sentences"][sentence["ID"]].has_key("Negatives"):
                                    docs_info[doc_id]["Sentences"][sentence["ID"]]["Negatives"]+= 1 ; 
                                else:
                                    docs_info[doc_id]["Sentences"][sentence["ID"]]["Negatives"]= 1 ; 
                                    
                            else:
                                if docs_info[doc_id]["Interactions"].has_key(pair["CLASS_TP"]):
                                    docs_info[doc_id]["Interactions"][pair["CLASS_TP"]]+=1;
                                else:
                                    docs_info[doc_id]["Interactions"][pair["CLASS_TP"]]=1;

                                if docs_info[doc_id]["Sentences"][sentence["ID"]].has_key(pair["CLASS_TP"]):
                                    docs_info[doc_id]["Sentences"][sentence["ID"]][pair["CLASS_TP"]]+= 1 ; 
                                else:
                                    docs_info[doc_id]["Sentences"][sentence["ID"]][pair["CLASS_TP"]]= 1 ; 
                if HAS_RELATION:
                    if docs_info[doc_id].has_key("Sentence_Count"):
                        docs_info[doc_id]["Sentence_Count"] += 1 ;
                    else:
                        docs_info[doc_id]["Sentence_Count"] = 1 ;
                        
        if PrintStatistics:
            MSG = ["-"*55 , " -------- STATISTICS ABOUT EXAMPLES IN EACH DOCUMENT --------"] ; 
            for d_id in docs_info:
                MSG.append (d_id + ":   Sentences:" + str(docs_info[d_id]["Sentence_Count"]) + "    Total Examples:" + str(sum([docs_info[d_id]["Interactions"][i] for i in docs_info[d_id]["Interactions"]])));
                for s_id in docs_info[d_id]["Sentences"]:
                    MSG.append ("\t"+s_id+":  " + str(docs_info[d_id]["Sentences"][s_id])) ; 
                MSG.append ("-");
            self.lp (MSG); 
            
        return docs, docs_info ;                          
                    
    def OnTheFlyPipeline (self, FilePath,DuplicationRemovalPolicy):
        self.NotFoundPOSTags = set() ; 
        self.NotFoundDTTags_Mapped = set(); 
        self.NotFoundDTTags_NotMapped = set(); 
        self.lp (["-"*80, "RUNNING PREPROCESSING PIPELINE FOR FILE:" , FilePath]); 
        Root = self.LoadTEESFile_GetTreeRoot (FilePath); 
        Sentences , LOCAL_TotalCorpusRootAnalysisResult = self.ProcessRoot (Root,DuplicationRemovalPolicy); 
        #import pdb ; pdb.set_trace() 
        self.BuildBagsOfFeatures (Sentences); 
        self.CalculateNumberOfExamplesPerSentence (Sentences); 
        docs, docs_info = self.CalculateDocumentWiseStatistics (Sentences); 

        if len(self.NotFoundPOSTags)>0:
            self.lp (["[WARNING]: Following POS Tags were in the XML, but not defined in the pipeline: " , str(list(self.NotFoundPOSTags))]); 
            
        if len(self.NotFoundDTTags_Mapped)>0:
            self.lp (["[WARNING]: Following DT were in the XML, not in the defined pipeline; mapped to their general embedding: " , str(list(self.NotFoundDTTags_Mapped))]);

        if len(self.NotFoundDTTags_NotMapped)>0:
            self.lp (["[WARNING]: Following DT were in the XML, not in the defined pipeline, NOT MAPPED to any general embedding: " , str(list(self.NotFoundDTTags_NotMapped))]);
            
        return Sentences , Root , LOCAL_TotalCorpusRootAnalysisResult , docs, docs_info ; 
        
