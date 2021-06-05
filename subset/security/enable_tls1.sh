#!/bin/bash 
#

sed -i '1s/^/openssl_conf = default_conf;\n/' /etc/ssl/openssl.cnf

cat <<EOF >> /etc/ssl/openssl.cnf
[default_conf]
ssl_conf = ssl_sect

[ssl_sect]
system_default = system_default_sect

[system_default_sect]
CipherString = DEFAULT@SECLEVEL=1
MinProtocol = TLSv1
EOF
