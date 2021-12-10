from ovs_helper import OvsHelper
from device_report_client import DeviceReportClient

import argparse

"""
vxlan_params = {
    'port': 0,
    'remote_ip': '192.168.9.2',
    'vni': 1,
    'local_ip': '10.1.1.1/24'
}

ovs_helper = OvsHelper()

#iface = ovs_helper.create_vxlan_endpoint(**vxlan_params)
#print(iface)
def add_devices_to_br(bridge, num_devices):
    for index in range(1, num_devices+1):
        ovs_helper.create_faux_device(index)
        iface = "faux-%s" % index
        ovs_helper.add_iface_to_bridge(bridge, iface)
        ovs_helper.set_native_vlan(iface, 200+index*10)

bridge = 'br0'
ovs_helper.create_ovs_bridge(bridge)
add_devices_to_br(bridge, 3)
ovs_helper.create_faux_device(4)
ovs_helper.add_iface_to_bridge(bridge, 'faux-4')
ovs_helper.set_trunk_vlan('faux-4', [220, 210])
"""

parser = argparse.ArgumentParser()
parser.add_argument('--target', help = "gRPC target", type = str)
parser.add_argument('--source', help = "Local VxLAN endpoint IP", type = str)
parser.add_argument('--device_mac', help = "Device under test MAC addr", type = str)
parser.add_argument('--device_vlan', help = "Device under test VLAN", type = int)
parser.add_argument('--ovs_br', help = "OVS bridge VxLAN VTEP is to be connected to", type = str)

args = parser.parse_args()
target = args.target #"172.17.0.1:50051"
tunnel_ip = args.source #"172.17.0.2"
mac = args.device_mac #"9a:02:57:1e:8f:01"
device_vlan = args.device_vlan #210
assigned_vlan = 0
ovs_bridge= args.ovs_br #"br0"

daq_client = DeviceReportClient(target, tunnel_ip, ovs_bridge)
daq_client.start()
daq_client.process_device_discovery(mac, device_vlan, assigned_vlan)
