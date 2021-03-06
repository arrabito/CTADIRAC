#!/usr/bin/env python
"""
  Submit an Example Hap Job
"""
from DIRAC.Core.Base import Script
Script.parseCommandLine()

def HapPerfExample() :
  from CTADIRAC.Interfaces.API.HapPerfJob import HapPerfJob
  from DIRAC.Interfaces.API.Dirac import Dirac

  HapVersion = 'v0.18'
####### DoCtaIrf option values #######################
  AnalysisType = 'Perf'
  EnergyMethod = 'Oak' 
  CutsConfig = 'ConfigTest_40pe_PSFA_arrayE'  
  RunList = 'dstrun'
  Zenith = '20'
  Offset = '0'
  Array = 'array-E.lis'
  ParticleType = 'gamma' 
##############################################

  infileLFNList = [
'/vo.cta.in2p3.fr/user/a/arrabito/HAP/mini-prod3/DST/gamma/dst_CTA_00283000.root',
'/vo.cta.in2p3.fr/user/a/arrabito/HAP/mini-prod3/DST/gamma/dst_CTA_00283001.root',
'/vo.cta.in2p3.fr/user/a/arrabito/HAP/mini-prod3/DST/gamma/dst_CTA_00283002.root',
'/vo.cta.in2p3.fr/user/a/arrabito/HAP/mini-prod3/DST/gamma/dst_CTA_00283003.root',
'/vo.cta.in2p3.fr/user/a/arrabito/HAP/mini-prod3/DST/gamma/dst_CTA_00283004.root',
'/vo.cta.in2p3.fr/user/a/arrabito/HAP/mini-prod3/DST/gamma/dst_CTA_00283005.root',
'/vo.cta.in2p3.fr/user/a/arrabito/HAP/mini-prod3/DST/gamma/dst_CTA_00283006.root',
'/vo.cta.in2p3.fr/user/a/arrabito/HAP/mini-prod3/DST/gamma/dst_CTA_00283007.root',
'/vo.cta.in2p3.fr/user/a/arrabito/HAP/mini-prod3/DST/gamma/dst_CTA_00283008.root',
'/vo.cta.in2p3.fr/user/a/arrabito/HAP/mini-prod3/DST/gamma/dst_CTA_00283009.root']

  for infileLFN in infileLFNList:

    general_opts = ['-V', HapVersion]

    DoCtaIrf_opts = ['-A',  AnalysisType,'-C', CutsConfig ,'-R', RunList, '-Z', Zenith, '-O', Offset, '-T', Array,'-M', EnergyMethod,'-P', ParticleType]

    opts = general_opts + DoCtaIrf_opts

    j = HapPerfJob(opts)

    j.setInputSandbox( ['LFN:/vo.cta.in2p3.fr/user/a/arrabito/HAP/mini-prod4/conf/v0.4/AnalysisConfig.tar.gz','passphrase'] )
    j.setOutputSandbox( ['DoCtaIrf.log'])

    j.setName(AnalysisType)

    j.setInputData(infileLFN)

#### build outdir #############################################
    RunNum = infileLFN.split( 'dst_CTA_' )[1].split('.root')[0] 
    outdir = 'HAP/Perf/' + ParticleType + '/' + RunNum 
    outfile = 'Performance_' + RunList  + '.root'

    j.setOutputData([outfile], outputSE='CC-IN2P3-Disk',outputPath=outdir) 
    j.setCPUTime(100000) 
    Script.gLogger.info( j._toJDL() )
    Dirac().submit( j )


if __name__ == '__main__':

  try:
    HapPerfExample()
  except Exception:
    Script.gLogger.exception()


