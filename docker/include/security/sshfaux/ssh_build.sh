#!/bin/bash 
#
# Build older versions OpenSSL 1.0.2 and OpenSSH 7.2
# Used for testing in faux devices only
#
# To run SSHD use /usr/local/sbin/sshd
# SSH components, e.g. ssh-keygen are found in /usr/local/bin
# SSH configuration and keys found in /usr/local/etc

# Build OpenSSL 1.0.2
wget https://www.openssl.org/source/openssl-1.0.2g.tar.gz 
tar -xzf openssl-1.0.2g.tar.gz 
cd openssl-1.0.2g 
./config --prefix=/usr/local/openssl --openssldir=/usr/local/openssl 
make -s 
make -s install 
cd .. 

# Prepare privellage seperation for SSHD
source ssh_privsep.sh

# Build OpenSSH 7.2
wget https://mirrors.mit.edu/pub/OpenBSD/OpenSSH/portable/openssh-7.2p1.tar.gz 
tar -xzf openssh-7.2p1.tar.gz 
cd openssh-7.2p1 
./configure --with-ssl-dir=/usr/local/openssl --with-ssh1 
make -s  
make -s install
