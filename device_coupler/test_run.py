from ovs_helper import OvsHelper
from daq_client import DAQClient

import argparse


parser = argparse.ArgumentParser()
parser.add_argument('--target', help = "gRPC target", type = str)
parser.add_argument('--source', help = "Local VxLAN endpoint IP", type = str)
parser.add_argument('--device_mac', help = "Device under test MAC addr", type = str)
parser.add_argument('--device_vlan', help = "Device under test VLAN", type = int)
parser.add_argument('--ovs_br', help = "OVS bridge VxLAN VTEP is to be connected to", type = str)

args = parser.parse_args()
target = args.target
tunnel_ip = args.source
mac = args.device_mac
device_vlan = args.device_vlan
ovs_bridge= args.ovs_br

daq_client = DAQClient(target, tunnel_ip, ovs_bridge)
daq_client.start()
daq_client.process_device_discovery(mac, device_vlan)
