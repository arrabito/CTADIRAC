"""
  Simple Wrapper on the Job class to handle HAP DST macro
"""

__RCSID__ = "$Id$"

from DIRAC.Interfaces.API.Job import Job
from DIRAC.Core.Workflow.Workflow                   import Workflow
from CTADIRAC.Core.Utilities import SoftwareInstallation
import os

class HapDSTwfJob( Job ) :


  def __init__( self, parameters = None, cpuTime = 3600 ):

    Job.__init__( self )

    self.workflow = Workflow()
    self.executable = '$DIRACROOT/scripts/cta-hap-wf'
    self.setCPUTime( cpuTime )
    argumentStr = "%s" % ( ' '.join( parameters ) )
    self.setConfigArgs( argumentStr )








