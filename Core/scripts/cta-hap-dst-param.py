#!/usr/bin/env python
import DIRAC
import os
import re

def setRunNumber( optionValue ):
  global run_number  
  inputfile = optionValue.split('ParametricInputData=')[1]
  p = re.compile('[0-9]{6}')
  run_number = p.search(inputfile).group()
  global part_type
  for part in ['gamma','electron','proton']:
    p = re.compile(part)
    if (p.search(inputfile)==None):
      continue
    else:
      part_type = p.search(inputfile).group()

def setTellist( optionValue ):
  global tellist
  tellist = optionValue
  return DIRAC.S_OK()

def setNevent( optionValue ):
  global nevent
  nevent = optionValue
  return DIRAC.S_OK()

def setVersion( optionValue ):
  global version
  version = optionValue
  return DIRAC.S_OK()

def sendOutput(stdid,line):
  DIRAC.gLogger.notice(line)


def main():

  from DIRAC.Core.Base import Script

### make_CTA_DST options ###############################################
  Script.registerSwitch( "T:", "tellist=", "Tellist", setTellist )
  Script.registerSwitch( "N:", "nevent=", "Nevent", setNevent )
  Script.registerSwitch( "p:", "run_number=", "Run Number (set automatically)", setRunNumber )
### other options ###############################################
  Script.registerSwitch( "V:", "version=", "HAP version", setVersion )

  Script.parseCommandLine( ignoreErrors = True )

  args = Script.getPositionalArgs()

  if len( args ) < 1:
    Script.showHelp()
  
  if tellist == None or version == None:
    Script.showHelp()
    jobReport.setApplicationStatus('Options badly specified')
    DIRAC.exit( -1 )
   
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

  hr = HapRootMacro()
  hr.setSoftwarePackage(HapPack)

  telconf = os.path.join( localArea(),'HAP/%s/config/%s' % (version,tellist))
  infile = build_infile()
  infilestr = '"' + infile + '"'
  telconfstr = '"' + telconf + '"'
  args = [str(int(run_number)), infilestr, telconfstr]
  
  try:
    args.extend([nevent])
  except NameError:
    DIRAC.gLogger.info( 'nevent arg not used' )
 
  DIRAC.gLogger.notice( 'make_CTA_DST macro Arguments:', args )
  hr.rootMacro = '/hapscripts/dst/make_CTA_DST.C+'
  hr.rootArguments = args
  DIRAC.gLogger.notice( 'Executing Hap make_CTA_DST macro' )
  res = hr.execute()

  if not res['OK']:
    DIRAC.gLogger.error( 'Failed to execute make_CTA_DST macro')
    jobReport.setApplicationStatus('Failure during make_CTA_DST')
    DIRAC.exit( -1 )

############ check existance of output file ####
  filedst = 'dst_CTA_%08d' % int(run_number) + '.root'

  if not os.path.isfile(filedst):
    DIRAC.gLogger.error('dst file not found:', filedst )
    jobReport.setApplicationStatus('make_CTA_DST.C: DST file not created')
    DIRAC.exit( -1 )

  fileout = 'dst_' + part_type + '_run' + run_number + '.root'
  cmd = 'mv ' + filedst + ' ' + fileout
  os.system(cmd)

###################Check std out #############################
  DIRAC.gLogger.notice('Executing DST Check step0')
    
  ret = getSoftwareEnviron(HapPack)
  if not ret['OK']:
    error = ret['Message']
    DIRAC.gLogger.error( error, HapPack)
    DIRAC.exit( -1 )

  hapEnviron = ret['Value']
  hessroot =  hapEnviron['HESSROOT']
  check_script = hessroot + '/hapscripts/dst/check_dst0.csh'
  cmdTuple = [check_script]
  ret = systemCall( 0, cmdTuple, sendOutput)
       
  if not ret['OK']:
    DIRAC.gLogger.error( 'Failed to execute DST Check step0')
    jobReport.setApplicationStatus('Check_dst0: Failed')
    DIRAC.exit( -1 )

  status, stdout, stderr = ret['Value']
  if status==1:
    jobReport.setApplicationStatus('Check_dst0: Big problem during the DST production')
    DIRAC.gLogger.error( 'DST Check step0 reports: Big problem during the DST production' )
    DIRAC.exit( -1 )
  if status==2:
    jobReport.setApplicationStatus('Check_dst0: No triggered events')
    DIRAC.gLogger.notice( 'DST Check step0 reports: No triggered events' )
    DIRAC.exit( )

############# run the CheckDST macro #################
  DIRAC.gLogger.notice('Executing DST check step1')
  hr.rootMacro = '/hapscripts/dst/CheckDST.C+'
  fileoutstr = '"' + fileout + '"'
  args = [fileoutstr]
  DIRAC.gLogger.notice( 'CheckDST macro Arguments:', args )
  hr.rootArguments = args
  DIRAC.gLogger.notice( 'Executing Hap CheckDST macro')
  res = hr.execute()

  if not res['OK']:
    DIRAC.gLogger.error( 'Failure during DST Check step1' )
    jobReport.setApplicationStatus('Check_dst1: Failed')
    DIRAC.exit( -1 )

#######################Check std out of CheckDST macro ##########################
  DIRAC.gLogger.notice('Executing DST Check step2')
  check_script = hessroot + '/hapscripts/dst/check_dst2.csh'
  cmdTuple = [check_script]
  ret = systemCall( 0, cmdTuple, sendOutput )
       
  if not ret['OK']:
    DIRAC.gLogger.error( 'Failed to execute DST Check step2')
    jobReport.setApplicationStatus('Check_dst2: Failed')
    DIRAC.exit( -1 )

  status, stdout, stderr = ret['Value']
  if status==1:
    jobReport.setApplicationStatus('DST Check step2: Big problem during the DST production')
    DIRAC.gLogger.error( 'DST Check step2 reports: Big problem during the DST production' )
    DIRAC.exit( -1 )
  if status==2:
    jobReport.setApplicationStatus('DST Check step2: No triggered events')
    DIRAC.gLogger.notice( 'DST Check step2 reports: No triggered events' )
    DIRAC.exit( )

  DIRAC.exit()

def build_infile():

  from DIRAC.Resources.Catalog.PoolXMLCatalog import PoolXMLCatalog

  pm = PoolXMLCatalog('pool_xml_catalog.xml')

  for Lfn in pm.getLfnsList():
    pfn = pm.getPfnsByLfn(Lfn)['Replicas']['Uknown']

  return pfn


if __name__ == '__main__':

  try:
    main()
  except Exception:
    DIRAC.gLogger.exception()
    DIRAC.exit( -1 )