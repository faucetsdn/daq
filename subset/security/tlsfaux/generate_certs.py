import subprocess, absolute_filepath

filepath = "/".join(absolute_filepath.script_directory) + "/certs/"

command_key = 'openssl req -nodes -newkey rsa:2048 -keyout ' + filepath + 'server.key -out ' + filepath + 'server.csr -subj "/C=GB/ST=London/L=KingsX/O=ExcelRedstone/OU=Software/CN=127.0.0.1"'
command_cert ='openssl x509 -req -days 365 -in ' + filepath + 'server.csr -signkey ' + filepath + 'server.key -out ' + filepath + 'server.crt'

def run_shell_command(command):
    process = subprocess.Popen(command, universal_newlines=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    text = process.stdout.read()
    retcode = process.wait()
    if len(text) > 0:
        print(text)

run_shell_command(command_key)
run_shell_command(command_cert)
