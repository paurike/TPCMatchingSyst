import ROOT
import os

# Adapted from code by David Hadley
def loadoaAnalysisLib(inputFileName, name=""):
    '''loadoaAnalysisLib will create a library for reading the contents of the
     input file. The output directory will be libReadoaAnalysis<name>. If the 
     output directory exists it skips the MakeProject step and just loads the
      existing library.
    '''
    outputPath = "libReadoaAnalysis"+name
    if not os.path.exists(outputPath):
        tfile = ROOT.TFile(inputFileName,"read")
        if not tfile.IsOpen():
            raise Exception(__name__+".loadoaAnalysisLib could not open input file",inputFileName, name)
        tfile.MakeProject(outputPath,"*","new+")
    ROOT.gSystem.Load(outputPath+"/"+outputPath+".so")
    return
