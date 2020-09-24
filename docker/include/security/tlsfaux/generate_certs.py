import subprocess, absolute_filepath

filepath = "/".join(absolute_filepath.script_directory) + "/certs/"

# This may be needed, not sure yet, needs more validation testing
command_rnd = 'touch /root/.rnd'

# Create the ecparam key to allow for DH/DHE/ECDSA ciphers
command_ecparam = 'openssl ecparam -out ' + filepath + 'ecparam.pem -name prime256v1'

# Create a CA Root Key
command_ca_key = 'openssl genpkey -paramfile ' + filepath + 'ecparam.pem -out ' + filepath + 'CA_Faux.key' 

# Create and self sign the root Certificat e
command_ca_crt = 'openssl req -x509 -new -key ' + filepath + 'CA_Faux.key -out ' + filepath + 'CA_Faux.pem -subj "/DC=DAQ/C=US/ST=MountainView/L=KingsX/O=DAQ/OU=Software/CN=DAQ CA Root"'



# Create the intermediate key
# command_int_key ='openssl genrsa -out ' + filepath +'intermediate.key 4096'

# Create an intermediate key and csr
# command_int_key_csr = 'openssl req -nodes -newkey rsa:2048 -keyout ' + filepath + 'intermediate.key -out ' + filepath + 'intermediate.csr -subj "/C=US/ST=MountainView/L=KingsX/O=DAQ/OU=Software/CN=DAQ Intermediate"'

# Generate the intermediate using the csr and sign with the CA Root key
# command_int_cert = 'openssl x509 -req -in ' + filepath + 'intermediate.csr -CA ' + filepath + 'CA_Faux.pem -CAkey ' + filepath + 'CA_Faux.key -CAcreateserial -out ' + filepath + 'intermediate.pem -days 500 -sha256'



# Create a server private key
command_server_key = 'openssl genpkey -paramfile ' + filepath + 'ecparam.pem -out ' + filepath + 'server.key'  

# Create a server csr
command_server_csr = 'openssl req -nodes -newkey ec:'+ filepath + 'ecparam.pem -keyout ' + filepath + 'server.key -out ' + filepath + 'server.csr -subj "/C=US/ST=MountainView/L=KingsX/O=DAQ/OU=Software/CN=127.0.0.1"'

# Generate the server cert using the csr and sign with the CA Root key
command_server_cert = 'openssl x509 -req -in ' + filepath + 'server.csr -CA ' + filepath + 'CA_Faux.pem -CAkey ' + filepath + 'CA_Faux.key -CAcreateserial -out ' + filepath + 'server.crt -days 500 -sha256'

# Generate the certificate using the csr and sign with the Intermediate Root key
# command_cert = 'openssl x509 -req -in ' + filepath + 'server.csr -CA ' + filepath + 'intermediate.pem -CAkey ' + filepath + 'intermediate.key -CAcreateserial -out ' + filepath + 'server.pem -days 500 -sha256'


# Combine the CA and root into one cert
# command_combine = 'cat ' + filepath + 'server.pem ' + filepath + 'CA_Faux.pem > ' + filepath + 'server.crt'


def run_shell_command(command):
    process = subprocess.Popen(command, universal_newlines=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    text = process.stdout.read()
    retcode = process.wait()
    if len(text) > 0:
        print(text)

run_shell_command(command_rnd)  
run_shell_command(command_ecparam)  

run_shell_command(command_ca_key)
run_shell_command(command_ca_crt)

run_shell_command(command_server_key)
run_shell_command(command_server_csr)
run_shell_command(command_server_cert)
