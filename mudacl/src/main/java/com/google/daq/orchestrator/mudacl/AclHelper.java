package com.google.daq.orchestrator.mudacl;

import com.google.daq.orchestrator.mudacl.DeviceTopology.Placement;
import com.google.daq.orchestrator.mudacl.SwitchTopology.Acl;
import com.google.daq.orchestrator.mudacl.SwitchTopology.Rule;

final class AclHelper {

  static final String DL_TYPE_IPv4 = "0x0800";
  static final Integer NW_PROTO_TCP = 6;
  static final Integer NW_PROTO_UDP = 17;
  static final Integer UDP_NTP_PORT = 123;
  static final Integer UDP_DNS_PORT = 53;
  static final Integer TCP_DNS_PORT = 53;
  static final Integer UDP_DHCP_SERVER_PORT = 67;
  static final Integer UDP_DHCP_CLIENT_PORT = 68;

  private static final String DL_TYPE_ARP = "0x0806";
  private static final int IP_PROTO_ICMP = 1;
  private static final String DL_BROADCAST = "ff:ff:ff:ff:ff:ff";

  static void addBaselineRules(Acl acl) {
    acl.add(icmpAllow());
    acl.add(arpAllow());
    acl.add(dhcpAllow());
    acl.add(dnsAllow());
    acl.add(dhcpBcast());
  }

  static void addRawRules(Acl acl) {
    acl.add(dhcpBcast());
  }

  private static Rule dhcpBcast() {
    Rule rule = new Rule("DHCP Broadcast", true);
    rule.dl_type = DL_TYPE_IPv4;
    rule.nw_proto = NW_PROTO_UDP;
    rule.dl_dst = DL_BROADCAST;
    rule.udp_src = AclHelper.UDP_DHCP_CLIENT_PORT;
    rule.udp_dst= AclHelper.UDP_DHCP_SERVER_PORT;
    return rule;
  }

  private static Rule arpAllow() {
    Rule rule = new Rule("ARP Allow", true);
    rule.dl_type = DL_TYPE_ARP;
    return rule;
  }

  private static Rule icmpAllow() {
    Rule rule = new Rule("ICMP Allow", true);
    rule.dl_type = DL_TYPE_IPv4;
    rule.nw_proto = IP_PROTO_ICMP;
    return rule;
  }

  private static Rule dhcpAllow() {
    Rule rule = new Rule("DHCP Allow", true);
    rule.dl_type = DL_TYPE_IPv4;
    rule.nw_proto = NW_PROTO_UDP;
    rule.udp_src = AclHelper.UDP_DHCP_CLIENT_PORT;
    rule.udp_dst= AclHelper.UDP_DHCP_SERVER_PORT;
    return rule;
  }

  private static Rule dnsAllow() {
    Rule rule = new Rule("DNS Allow", true);
    rule.dl_type = DL_TYPE_IPv4;
    rule.nw_proto = NW_PROTO_UDP;
    rule.udp_dst= AclHelper.UDP_DNS_PORT;
    return rule;
  }

  static class PortAcl {
    final Placement placement;
    final Acl edgeAcl;
    final Acl upstreamAcl;

    PortAcl(Placement placement) {
      this.placement = placement;
      this.edgeAcl = new Acl();
      this.upstreamAcl = new Acl();
    }
  }
}
