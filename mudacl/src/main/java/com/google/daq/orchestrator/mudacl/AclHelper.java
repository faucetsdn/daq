package com.google.daq.orchestrator.mudacl;

import com.google.daq.orchestrator.mudacl.DeviceTopology.Placement;
import com.google.daq.orchestrator.mudacl.SwitchTopology.Acl;
import com.google.daq.orchestrator.mudacl.SwitchTopology.Rule;

public final class AclHelper {

  public static final String DL_TYPE_IPv4 = "0x0800";
  public static final String DL_TYPE_ARP = "0x0806";
  public static final int IP_PROTO_ICMP = 1;
  public static final int IP_PROTO_TCP = 6;
  public static final int IP_PROTO_UDP = 17;

  public static void addBaselineRules(Acl acl) {
    acl.add(makeIcmpRule());
    acl.add(makeArpRule());
    acl.add(makeDhcpRule());
  }

  public static void addRawRules(Acl acl) {
    acl.add(new Rule("All Allow", true));
  }

  private static Rule makeArpRule() {
    Rule rule = new Rule("ARP Allow", true);
    rule.dl_type = DL_TYPE_ARP;
    return rule;
  }

  private static Rule makeIcmpRule() {
    Rule rule = new Rule("ICMP Allow", true);
    rule.dl_type = DL_TYPE_IPv4;
    rule.nw_proto = IP_PROTO_ICMP;
    return rule;
  }

  private static Rule makeDhcpRule() {
    Rule rule = new Rule("DHCP Allow", true);
    rule.dl_type = DL_TYPE_IPv4;
    rule.nw_proto = IP_PROTO_UDP;
    rule.udp_src = 68;
    rule.udp_dst= 67;
    return rule;
  }

  public static class PortAcl {
    final Placement placement;
    final Acl acl;

    public PortAcl(Placement placement, Acl acl) {
      this.placement = placement;
      this.acl = acl;
    }
  }
}
