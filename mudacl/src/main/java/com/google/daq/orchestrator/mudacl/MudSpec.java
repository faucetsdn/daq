package com.google.daq.orchestrator.mudacl;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public class MudSpec {

  @JsonProperty("ietf-mud:mud")
  MudDescriptor mudDescriptor;

  @JsonProperty("ietf-access-control-list:access-lists")
  AccessLists accessLists;

  static class MudDescriptor {
    @JsonProperty("mud-version")
    public Integer mudVersion;

    @JsonProperty("mud-url")
    public String mudUrl;

    @JsonProperty("last-update")
    public String lastUpdate;

    @JsonProperty("cache-validity")
    public Integer cacheValidity;

    @JsonProperty("is-supported")
    public Boolean isSupported;

    @JsonProperty("systeminfo")
    public String systemInfo;

    @JsonProperty("from-device-policy")
    public DevicePolicy fromDevicePolicy;

    @JsonProperty("to-device-policy")
    public DevicePolicy toDevicePolicy;
  }

  static class DevicePolicy {
    @JsonProperty("access-lists")
    public PolicyLists accessLists;
  }

  static class PolicyLists {
    @JsonProperty("access-list")
    public List<PolicySpec> accessList;
  }

  static class PolicySpec {
    public String name;
  }

  static class AccessLists {
    public List<AclSpec> acl;
  }

  static class AclSpec {
    public String name;
    public String type;
    public AclAces aces;
  }

  static class AclAces {
    public List<AclAce> ace;
  }

  static class AclAce {
    public String name;
    public Matches matches;
    public Actions actions;
  }

  static class Matches {
    @JsonProperty("ietf-mud:mud")
    public MudMatch mud;
    public NwSpec ipv4;
    public NwSpec ipv6;
    public TpSpec tcp;
    public TpSpec udp;
  }

  static class MudMatch {
    public String controller;
  }

  static class NwSpec {
    @JsonProperty("ietf-acldns:src-dnsname")
    public String dnsSrc;
    @JsonProperty("ietf-acldns:dst-dnsname")
    public String dnsDst;
    public Integer protocol;
  }

  static class TpSpec {
    @JsonProperty("ietf-mud:direction-initiated")
    public String directionInitiated;

    @JsonProperty("source-port")
    public PortSpec sourcePort;

    @JsonProperty("destination-port")
    public PortSpec destinationPort;
  }

  static class PortSpec {
    public String operator;
    public Integer port;

    @JsonProperty("lower-port")
    public Integer lowerPort;

    @JsonProperty("upper-port")
    public Integer upperPort;
  }

  static class Actions {
    public String forwarding;
  }
}
