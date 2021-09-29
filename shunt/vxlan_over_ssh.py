"""Module to build VxLAN tunnels over SSH tunnels using shell commands"""

from __future__ import absolute_import
from shunt.shell_command_helper import ShellCommandHelper


def build_ssh_tunnel(ssh_in_port, ssh_out_port, remote_host, reverse=False):
    """
    Args:
        ssh_in_port: Destination port for tunnel
        ssh_out_port: Source port for tunnel
        remote_host: Remote host IP
        reverse: Boolean. Creates reverse forwarding tunnel if True.
    Returns: None
    """
    shellcmd = ShellCommandHelper()
    direction = 'R' if reverse else 'L'
    shellcmd.run_cmd("ssh -o StrictHostKeyChecking=no -%s %s:127.0.0.1:%s -N -f %s"
                     % (direction, ssh_out_port, ssh_in_port, remote_host))


def build_bidirectional_ssh_tunnel(ssh_in_port, ssh_out_port, remote_host):
    """
    Args:
        ssh_in_port: Incoming traffice port
        ssh_out_port: Outgoing traffic port
        remote_host: Remote host IP
    Returns: None
    """
    build_ssh_tunnel(ssh_in_port, ssh_out_port, remote_host, reverse=False)
    build_ssh_tunnel(ssh_in_port, ssh_out_port, remote_host, reverse=True)


def create_virtual_if(if_name, if_ip):
    """
    Args:
        if_name: interface name
        if_ip: interface IP
    Returns: None
    """
    shellcmd = ShellCommandHelper()
    shellcmd.run_cmd("sudo ip link add %s type dummy" % (if_name))
    shellcmd.run_cmd("sudo ip addr add %s/24 dev %s" % (if_ip, if_name))
    shellcmd.run_cmd("sudo ip link set %s up" % (if_name))


def socat_tcp_to_udp(src_port, dst_port):
    """
    Socat command to map TCP port to UDP port
    Args:
        src_port: Source TCP port
        dst_port: Destination UDP port
    Returns: None
    """
    shellcmd = ShellCommandHelper()
    shellcmd.run_cmd("socat -T15 tcp4-listen:%s,reuseaddr,fork udp:localhost:%s"
                     % (src_port, dst_port), detach=True)


def socat_udp_to_tcp(src_port, dst_port):
    """
    Socat command to map UDP port to TCP port
    Args:
        src_port: Source UDP port
        dst_port: Destincation TCP port
    Returns: None
    """
    shellcmd = ShellCommandHelper()
    shellcmd.run_cmd("socat -T15 udp4-listen:%s,reuseaddr,fork tcp:localhost:%s"
                     % (src_port, dst_port), detach=True)


def iptables_udp_change_source(dst_ip, dst_port, src_ip_port):
    """
    iptables command to change source IP/ports of UDP packets
    Args:
        dst_ip: Destination IP of packet to be changed
        dst_port: Destination port of packet to be changed
        src_ip_port: <source_ip_to_be_added>:<source port range> e.g. 192.168.1.2:38000-45000
    Returns: None
    """
    shellcmd = ShellCommandHelper()
    shellcmd.run_cmd(
        "sudo iptables -t nat -A POSTROUTING -p udp -d %s --dport %s -j SNAT --to-source %s"
        % (dst_ip, dst_port, src_ip_port))


def iptables_udp_divert_iface_traffic(iface, dst_port, target_dst_port):
    """
    iptables command to divert udp traffic egressing from an interface to a different port
    Args:
        iface: Interface packets are egressign from
        dst_port: Destination port of packets to be diverted
        target_dst_port: Destination port packets are diverted to
    Returns: None
    """
    shellcmd = ShellCommandHelper()
    shellcmd.run_cmd(
        "sudo iptables -t nat -A OUTPUT -o %s -p udp --dport %s -j REDIRECT --to-ports %s"
        % (iface, dst_port, target_dst_port))


def create_vxlan_tunnel(vni, remote_ip, vxlan_port, vtep_ip):
    """
    Method to create a VxLAN tunnel and assign an IP to the VTEP
    Args:
        vni: VNI of tunnel to be created
        remote_ip: Remote IP address for underlay network
        vxlan_port: Remote destination port for VxLAN tunnel
    Returns: None
    """
    shellcmd = ShellCommandHelper()
    shellcmd.run_cmd(
        "sudo ip link add vxlan type vxlan id %s remote %s dstport %s srcport %s %s nolearning"
        % (vni, remote_ip, vxlan_port, vxlan_port, vxlan_port))
    shellcmd.run_cmd("sudo ip addr add %s/24 dev vxlan" % (vtep_ip))
    shellcmd.run_cmd("sudo ip link set vxlan up")


def build_vxlan_ssh_conn(conn_params):
    """
    Args:
        conn_params: JSON. Format:{  # TODO: Turn into a proto for easy config exchange.
                virt_if_name: Interface name of virtual interface for underlay n/w
                virt_if_ip: IP for virtual interface
                ssh_in_port: Port for incoming traffic
                ssh_out_port: Port for outgoing traffic
                remote_ip: Remote IP of underlay n/w
                vni: VxLAN identifier
                vxlan_if_ip: VxLAN interface IP
        }
    Returns: None
    """
    VXLAN_PORT = '4789'
    LOCAL_HOST = '127.0.0.1'
    VXLAN_SOURCE_PORT_RANGE = "38000-45000"
    INTERMEDIATE_PORT = "20000"
    create_virtual_if(conn_params['virt_if_name'], conn_params['virt_if_ip'])
    socat_tcp_to_udp(conn_params['ssh_in_port'], VXLAN_PORT)
    source_ip_port = conn_params['remote_ip'] + ":" + VXLAN_SOURCE_PORT_RANGE
    iptables_udp_change_source(LOCAL_HOST, VXLAN_PORT, source_ip_port)
    iptables_udp_divert_iface_traffic(conn_params['virt_if_name'], VXLAN_PORT, INTERMEDIATE_PORT)
    socat_udp_to_tcp(INTERMEDIATE_PORT, conn_params['ssh_out_port'])
    create_vxlan_tunnel(
        conn_params['vni'], conn_params['remote_ip'], VXLAN_PORT, conn_params['vxlan_if_ip'])
