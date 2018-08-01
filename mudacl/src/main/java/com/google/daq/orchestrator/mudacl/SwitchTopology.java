package com.google.daq.orchestrator.mudacl;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;

public class SwitchTopology {

  public Map<String, DataPlane> dps = new TreeMap<>();
  public Map<String, VLan> vlans = new TreeMap<>();
  public Map<String, Acl> acls = new TreeMap<>();
  @JsonProperty("include-optional")
  public List<String> includeOptional;
  public List<String> include;

  static class DataPlane {
    public String dp_id;
    public String name;
    public String hardware;
    public Stack stack;
    public String ofchannel_log;
    public Integer timeout;
    public Integer arp_neighbor_timeout;
    public Map<String, Interface> interface_ranges = new TreeMap<>();
    public Map<Integer, Interface> interfaces = new TreeMap<>();
  }

  static class Stack {
    public String dp;
    public Integer port;
    public String priority;
  }

  static class Interface {
    public String description;
    public String native_vlan;
    public String unicast_flood;
    public Set<String> tagged_vlans;
    public String acl_in;
    public Stack stack;
    public List<Integer> mirror;
    public String output_only;
  }

  static class VLan {
    public String description;
    public Integer max_hosts;
  }

  static class Acl extends ArrayList<Ace> {
    public void add(Rule rule) {
      add(new Ace(rule));
    }
  }

  static class Ace {
    public Rule rule;

    public Ace() {
    }

    public Ace(Rule rule) {
      this.rule = rule;
    }

    @Override
    public boolean equals(Object other) {
      return other instanceof Ace && rule.equals(((Ace) other).rule);
    }
  }

  static class Actions {
    public Integer allow;
    public String mirror;
    public Output output;

    @Override
    public boolean equals(Object other) {
      if (other instanceof Actions) {
        Actions otherActions = (Actions) other;
        return Objects.equals(allow, otherActions.allow) &&
            Objects.equals(mirror, otherActions.mirror) &&
            Objects.equals(output, otherActions.output);
      }
      return false;
    }
  }

  static class Output extends HashMap<String, String> {
  }

  static class Rule {
    public String description;
    public String cookie;
    public String dl_type;
    public String dl_src;
    public String dl_dst;
    public Integer nw_proto;
    public String nw_src;
    public String nw_dst;
    public Integer tcp_src;
    public Integer tcp_dst;
    public Integer udp_src;
    public Integer udp_dst;
    public String vlan_vid;
    public Actions actions = new Actions();

    public Rule() {
    }

    public Rule(String description, boolean allow) {
      this.description = description;
      actions.allow = allow ? 1 : 0;
    }

    @Override
    public boolean equals(Object other) {
      if (!(other instanceof Rule)) {
        return false;
      }
      Rule otherRule = (Rule) other;
      return Objects.equals(dl_type, otherRule.dl_type) &&
          Objects.equals(dl_src, otherRule.dl_src) &&
          Objects.equals(dl_dst, otherRule.dl_dst) &&
          Objects.equals(nw_proto, otherRule.nw_proto) &&
          Objects.equals(nw_src, otherRule.nw_src) &&
          Objects.equals(nw_dst, otherRule.nw_dst) &&
          Objects.equals(tcp_src, otherRule.tcp_src) &&
          Objects.equals(tcp_dst, otherRule.tcp_dst) &&
          Objects.equals(udp_src, otherRule.udp_src) &&
          Objects.equals(udp_dst, otherRule.udp_dst);
    }

    public boolean matches(Rule otherRule) {
      return (dl_type == null || dl_type.equals(otherRule.dl_type)) &&
          (dl_src == null || dl_src.equals(otherRule.dl_src)) &&
          (dl_dst == null || dl_dst.equals(otherRule.dl_dst)) &&
          (nw_proto == null || nw_proto.equals(otherRule.nw_proto)) &&
          (nw_src == null || nw_src.equals(otherRule.nw_src)) &&
          (nw_dst == null || nw_dst.equals(otherRule.nw_dst)) &&
          (tcp_src == null || tcp_src.equals(otherRule.tcp_src)) &&
          (tcp_dst == null || tcp_dst.equals(otherRule.tcp_dst)) &&
          (udp_src == null || udp_src.equals(otherRule.udp_src)) &&
          (udp_dst == null || udp_dst.equals(otherRule.udp_dst));
    }
  }
}
