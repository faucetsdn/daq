#!/bin/bash -e

# Quick script to fire up test server for local device testing.

RESULT=$1

set_password () {
    echo $1 | chpasswd
}

set_up_valid_certificates () {
    echo Generating tls certs.
    python tlsfaux/generate_certs.py
    echo Starting tls server on port 443 https.
    mv nginxpass.conf /etc/nginx/nginx.conf
    service nginx start
}

set_up_invalid_certificates () {
    echo Starting expired tls server on port 443 https.
    mv nginxfail.conf /etc/nginx/nginx.conf
    service nginx start
}

set_up_telnet () {
    /etc/init.d/openbsd-inetd restart
    service xinetd start
}

set_up_ssh () {
    /usr/sbin/sshd -D &
    service ssh start
}

switch_off_all_servers () {
    /etc/init.d/openbsd-inetd stop
    service xinetd stop
    service ssh stop
    service nginx stop
}

# PASS result means: All servers on, tls certificates valid, passwords changed from default.
if [ "$RESULT" == "pass" ]; then
    set_password 'root:pass'
    htpasswd -b -c /etc/nginx/.htpasswd admin fail
    set_up_telnet
    set_up_ssh
    set_up_valid_certificates

# FAIL result means: All servers on, tls certificates invalid, passwords not changed from default.
elif [ "$RESULT" == "fail" ]; then
    set_password 'root:default'
    echo "pass\npass\n\n\n\n\n\ny\n" | adduser "admin"
    echo "admin:default" | chpasswd
    htpasswd -b -c /etc/nginx/.htpasswd admin default
    set_up_telnet
    set_up_ssh
    set_up_invalid_certificates

# SKIP result means: All servers off, tls certificates not generated.
elif [ "$RESULT" == "skip" ]; then
    echo "No services started."
fi

# Keep the container from exiting.
echo Blocking for all eternity.
tail -f /dev/null
