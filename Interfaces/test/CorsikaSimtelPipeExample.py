#!/usr/bin/env python
"""
  Submit a Corsika Simtel Example Job with piping
"""
from DIRAC.Core.Base import Script
Script.setUsageMessage( '\n'.join( [ __doc__.split( '\n' )[1],
                                     'Usage:',
                                     '  %s [option|cfgfile] ... [runMin] ...' % Script.scriptName,
                                     'Arguments:',
                                     '  runMin:     Min runNumber',
                                     '  runMax:     Max runNumber',
                                     '  cfgFile:    Corsika config file',
                                     '  storageElement: Storage Element'] ) )
Script.parseCommandLine()

import os

def CorsikaSimtelPipeExample( args = None ) :
  
  from CTADIRAC.Interfaces.API.CorsikaSimtelPipeProdJob import CorsikaSimtelPipeProdJob
  from DIRAC.Interfaces.API.Dirac import Dirac
  
  j = CorsikaSimtelPipeProdJob()
  j.setVersion('prod-2_21122012')

  j.setExecutable('corsika_autoinputs') 

  ilist = []

  if (len(args) != 3 and len(args) != 4):
    Script.showHelp()
  
  if (len(args)==4):
    storage_element = args[3]
    if storage_element not in ('CC-IN2P3-Tape','CYF-STORM-Disk','DESY-ZN-Disk'):
      print 'Storage element is not valid'
      Script.showHelp()
  else :
    storage_element = 'LUPM-Disk'

  runMin = int(args[0])
  runMax = int(args[1])
  cfgfile = args[2]

  for i in range(runMin,runMax+1):
    run_number = '%06d' % i
    ilist.append(run_number)

  j.setGenericParametricInput(ilist)                                                                                         
  j.setName('run%s')
  
  j.setJobGroup(cfgfile[7:])

  j.setInputSandbox( [ cfgfile ,'fileCatalog.cfg','prodConfigFile'] )

  j.setParameters(['fileCatalog.cfg','--template',cfgfile,'-D',storage_element])

  j.setOutputSandbox( ['corsika_autoinputs.log'])

  j.setCPUTime(100000)

  Script.gLogger.info( j._toJDL() )
  Dirac().submit( j )


if __name__ == '__main__':

  args = Script.getPositionalArgs()

  try:
    CorsikaSimtelPipeExample( args )
  except Exception:
    Script.gLogger.exception()
