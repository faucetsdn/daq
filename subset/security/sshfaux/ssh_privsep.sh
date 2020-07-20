#!/bin/bash 
#
# Prepare environment for running SSHD with privilege separation 
# https://github.com/openssh/openssh-portable/blob/master/README.privsep

mkdir /etc/ssh 
mkdir /var/empty 
chown root:sys /var/empty 
chmod 755 /var/empty 
groupadd sshd 
useradd -g sshd -c 'sshd privsep' -d /var/empty -s /bin/false sshd 
