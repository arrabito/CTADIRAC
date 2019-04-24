Bootstrap: docker
From: centos:7

%environment
source /opt/dirac/bashrc
export X509_CERT_DIR=/opt/dirac/etc/grid-security/certificates
export SSL_CERT_DIR=/opt/dirac/etc/grid-security/certificates

%post
# CTADIRAC client location
export DIRAC_ROOT=/opt/dirac

# Retrieve the latest CTADIRAC release from defaults
PYTHON_VERSION=27
RELEASE=$(curl -s -L http://cta-dirac.in2p3.fr/DIRAC/defaults/cta.cfg | grep Release | tail -1 | awk -F "= " '{print $2}')
LCGVER=$(curl -s -L http://cta-dirac.in2p3.fr/DIRAC/defaults/cta.cfg | grep LcgVer | awk -F "= " '{print $2}')

yum -y update
# General packages needed inside the container
yum -y install epel-release less strace wget git which 
# Packages DIRAC depends on
yum -y install boost-program-options boost-python boost-system boost-thread c-ares lfc-libs libtool-ltdl protobuf
# Install ntpdate to make sure clock is exact
# yum -y install ntpdate.x86_64
# Sync the clock
# ntpdate ntp.inria.fr

# Install CAs on /tmp (shared with host by default) 
#rm -R /etc/grid-security/certificates
# mkdir -p /tmp/etc/grid-security/certificates
#ln -s /tmp/etc/grid-security/certificates /etc/grid-security
cat <<EOF > /etc/yum.repos.d/ca-policy-egi.repo
[EGI-trustanchors]
name=EGI-trustanchors
baseurl=http://repository.egi.eu/sw/production/cas/1/current/
gpgkey=http://repository.egi.eu/sw/production/cas/1/GPG-KEY-EUGridPMA-RPM-3
gpgcheck=1
enabled=1
EOF

yum -y install ca-policy-egi-core

mkdir -p /tmp/etc/grid-security
cp -R /etc/grid-security/certificates /tmp/etc/grid-security

# Create base directory for CTADIRAC client installation
mkdir -p $DIRAC_ROOT

# Install lcg bundles
mkdir -p $DIRAC_ROOT/.installCache
cd $DIRAC_ROOT/.installCache
wget http://diracproject.web.cern.ch/diracproject/tars/../lcgBundles/DIRAC-lcg-${LCGVER}-Linux_x86_64_glibc-2.17-python27.tar.gz

# Install CTADIRAC client
cd $DIRAC_ROOT
wget --no-check-certificate https://github.com/DIRACGrid/DIRAC/raw/master/Core/scripts/dirac-install.py
python dirac-install.py -V CTA -v

# Since there is no proxy available, manually configure the CTADIRAC client
cat <<EOF > $DIRAC_ROOT/etc/dirac.cfg
LocalInstallation
{
  ConfigurationServer = dips://ccdcta-server03.in2p3.fr:9135/Configuration/Server
  ConfigurationServer += dips://ccdcta-server02.in2p3.fr:9135/Configuration/Server
  ConfigurationServer += dips://dcta-agents01.pic.es:9135/Configuration/Server
  ConfigurationServer += dips://dcta-servers01.pic.es:9135/Configuration/Server
  VirtualOrganization = vo.cta.in2p3.fr
  Setup = CTA
  PythonVersion = ${PYTHONVERSION}
  Project = CTA
  InstallType = client
  Extensions = COMDIRAC
  Extensions += CTA
  SkipCAChecks = True
  Release = ${RELEASE}
  LcgVer = ${LCGVER}
  SkipCADownload = False
}
DIRAC
{
  Configuration
  {
    Servers = dips://ccdcta-server03.in2p3.fr:9135/Configuration/Server
    Servers += dips://ccdcta-server02.in2p3.fr:9135/Configuration/Server
    Servers += dips://dcta-agents01.pic.es:9135/Configuration/Server
    Servers += dips://dcta-servers01.pic.es:9135/Configuration/Server
  }
  Setup = CTA
  VirtualOrganization = vo.cta.in2p3.fr
  Extensions = COMDIRAC
  Extensions += CTA
  Security
  {
    UseServerCertificate = no
    SkipCAChecks = yes
  }
}
EOF

mkdir -p $DIRAC_ROOT/etc/grid-security/vomses
cat <<EOF > $DIRAC_ROOT/etc/grid-security/vomses/vo.cta.in2p3.fr
"vo.cta.in2p3.fr" "cclcgvomsli01.in2p3.fr" "15008" "/O=GRID-FR/C=FR/O=CNRS/OU=CC-IN2P3/CN=cclcgvomsli01.in2p3.fr" "vo.cta.in2p3.fr" "24"
EOF

mkdir -p $DIRAC_ROOT/etc/grid-security/vomsdir/vo.cta.in2p3.fr
cat <<EOF > $DIRAC_ROOT/etc/grid-security/vomsdir/vo.cta.in2p3.fr/cclcgvomsli01.in2p3.fr.lsc
/O=GRID-FR/C=FR/O=CNRS/OU=CC-IN2P3/CN=cclcgvomsli01.in2p3.fr
/C=FR/O=MENESR/OU=GRID-FR/CN=AC GRID-FR Services
EOF

# Change permissions to allow later CAs updates
chmod -R 777 $DIRAC_ROOT
chmod -R 777 /tmp/etc

# Create link to make CTADIRAC client point to the CAs location 
ln -s /tmp/etc/grid-security/certificates /opt/dirac/etc/grid-security

