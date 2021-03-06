#!/usr/bin/env python
import DIRAC
import os
import gzip

def sendSimtelOutput(stdid,line):
  logfilename = 'simtel.log.gz'
  f = gzip.open( logfilename,'ab')
  f.write(line)
  f.write('\n')
  f.close()
  
def sendOutput(stdid,line):
  DIRAC.gLogger.notice(line)
  
def main():

  from DIRAC.Core.Base import Script
 
  Script.registerSwitch( "T:", "template=", "Corsika Template" )
  Script.registerSwitch( "p:", "run_number=", "Do not use: Run Number automatically set" )
  Script.registerSwitch( "E:", "executable=", "Executable (Use SetExecutable)")
  Script.registerSwitch( "v:", "version=", "Version (Use setVersion)")  
  Script.registerSwitch( "D:", "dcta=", "dcta")
  Script.registerSwitch( "I:", "icta=", "icta")
  Script.registerSwitch( "C:", "c_cta=", "c_cta")
  
  Script.parseCommandLine( ignoreErrors = False )
  
  ## default values ##############
  run_number = None
  template = None
  executable = None
  version = None
  
  ### set switch values ###
  for switch in Script.getUnprocessedSwitches():
    if switch[0] == "run_number" or switch[0] == "p":
      run_number = switch[1].split('ParametricParameters=')[1]
    elif switch[0] == "template" or switch[0] == "T":
      template = switch[1]
    elif switch[0] == "executable" or switch[0] == "E":
      executable = switch[1]
    elif switch[0] == "version" or switch[0] == "v":
      version = switch[1]
      
  if version == None or executable == None or run_number == None or template == None:
    Script.showHelp()
    jobReport.setApplicationStatus('Missing options')
    DIRAC.exit( -1 )   

  from CTADIRAC.Core.Workflow.Modules.CorsikaApp import CorsikaApp
  from CTADIRAC.Core.Utilities.SoftwareInstallation import checkSoftwarePackage
  from CTADIRAC.Core.Utilities.SoftwareInstallation import installSoftwarePackage
  from CTADIRAC.Core.Utilities.SoftwareInstallation import installSoftwareEnviron
  from CTADIRAC.Core.Utilities.SoftwareInstallation import getSoftwareEnviron
  from CTADIRAC.Core.Utilities.SoftwareInstallation import localArea
  from CTADIRAC.Core.Utilities.SoftwareInstallation import sharedArea
  from CTADIRAC.Core.Utilities.SoftwareInstallation import workingArea
  from DIRAC.Core.Utilities.Subprocess import systemCall
  from DIRAC.WorkloadManagementSystem.Client.JobReport import JobReport

  jobID = os.environ['JOBID']
  jobID = int( jobID )
  jobReport = JobReport( jobID )

  CorsikaSimtelPack = 'corsika_simhessarray/' + version + '/corsika_simhessarray'

  packs = [CorsikaSimtelPack]

  for package in packs:
    DIRAC.gLogger.notice( 'Checking:', package )
    if sharedArea:
      if checkSoftwarePackage( package, sharedArea() )['OK']:
        DIRAC.gLogger.notice( 'Package found in Shared Area:', package )
        installSoftwareEnviron( package, workingArea() )
        packageTuple =  package.split('/')
        corsika_subdir = sharedArea() + '/' + packageTuple[0] + '/' + version 
        cmd = 'cp -u -r ' + corsika_subdir + '/* .'        
        os.system(cmd)
        continue
    if workingArea:
      if checkSoftwarePackage( package, workingArea() )['OK']:
        DIRAC.gLogger.notice( 'Package found in Local Area:', package )
        continue
      if installSoftwarePackage( package, workingArea() )['OK']:
      ############## compile #############################
        cmdTuple = ['./build_all','prod2','qgs2']
######### special case for Astri ############################
        if version == 'prod-2_08072014_to':
        ############## compile #############################
          fd = open('run_compile.sh', 'w' )
          fd.write( """#! /bin/sh  
source ./build_all prod2 qgs2
#
echo " Let's check that build_all did its work " 
ls -alFsh 
echo "+++++++++++++++++++++++++++++++++++++++++++++++++"
echo " Let's see what files are in the corsika-run directory " 
ls -alFsh ./corsika-run
#
if [ ! -x ./corsika-run/corsika ]
then 
    echo " ERROR: Corsika executable found. Exit " 
    exit 1
fi
echo "+++++++++++++++++++++++++++++++++++++++++++++++++"
#
echo " Now let's try to compile hessio according to Federico's recipe "
cd ./hessioxxx 
make clean 
make EXTRA_DEFINES="-DCTA_PROD2 -DWITH_LOW_GAIN_CHANNEL"
# 
echo " Let's see what files are in the lib directory " 
ls -alFsh ./lib
#
if [ ! -f ./lib/libhessio.so ]
then 
    echo " ERROR: libhessio library not found. Exit " 
    exit 1
fi
echo "+++++++++++++++++++++++++++++++++++++++++++++++++"
#
cd .. # come back to original dir
# 
echo " Now let's try to compile simtel according to Federico's recipe "
cd ./sim_telarray
make clean 
make EXTRA_DEFINES="-DCTA_PROD2 -DWITH_LOW_GAIN_CHANNEL"
make install 
# 
echo " Let's see what files are in the bin directory " 
ls -alFsh ./bin
#
if [ ! -x ./bin/sim_telarray ]
then 
    echo " ERROR: sim_telarray excutable not found. Exit " 
    exit 1
fi
echo "+++++++++++++++++++++++++++++++++++++++++++++++++"
#
echo " Everything was compiled and linked properly" """)
          fd.close()
          os.system('chmod u+x run_compile.sh')
          cmdTuple = ['./run_compile.sh']
##########################################################################
        ret = systemCall( 0, cmdTuple, sendOutput)
        if not ret['OK']:
          DIRAC.gLogger.error( 'Failed to execute build')
          DIRAC.exit( -1 )
        continue

    DIRAC.gLogger.error( 'Check Failed for software package:', package )
    DIRAC.gLogger.error( 'Software package not available')
    DIRAC.exit( -1 )  

###### execute corsika ###############
  cs = CorsikaApp()
  cs.setSoftwarePackage(CorsikaSimtelPack)
  cs.csExe = executable
  cs.csArguments = ['--run-number',run_number,'--run','corsika',template] 
  corsikaReturnCode = cs.execute()
  
  if corsikaReturnCode != 0:
    DIRAC.gLogger.error( 'Failed to execute corsika Application')
    jobReport.setApplicationStatus('Corsika Application: Failed')
    DIRAC.exit( -1 )

###### rename corsika file #################################
  rundir = 'run' + run_number
  corsikaKEYWORDS = ['TELFIL']
  dictCorsikaKW = fileToKWDict(template,corsikaKEYWORDS)
  corsikafilename = rundir + '/' + dictCorsikaKW['TELFIL'][0]
  destcorsikafilename = 'corsika_run' + run_number + '.corsika.gz'
  cmd = 'mv ' + corsikafilename + ' ' + destcorsikafilename
  os.system(cmd)
  
  ### create corsika tar ####################
  corsika_tar = 'corsika_run' + run_number + '.tar.gz'
  filetar1 = rundir + '/'+'input'
  filetar2 = rundir + '/'+ 'DAT' + run_number + '.dbase'
  filetar3 = rundir + '/run' + str(int(run_number)) + '.log'
  cmdTuple = ['/bin/tar','zcf',corsika_tar, filetar1,filetar2,filetar3]
  DIRAC.gLogger.notice( 'Executing command tuple:', cmdTuple )
  ret = systemCall( 0, cmdTuple, sendOutput)
  if not ret['OK']:
    DIRAC.gLogger.error( 'Failed to execute tar')
    DIRAC.exit( -1 )

###### execute sim_telarray ###############
  ret = getSoftwareEnviron( CorsikaSimtelPack )
  if not ret['OK']:
    error = ret['Message']
    DIRAC.gLogger.error( error, CorsikaSimtelPack )
    DIRAC.exit( -1 )

  corsikaEnviron = ret['Value']
  cmdTuple = ['sim_telarray']
  # add input file argument for sim_telarray  ###################
  inputfile = 'input_file='+destcorsikafilename
  inputfileopt = ['-C',inputfile]
  cmdTuple.extend(inputfileopt)
  # add output file argument for sim_telarray 
  destsimtelfilename = 'simtel_run' + run_number + '.simtel.gz'
  outputfile = 'output_file='+destsimtelfilename
  outputfileopt = ['-C',outputfile]
  cmdTuple.extend(outputfileopt)
  # add histo argument for sim_telarray 
  desthistofilename = 'simtel_run' + run_number + '.hdata.gz'
  histofile = 'histogram_file='+desthistofilename
  histofileopt = ['-C',histofile]
  cmdTuple.extend(histofileopt)

  # add other arguments for sim_telarray specified by user ######
  simtelparfile = open('simtel.par', 'r').readlines()
  
  for line in simtelparfile:
    for word in line.split():
      cmdTuple.append(word)

  DIRAC.gLogger.notice( 'Executing command tuple:', cmdTuple )
  ret = systemCall( 0, cmdTuple, sendSimtelOutput,env = corsikaEnviron )

  if not ret['OK']:
    DIRAC.gLogger.error( 'Failed to execute:',simexe)
    DIRAC.exit( -1 )
    
  DIRAC.exit()

#### parse corsika template ##############
def fileToKWDict (fileName, keywordsList):    
  DIRAC.gLogger.notice('parsing: ', fileName)
  dict={}
  configFile = open(fileName, "r").readlines()
  for line in configFile:
    for word in line.split():
      if word in keywordsList:
        lineSplit = line.split()
        lenLineSplit = len(lineSplit)
        value = lineSplit[1:lenLineSplit]
        dict[word] = value
  return dict

if __name__ == '__main__':

  try:
    main()
  except Exception:
    DIRAC.gLogger.exception()
    DIRAC.exit( -1 )


