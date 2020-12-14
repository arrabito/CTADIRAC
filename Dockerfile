FROM centos:7


RUN useradd -ms /bin/bash dirac

WORKDIR /home/dirac

# CTADIRAC client location
ARG HOME=/home/dirac
ARG DIRAC_ROOT=$HOME/dirac_client

# Set Python version
ARG PYTHON_VERSION=27

RUN yum -y update

# General packages needed inside the container
RUN yum -y install epel-release less strace wget git which emacs

# Packages DIRAC depends on
RUN yum -y install boost-program-options boost-python boost-system boost-thread c-ares lfc-libs libtool-ltdl protobuf

# Install CAs in the default location /etc/grid-security/certificates
RUN echo $'[EGI-trustanchors] \n\
name=EGI-trustanchors \n\
baseurl=http://repository.egi.eu/sw/production/cas/1/current/ \n\
gpgkey=http://repository.egi.eu/sw/production/cas/1/GPG-KEY-EUGridPMA-RPM-3 \n\
gpgcheck=1 \n\
enabled=1' >  /etc/yum.repos.d/ca-policy-egi.repo

RUN yum -y install ca-policy-egi-core

# Create base directory for CTADIRAC client installation
USER dirac

RUN mkdir -p $DIRAC_ROOT

# Install CTADIRAC client
RUN cd $DIRAC_ROOT; wget --no-check-certificate https://github.com/DIRACGrid/DIRAC/raw/master/Core/scripts/dirac-install.py; python dirac-install.py -V CTA -v

# Since there is no proxy available, manually configure the CTADIRAC client
RUN echo $'LocalInstallation \n\
{ \n\
  ConfigurationServer = dips://ccdcta-server04.in2p3.fr:9135/Configuration/Server \n\
  ConfigurationServer += dips://ccdcta-server05.in2p3.fr:9135/Configuration/Server \n\
  ConfigurationServer += dips://dcta-agents.pic.es:9135/Configuration/Server \n\
  ConfigurationServer += dips://dcta-servers.pic.es:9135/Configuration/Server \n\
  VirtualOrganization = vo.cta.in2p3.fr \n\
  Setup = CTA \n\
  PythonVersion = ${PYTHONVERSION} \n\
  Project = CTA \n\
  InstallType = client \n\
  Extensions = COMDIRAC \n\
  Extensions += CTA \n\
  SkipCAChecks = True' > $DIRAC_ROOT/etc/dirac.cfg
  RUN export rel=$(curl -s -L http://cta-dirac.in2p3.fr/DIRAC/defaults/cta.cfg | grep Release | tail -1 | awk -F "= " '{print $2}'); echo "  Release=$rel" >> $DIRAC_ROOT/etc/dirac.cfg
RUN echo $'  SkipCADownload = False \n\
} \n\
DIRAC \n\
{ \n\
  Configuration \n\
  { \n\
    Servers = dips://ccdcta-server04.in2p3.fr:9135/Configuration/Server \n\
    Servers += dips://ccdcta-server05.in2p3.fr:9135/Configuration/Server \n\
    Servers += dips://dcta-agents.pic.es:9135/Configuration/Server \n\
    Servers += dips://dcta-servers.pic.es:9135/Configuration/Server \n\
  } \n\
  Setup = CTA \n\
  VirtualOrganization = vo.cta.in2p3.fr \n\
  Extensions = COMDIRAC \n\
  Extensions += CTA \n\
  Security \n\
  { \n\
    # This option is specific to the usage in container \n\
    CALocation = /tmp/etc/grid-security/certificates \n\
    UseServerCertificate = no \n\
    SkipCAChecks = yes \n\
  } \n\
}' >> $DIRAC_ROOT/etc/dirac.cfg


RUN mkdir -p $DIRAC_ROOT/etc/grid-security/vomses
RUN echo $'"vo.cta.in2p3.fr" "cclcgvomsli01.in2p3.fr" "15008" "/O=GRID-FR/C=FR/O=CNRS/OU=CC-IN2P3/CN=cclcgvomsli01.in2p3.fr" "vo.cta.in2p3.fr" "24"' > $DIRAC_ROOT/etc/grid-security/vomses/vo.cta.in2p3.fr

RUN mkdir -p $DIRAC_ROOT/etc/grid-security/vomsdir/vo.cta.in2p3.fr
RUN echo $'/O=GRID-FR/C=FR/O=CNRS/OU=CC-IN2P3/CN=cclcgvomsli01.in2p3.fr \n\
/C=FR/O=MENESR/OU=GRID-FR/CN=AC GRID-FR Services' > $DIRAC_ROOT/etc/grid-security/vomsdir/vo.cta.in2p3.fr/cclcgvomsli01.in2p3.fr.lsc


RUN echo $'#!/bin/bash \n\
# Copy CAs in a writable location shared with the host \n\
if ! [ -d "/tmp/etc/grid-security/certificates" ] \n\
  then \n\
  mkdir -p /tmp/etc/grid-security \n\
  cp -R /etc/grid-security/certificates /tmp/etc/grid-security \n\
fi \n\
source /home/dirac/dirac_client/bashrc \n\
/bin/bash' > dirac_env.sh

RUN chmod +x dirac_env.sh

RUN ln -s $DIRAC_ROOT/bashrc $DIRAC_ROOT/pro/bashrc

CMD source /home/dirac/dirac_env.sh


