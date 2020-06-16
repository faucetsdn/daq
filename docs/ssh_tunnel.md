# SSH Tunnel Setup for remote connection to DAQ lab computers

The following procedure configures an SSH tunnel from a local Linux 
computer running DAQ in a debian based distribution to a cloud linux 
virtual machine (VM) running a debian based distribution.

The procedure is divided into four parts:

1. Configuration of the VM in the cloud
2. Configuration of the local DAQ instance computer with `autossh` to open the ssh tunnel to the cloud
3. Transfer of public key from the DAQ instance computer to the VM in the cloud
4. Remote access

# Cloud VM Instance

For the first part, we are configuring a compute engine virtual machine (VM) 
instance in the Google Cloud Platform (GCP) and creating a remote user called `tunnel`.

## Virtual machine setup

1. Head to [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. If you don’t already have a project, create one
3. From the Compute Engine menu select “VM instances”  
4. Create VM instance, selecting Debian 10 Buster as the operating system
5. Set a static IP address for the VM instance - in this example the IP address is indicated as **XXX.XXX.XXX.XXX**
6. Add users on the IAM section of GCP as needed
7. Enable port 22 as a firewall rule

     ```
     cloud_machine$ gcloud compute firewall-rules create default-allow-ssh --allow tcp:22
     ```

8. Run the VM and in case `openssh` is not installed, install `openssh-server`

    ```
    cloud_machine$ sudo apt install openssh-server

    ```

## Creation of the remote `tunnel` user

1. Create the remote `tunnel` user:

    ```
    cloud_machine$ sudo adduser tunnel

    Adding user `tunnel' ...
    Adding new group `tunnel' (1002) ...
    Adding new user `tunnel' (1002) with group `tunnel' ...
    The home directory `/home/tunnel' already exists.  Not copying from `/etc/skel'.
    Enter new UNIX password: 
    Retype new UNIX password: 
    passwd: password updated successfully
    Changing the user information for tunnel
    Enter the new value, or press ENTER for the default
    	Full Name []: Tunnel User
    	Room Number []: 
    	Work Phone []: 
    	Home Phone []: 
    	Other []: 
    Is the information correct? [Y/n] 
    ```

2. Become the `tunnel` user:

    ```
    cloud_machine$ su tunnel
    Password: 
    ```


3. Create an ssh key pair for the `tunnel` user:

    ```
    cloud_machine$ ssh-keygen 

    Generating public/private rsa key pair.
    Enter file in which to save the key (/home/tunnel/.ssh/id_rsa): 
    Created directory '/home/tunnel/.ssh'.
    Enter passphrase (empty for no passphrase): 
    Enter same passphrase again: 
    Your identification has been saved in /home/tunnel/.ssh/id_rsa.
    Your public key has been saved in /home/tunnel/.ssh/id_rsa.pub.
    The key fingerprint is:
    SHA256:Ok1jHOetfMY8p0XwnOvFM9RJND63AF5CdT80C1liGKM tunnel@daq_machine
    The key's randomart image is:
    +---[RSA 2048]----+
    |          .*+*.B |
    |          o.*.B =|
    |        .E.... *o|
    |       . + . +o.B|
    |        S . . =+.|
    |       = o = ..o |
    |          o * +oo|
    |       .   o * .o|
    |            . *  |
    +----[SHA256]-----+

    ```

# DAQ Instance

For the second part, we are creating a new user called `tunnel` 
and then installing autossh to create the ssh-tunnel service on 
the DAQ instance machine.

## Creation of the `tunnel` user on the DAQ instance machine

1. Create the `tunnel` user:

    ```
    daq_machine$ sudo adduser tunnel
    Adding user `tunnel' ...
    Adding new group `tunnel' (1002) ...
    Adding new user `tunnel' (1002) with group `tunnel' ...
    The home directory `/home/tunnel' already exists.  Not copying from `/etc/skel'.
    Enter new UNIX password: 
    Retype new UNIX password: 
    passwd: password updated successfully
    Changing the user information for tunnel
    Enter the new value, or press ENTER for the default
    	Full Name []: Tunnel User
    	Room Number []: 
    	Work Phone []: 
    	Home Phone []: 
    	Other []: 
    Is the information correct? [Y/n] 
    ```

2. Become the `tunnel` user:

    ```
    daq_machine$ su tunnel
    Password: 
    ```


3. Create an ssh key pair for the `tunnel` user:

    ```
    daq_machine$ ssh-keygen 
    Generating public/private rsa key pair.
    Enter file in which to save the key (/home/tunnel/.ssh/id_rsa): 
    Created directory '/home/tunnel/.ssh'.
    Enter passphrase (empty for no passphrase): 
    Enter same passphrase again: 
    Your identification has been saved in /home/tunnel/.ssh/id_rsa.
    Your public key has been saved in /home/tunnel/.ssh/id_rsa.pub.
    The key fingerprint is:
    SHA256:Ok1jHOetfMY8p0XwnOvFM9RJND63AF5CdT80C1liGKM tunnel@daq_machine
    The key's randomart image is:
    +---[RSA 2048]----+
    |          .*+*oB |
    |          o.*.B =|
    |        .E.... *o|
    |       . + . +o.B|
    |        S . . =+.|
    |       = o + ..o |
    |      o . o * +oo|
    |       .   o * .o|
    |            . .  |
    +----[SHA256]-----+

    ```

## Set up of the ssh-tunnel service

1. Install ssh and autossh 

    ```
    daq_machine$ sudo apt install autossh
    ```


2. Edit a new service file for the tunnel connection:

    ```
    daq_machine$ sudo nano /etc/systemd/system/ssh-tunnel.service
    ```


3. Input the following text into the file and save it:


```
[Unit]
Description=AutoSSH tunnel service
After=network-online.target ssh.service

[Service]
Environment="AUTOSSH_GATETIME=0"
ExecStart=/usr/bin/autossh -v -M 0 -N -R 19991:localhost:22 -o "ServerAliveInterval 60" \
   -o "ServerAliveCountMax 3" -o "StrictHostKeyChecking=no" -o "BatchMode=yes" \
   -i /home/tunnel/.ssh/id_rsa  tunnel@XXX.XXX.XXX.XXX
ExecStop=/usr/bin/pkill -9 autossh
TimeoutSec=10
RestartSec=2
Restart=always

[Install]
WantedBy=multi-user.target
```
    After copying and pasting the text above, change the
    <code> <strong>XXX.XXX.XXX.XXX </strong></code>text with the 
    IP address or the hostname of your virtual machine in the cloud.

4. Update `systemctl`

    daq_machine<code>$ <strong>sudo systemctl daemon-reload</strong></code>

5. Enable the new ssh-tunnel service at startup

    daq_machine<code>$ <strong>systemctl enable ssh-tunnel.service</strong> </code>

```
Created symlink /etc/systemd/system/multi-user.target.wants/ssh-tunnel.service → /etc/systemd/system/ssh-tunnel.service.
```

# Transfer of the public key 

Now that the ssh-tunnel service is set up on the DAQ instance machine 
and that the tunnel user is created on the remote machine in the cloud, 
we need to exchange the keys to enable the tunnel to be created 
automatically without user intervention when the DAQ instance machine starts.

1. **On the DAQ instance machine**, show the content of the public key file

    ```
    daq_machine$ sudo cat /home/tunnel/.ssh/id_rsa.pub
    ```

2. This command will display a key similar to the one below (this key has been randomly generated for illustrative purposes only)

    ```
    ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDpaeZ7fsc1PSJrtFswETmmLBke7VFtnydShTEjOfzwhW7hQCmDAsJblrbxLz+9cy8ff+Y3IXLssbclcDdSOqku3i5l9/hC5g9EFXveYO2Z123FYuhays2893+257DY6LjecALicSuhb2CHogaldj8D28FjBmQh6hKJugjhuaTySK361zT3dB9NV9TvYWS8M9jMmbWMZm6loD4vxO7DqteNRHbXAKzD4gtf1XFtKvaPTJfVJEK0sLlpTdQjpMRJB4YyqsUjRJ3qeOeD/SflL60ak4j3TEHoXRSVuRDOQmMzdKhKJfPhCSxZsMGvtdPSkHNXRXRTE1Mhnr3F6k2CxFj5 tunnel@daq_machine_hostname_or_ip_address
    ```


3. **On the remote virtual machine**, copy the content of this public key file and paste it into the authorized_keys file, for instance editing it with `nano`

    ```
    cloud_machine$ nano /home/tunnel/.ssh/authorized_keys
    ```


4. On the DAQ instance machine, start the new ssh-tunnel service

    ```
    daq_machine$ systemctl start ssh-tunnel.service
    ```


5. Check that the new ssh-tunnel service is running on the DAQ instance machine 

    ```
    daq_machine$ systemctl status ssh-tunnel.service 


    ● digital-building.service - AutoSSH tunnel service
       Loaded: loaded (/etc/systemd/system/ssh-tunnel.service; enabled; vendor preset: enabled)
       Active: active (running) since Thu 2020-04-23 14:14:41 BST; 27s ago
     Main PID: 3316 (autossh)
        Tasks: 2 (limit: 4915)
       CGroup: /system.slice/ssh-tunnel.service
               ├─3316 /usr/lib/autossh/autossh -v -M 0 -N -R 19991:localhost:22 -o ServerAliveInterval 60 -o ServerAliveCountMax 3 -o StrictHostKeyChecking=no -o BatchMode=yes -i /home/tunnel/.ssh/id_rsa tunnel@34.66.115.220
               └─3319 /usr/bin/ssh -v -N -R 19991:localhost:22 -o ServerAliveInterval 60 -o ServerAliveCountMax 3 -o StrictHostKeyChecking=no -o BatchMode=yes -i /home/tunnel/.ssh/id_rsa tunnel@digital-building.org

    Apr 23 14:14:41 daq_machine autossh[3316]: Authenticated to digital-building.org ([130.211.66.54]:22).
    Apr 23 14:14:41 daq_machine autossh[3316]: debug1: Remote connections from LOCALHOST:19991 forwarded to local address localhost:22
    Apr 23 14:14:41 daq_machine autossh[3316]: debug1: Requesting no-more-sessions@openssh.com
    Apr 23 14:14:41 daq_machine autossh[3316]: debug1: Entering interactive session.
    Apr 23 14:14:41 daq_machine autossh[3316]: debug1: pledge: network
    Apr 23 14:14:42 daq_machine autossh[3316]: debug1: client_input_global_request: rtype hostkeys-00@openssh.com want_reply 0
    Apr 23 14:14:42 daq_machine autossh[3316]: debug1: Remote: /home/tunnel/.ssh/authorized_keys:8: key options: agent-forwarding port-forwarding pty user-rc x11-forwarding
    Apr 23 14:14:42 daq_machine autossh[3316]: debug1: Remote: /home/tunnel/.ssh/authorized_keys:8: key options: agent-forwarding port-forwarding pty user-rc x11-forwarding
    Apr 23 14:14:42 daq_machine autossh[3316]: debug1: remote forward success for: listen 19991, connect localhost:22
    Apr 23 14:14:42 daq_machine autossh[3316]: debug1: All remote forwarding requests processed
    ```

# Achieving Remote Access

The final step is to login to the cloud virtual machine and check 
that you are able to connect to the DAQ instance machine through 
the ssh tunnel.


```
cloud_machine$ ssh -p 19991 tunnel@localhost
```


You will be prompted to input your user password and then let into 
the local machine from the remote one.

If you need particular permissions to access files and resources 
on the local machine, you can switch to the user with the correct 
permissions and avoid to give too much power to the tunnel user. 
Alternatively you can login directly with the name of the appropriate 
user on the DAQ instance machine.
