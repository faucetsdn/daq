#!/bin/bash 
#

# Enable TLSv1 in OpenSSL
sed -i '1s/^/openssl_conf = default_conf\n/' /etc/ssl/openssl.cnf

cat <<EOF >> /etc/ssl/openssl.cnf
[default_conf]
ssl_conf = ssl_sect

[ssl_sect]
system_default = system_default_sect

[system_default_sect]
CipherString = DEFAULT@SECLEVEL=1
MinProtocol = TLSv1
EOF

#Enable TLSv1 in JDK
DISABLED_ALGORITHMS='jdk.tls.disabledAlgorithms=SSLv3, RC4, DES, MD5withRSA, \\
    DH keySize < 1024, EC keySize < 224, 3DES_EDE_CBC, anon, NULL, \\
    include jdk.disabled.namedCurves'

perl -i -0777 -pe "s/^(jdk.tls.disabledAlgorithms=.*?(?!\\\n)\n)$/$DISABLED_ALGORITHMS/gms"  /etc/java-11-openjdk/security/java.security
