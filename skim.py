import ROOT
import datetime

# Written by David Hadley
# Modified by Steve Dennis
# University of Warwick 2012

###############################################################################

class SkimOaAnalysisException(Exception):
    pass

###############################################################################

class SkimOaAnalysis:
    '''Select specific events from a set of oaAnalysis files.'''
    def __init__(self, inputFileList, outputFileName, selection):
        '''Construct an new skimming object. 
        Requires an list of input file names, 
        the name of the output file (existing files will be overwritten).
        Selection must be an object which provides a method "applySelection(event)".
        This method must return True (event passed selection) or False (event did not pass selection).
        The input event is a dictionary of TTrees
        Run the job by calling "run()".
        '''
        self.inputFileList = inputFileList
        self.outputFileName = outputFileName
        self.selection = selection
        #Trees to be written out
        self.fullTreeNames = ["HeaderDir/BasicHeader",
                              "HeaderDir/BasicDataQuality",
                              "HeaderDir/BeamSummaryData",
                              "ReconDir/P0D",
                              "ReconDir/P0DECal",
                              "ReconDir/TrackerECal",
                              "ReconDir/Global",
                              "ReconDir/Tracker",
                              "ReconDir/SMRD",
                              "ReconDir/FGDOnly",
                              ]
        self.optionalTreeNames = ["TruthDir/Trajectories",
                                  "TruthDir/Vertices",
                                  "HeaderDir/GeometrySummary",
                                  ]
        self.listOfTreeNames = self.fullTreeNames+self.optionalTreeNames
        self.percentageComplete = 0
        return
    
    # Turns a dictionary of iterables into an iterator that returns a dictionary of the entries
    # Stops iterating when any iterator in the dictionary runs out
    @staticmethod
    def dictToIter(d):
      iterdict = dict( ((k, v.__iter__()) for (k, v) in d.items()) )
      
      while True:
        to_return = dict( ( (k, v.next()) for (k, v) in iterdict.items() ) )
          
        if len(to_return) == len(d):
          yield to_return
        else:
          raise StopIteration
    
    def getTreeNames(self):
        return self.listOfTreeNames
    
    def printProgress(self,i,nPseudoExperiments):
        '''Print percentage complete to the terminal.'''
        done = (100*i)/nPseudoExperiments
        if done >= self.percentageComplete:
            print "SkimOaAnalysis() ",str("%.0f"%(done)),"% complete (",i,"/",nPseudoExperiments,",",datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S"),")"
            if self.percentageComplete < 10:
              self.percentageComplete += 1
            else:
              self.percentageComplete += 10
    
    def run(self):
        '''Run the skimming job.'''
        outFile = None
        outTrees = None
        #loop over input files
        nFiles = len(self.inputFileList)
        for iFile,fname in enumerate(self.inputFileList):
            self.printProgress(iFile,nFiles)
            #~ print fname
            #open input file
            inFile = ROOT.TFile(fname,"read")
            inTrees = dict()
            for treeName in self.listOfTreeNames:
                tree = inFile.Get(treeName)
                if tree:
                    key = tuple(treeName.split("/"))
                    #print key
                    inTrees[key] = tree
            
            if outFile:
                #reset branch addresses
                for key,trOut in outTrees.iteritems():
                    trIn = inTrees[key]
                    trIn.CopyAddresses(trOut)
                  
            else:
                #create output file
                outFile = ROOT.TFile(self.outputFileName,"recreate")
                outTrees = dict()
                for key,tree in inTrees.iteritems():
                    dirName = key[0]
                    if not outFile.GetDirectory(dirName):
                        outFile.mkdir(dirName)
                    outFile.cd(dirName)
                    outTrees[key] = tree.CloneTree(0)
                    outFile.cd()
                    outTrees[key].SetAutoSave( int(3E7) ) # autosave every ~30 MB
                    
                    
            tree_iter = self.dictToIter(inTrees)
            #load trees
            for event in tree_iter:
                #print event,tree.GetName()
                if self.selection.applySelection(event):
                    #fill trees
                    for key,tree in outTrees.iteritems():
                        dirName = key[0]
                        outFile.cd(dirName)
                        tree.Fill()
        
        for key, tree in outTrees.iteritems():
          tree.AutoSave()
          
        outFile.Close()
        return
    
###############################################################################

def simpleTest():
    import glob
    import os
    #files to process
    inputFilePattern = "/home/dave/t2k/data/nd280/production005/A/rdp/ND280/00006000_00006999/anal/oa_nd_spl_*.root"
    inputFileList = glob.glob(inputFilePattern)
    #just do two files as a test
    inputFileList = inputFileList[:2]
    #load the oaAnalysisLibrary
    if not os.path.exists("libReadoaAnalysis"):
        tfile = ROOT.TFile(inputFileList[0],"read")
        tfile.MakeProject("libReadoaAnalysis","*","new+")
    ROOT.gSystem.Load("libReadoaAnalysis/libReadoaAnalysis.so")
    
    #a simple example selection class
    class SimpleSandMuonSelection:
        '''Selects events that contain a track with 3 TPC components.
        In beam these are very likely to contain sand muons.
        '''
        def applySelection(self, event):
          
            globalreco = event[('ReconDir', 'Global' )]
            #any global tracks have 3 TPCs?
            for pid in globalreco.PIDs:
                if pid.NTPCs>=3:
                    return True
            return False
    #run skim job
    outputFileName = "simpleTest.skimmer.oaAnalysis.root"
    selection = SimpleSandMuonSelection()
    skimmer = SkimOaAnalysis(inputFileList, outputFileName, selection)
    skimmer.run()
    #now do check that the output is sensible
    tfile = ROOT.TFile(outputFileName,"read")
    treeNames = skimmer.listOfTreeNames
    trees = dict([(n,tfile.Get(n)) for n in treeNames if n not in skimmer.optionalTreeNames])
    lastIds = None
    for tree in trees.itervalues():
        ids = [ (int(e.RunID),int(e.SubrunID),int(e.EventID)) for e in tree ]
        #check each entry should be unique
        assert len(set(ids)) == len(ids)
        if lastIds:
            #check that event ids are identical in each tree
            assert ids == lastIds
        lastIds = ids
    print "done!"
    return

###############################################################################                

def main():
    simpleTest()

if __name__ == "__main__":
    main()

