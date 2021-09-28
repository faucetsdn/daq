import sys
from shunt.vxlan_over_ssh import build_vxlan_ssh_conn, build_bidirectional_ssh_tunnel

CONN_PARAMS = {
    'virt_if_name': 'ep0',
    'ssh_in_port': '30001',
    'ssh_out_port': '30000',
    'vni': '0'
}

CONN_PARAMS_CLIENT = {
    'virt_if_ip': '192.168.21.2',
    'remote_ip': '192.168.21.1',
    'vxlan_if_ip': '192.168.1.2'
}
CONN_PARAMS_CLIENT.update(CONN_PARAMS)

CONN_PARAMS_SERVER = {
    'virt_if_ip': '192.168.21.1',
    'remote_ip': '192.168.21.2',
    'vxlan_if_ip': '192.168.1.1'
}
CONN_PARAMS_SERVER.update(CONN_PARAMS)


if sys.argv[1] == 'client':
    print('params:', CONN_PARAMS_CLIENT)
    build_bidirectional_ssh_tunnel(
        CONN_PARAMS['ssh_in_port'], CONN_PARAMS['ssh_out_port'], 'shunt_host_server_1')
    build_vxlan_ssh_conn(CONN_PARAMS_CLIENT)
elif sys.argv[1] == 'server':
    print('params:', CONN_PARAMS_SERVER)
    build_vxlan_ssh_conn(CONN_PARAMS_SERVER)
