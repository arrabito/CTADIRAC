#!/usr/bin/env python
import DIRAC
import os

def setInfile( optionValue ):
  global infile
  infile = optionValue
  return DIRAC.S_OK()

def setOutfile( optionValue ):
  global outfile
  outfile = optionValue
  return DIRAC.S_OK()

def setTellist( optionValue ):
  global tellist
  tellist = optionValue
  return DIRAC.S_OK()

def setPixelslices( optionValue ):
  global pixelslices
  pixelslices = optionValue
  return DIRAC.S_OK()

def setNfirst_mcevt( optionValue ):
  global Nfirst_mcevt
  Nfirst_mcevt = optionValue
  return DIRAC.S_OK()

def setNlast_mcevt( optionValue ):
  global Nlast_mcevt
  Nlast_mcevt = optionValue
  return DIRAC.S_OK()

def setVersion( optionValue ):
  global version
  version = optionValue
  return DIRAC.S_OK()

def sendOutput(stdid,line):
  DIRAC.gLogger.notice(line)


def main():

  from DIRAC.Core.Base import Script

#### eventio_cta options ##########################################
  Script.registerSwitch( "I:", "infile=", "Input file", setInfile )
  Script.registerSwitch( "O:", "outfile=", "Output file", setOutfile )
  Script.registerSwitch( "T:", "tellist=", "Tellist", setTellist )
  Script.registerSwitch( "F:", "Nfirst_mcevt=", "Nfirst_mcevt", setNfirst_mcevt)
  Script.registerSwitch( "L:", "Nlast_mcevt=", "Nlast_mcevt", setNlast_mcevt)
  Script.registerSwitch( "P:", "pixelslices=", "setPixelslices (true/false)",setPixelslices)
### other options ###############################################
  Script.registerSwitch( "V:", "version=", "HAP version", setVersion )

  Script.parseCommandLine( ignoreErrors = True ) 
 
  args = Script.getPositionalArgs()

  if len( args ) < 1:
    Script.showHelp()
  
  if outfile == None or infile == None or tellist == None or version == None:
    Script.showHelp()
    jobReport.setApplicationStatus('Options badly specified')
    DIRAC.exit( -1 ) 
   
  from CTADIRAC.Core.Workflow.Modules.HapApplication import HapApplication
  from CTADIRAC.Core.Workflow.Modules.HapRootMacro import HapRootMacro
  from CTADIRAC.Core.Utilities.SoftwareInstallation import checkSoftwarePackage
  from CTADIRAC.Core.Utilities.SoftwareInstallation import installSoftwarePackage
  from CTADIRAC.Core.Utilities.SoftwareInstallation import getSoftwareEnviron
  from CTADIRAC.Core.Utilities.SoftwareInstallation import localArea
  from CTADIRAC.Core.Utilities.SoftwareInstallation import sharedArea
  from DIRAC.Core.Utilities.Subprocess import systemCall
  from DIRAC.WorkloadManagementSystem.Client.JobReport import JobReport
  
  jobID = os.environ['JOBID']
  jobID = int( jobID )
  jobReport = JobReport( jobID )

  HapPack = 'HAP/' + version + '/HAP'

  packs = ['HESS/v0.2/lib','HESS/v0.3/root',HapPack] 

  for package in packs:
    DIRAC.gLogger.notice( 'Checking:', package )
    if sharedArea:
      if checkSoftwarePackage( package, sharedArea() )['OK']:
        DIRAC.gLogger.notice( 'Package found in Shared Area:', package )
        continue
    if localArea:
      if checkSoftwarePackage( package, localArea() )['OK']:
        DIRAC.gLogger.notice( 'Package found in Local Area:', package )
        continue
      if installSoftwarePackage( package, localArea() )['OK']:
        continue
    DIRAC.gLogger.error( 'Check Failed for software package:', package )
    DIRAC.gLogger.error( 'Software package not available')
    DIRAC.exit( -1 ) 

  telconf = os.path.join( localArea(),'HAP/%s/config/%s' % (version,tellist)) 

  ha = HapApplication()
  ha.setSoftwarePackage(HapPack)
  ha.hapExecutable = 'eventio_cta'
  ha.hapArguments = ['-file', infile, '-o', outfile, '-tellist', telconf]

  try:
    ha.hapArguments.extend(['-Nfirst_mcevt', Nfirst_mcevt, '-Nlast_mcevt', Nlast_mcevt])
  except NameError:
    DIRAC.gLogger.info( 'Nfirst_mcevt/Nlast_mcevt options are not used' )

  try:
    if(pixelslices == 'true'):
      ha.hapArguments.extend(['-pixelslices'])
  except NameError:
      DIRAC.gLogger.info( 'pixelslices option is not used' )

  DIRAC.gLogger.notice( 'Executing Hap Converter Application' )
  res = ha.execute()

  if not res['OK']:
    DIRAC.gLogger.error( 'Failed to execute eventio_cta Application')
    jobReport.setApplicationStatus('eventio_cta: Failed')
    DIRAC.exit( -1 )
  
  if not os.path.isfile(outfile):
    error = 'raw file was not created:'
    DIRAC.gLogger.error( error, outfile )
    jobReport.setApplicationStatus('eventio_cta: RawData not created')
    DIRAC.exit( -1 )

###################### Check RAW DATA #######################
  hr = HapRootMacro()
  hr.setSoftwarePackage(HapPack)
 
  DIRAC.gLogger.notice('Executing RAW check step0')
  hr.rootMacro = '/hapscripts/dst/Open_Raw.C+'
  outfilestr = '"' + outfile + '"'
  args = [outfilestr]
  DIRAC.gLogger.notice( 'Open_Raw macro Arguments:', args )
  hr.rootArguments = args
  DIRAC.gLogger.notice( 'Executing Hap Open_Raw macro')
  res = hr.execute()

  if not res['OK']:
    DIRAC.gLogger.error( 'Open_Raw: Failed' )
    DIRAC.exit( -1 )
    
#########################Quality Check for raw Output File: step1####################                                                                                                                  
  DIRAC.gLogger.notice('Executing Raw Check step1')
  
  ret = getSoftwareEnviron(HapPack)
  if not ret['OK']:
    error = ret['Message']
    DIRAC.gLogger.error( error, HapPack)
    DIRAC.exit( -1 )

  hapEnviron = ret['Value']
  hessroot =  hapEnviron['HESSROOT']
  check_script = hessroot + '/hapscripts/dst/check_raw.csh'
  cmdTuple = [check_script]
  ret = systemCall( 0, cmdTuple, sendOutput)

  if not ret['OK']:
    DIRAC.gLogger.error( 'Failed to execute RAW Check step1')
    jobReport.setApplicationStatus('Check_raw: Failed')
    DIRAC.exit( -1 )

  status, stdout, stderr = ret['Value']
  if status==1:
    jobReport.setApplicationStatus('RAW Check step1: Big problem during RAW production')
    DIRAC.gLogger.error( 'Check_raw: Big problem during RAW production' )
    DIRAC.exit( -1 )

  DIRAC.exit()

if __name__ == '__main__':

  try:
    main()
  except Exception:
    DIRAC.gLogger.exception()
    DIRAC.exit( -1 )


