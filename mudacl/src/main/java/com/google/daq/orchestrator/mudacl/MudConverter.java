package com.google.daq.orchestrator.mudacl;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.daq.orchestrator.mudacl.DeviceTopology.MacIdentifier;
import com.google.daq.orchestrator.mudacl.DeviceTypes.DeviceClassifier;
import com.google.daq.orchestrator.mudacl.MudSpec.AccessLists;
import com.google.daq.orchestrator.mudacl.MudSpec.AclAce;
import com.google.daq.orchestrator.mudacl.MudSpec.AclSpec;
import com.google.daq.orchestrator.mudacl.MudSpec.DevicePolicy;
import com.google.daq.orchestrator.mudacl.MudSpec.Matches;
import com.google.daq.orchestrator.mudacl.MudSpec.PolicySpec;
import com.google.daq.orchestrator.mudacl.MudSpec.PortSpec;
import com.google.daq.orchestrator.mudacl.MudSpec.TpSpec;
import com.google.daq.orchestrator.mudacl.SwitchTopology.Ace;
import com.google.daq.orchestrator.mudacl.SwitchTopology.Acl;
import com.google.daq.orchestrator.mudacl.SwitchTopology.Rule;
import java.io.File;
import java.net.Inet4Address;
import java.net.UnknownHostException;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

public class MudConverter implements AclProvider {

  private static final String MUD_FILE_FORMAT = "%s.json";
  private static final String FROM_DEVICE_POLICY = "from-device";
  private static final String TO_DEVICE_POLICY = "to-device";
  private static final String PORT_MATCH_OPERATOR = "eq";
  private static final String EDGE_DEVICE_DESCRIPTION_FORMAT = "MUD %s %s";
  private static final String JSON_SUFFIX = ".json";
  private static final String DNS_TEMPLATE_FORMAT = "@dns:%s";
  private static final String MUD_FILE_SUFFIX = ".json";

  private final File rootPath;

  private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

  MudConverter(File rootPath) {
    if (!rootPath.isDirectory()) {
      throw new IllegalArgumentException(
          "Missing mud root directory " + rootPath.getAbsolutePath());
    }
    this.rootPath = rootPath;
  }

  @Override
  public List<String> targetTypes() {
    return Arrays.stream(rootPath.listFiles())
        .filter(this::isMudFile)
        .map(this::getTargetType)
        .collect(Collectors.toList());
  }

  private boolean isMudFile(File file) {
    return file.getName().endsWith(MUD_FILE_SUFFIX);
  }

  private String getTargetType(File mudFile) {
    String filename = mudFile.getName();
    if (!filename.endsWith(JSON_SUFFIX)) {
      throw new IllegalArgumentException("Unexpected filename suffix on " + mudFile.getAbsolutePath());
    }
    return filename.substring(0, filename.length() - JSON_SUFFIX.length());
  }

  @Override
  public Acl makeEdgeAcl(MacIdentifier srcDev, DeviceClassifier device) {
    Acl acl = device == null ? makeUnknownEdgeAcl(srcDev) : makeFromEdgeAcl(device);
    for (Ace ace : acl) {
      ace.rule.dl_src = srcDev.toString();
    }
    return acl;
  }

  private Acl makeFromEdgeAcl(DeviceClassifier device) {
    Acl acl = makeFromAcl(getMudSpec(device), device.isTemplate);
    for (Ace ace : acl) {
      ace.rule.description = String.format(
          EDGE_DEVICE_DESCRIPTION_FORMAT, device.type, ace.rule.description);
    }
    return acl;
  }

  private Acl makeFromAcl(MudSpec mudSpec, boolean isTemplate) {
    return expandAcl(mudSpec.mudDescriptor.fromDevicePolicy, mudSpec.accessLists, isTemplate);
  }

  private Acl expandAcl(DevicePolicy devicePolicy, AccessLists accessLists, boolean isTemplate) {
    Acl acl = new Acl();
    if (devicePolicy != null) {
      for (PolicySpec policySpec : devicePolicy.accessLists.accessList) {
        AclSpec aclSpec = getAclSpec(accessLists, policySpec);
        for (AclAce aclAce : aclSpec.aces.ace) {
          acl.add(makeAclRule(aclAce, isTemplate));
        }
      }
    }
    return acl;
  }

  private Rule makeAclRule(AclAce aclAce, boolean isTemplate) {
    boolean accept = aclAce.actions.forwarding.equals("accept");
    if (!accept && !aclAce.actions.forwarding.equals("drop")) {
      throw new IllegalArgumentException(
          "Unrecognized forwarding clause " + aclAce.actions.forwarding);
    }

    Rule rule = new Rule(aclAce.name, accept);
    Matches matches = aclAce.matches;
    if (matches.ipv4 == null) {
      throw new IllegalArgumentException("Missing ipv4 match criteria");
    }
    rule.dl_type = AclHelper.DL_TYPE_IPv4;
    Integer protocol = matches.ipv4.protocol;
    if (protocol != AclHelper.IP_PROTO_TCP && protocol != AclHelper.IP_PROTO_UDP) {
      throw new IllegalArgumentException("IP protocol not supported " + protocol);
    }
    rule.nw_proto = protocol;
    // TODO: Make this a template.
    String dnsDst = matches.ipv4.dnsDst;
    rule.nw_dst = dnsDst == null
        ? null
        : isTemplate
            ? String.format(DNS_TEMPLATE_FORMAT, dnsDst)
            : resolveIpv4Dst(dnsDst);
    rule.tcp_dst = resolveTcpDst(matches.tcp);
    rule.tcp_src = resolveTcpSrc(matches.tcp);
    rule.udp_src = matches.udp == null ? null : resolveUdpPort(matches.udp.sourcePort);
    rule.udp_dst = matches.udp == null ? null : resolveUdpPort(matches.udp.destinationPort);
    return rule;
  }

  private Integer resolveUdpPort(PortSpec portSpec) {
    if (portSpec == null) {
      return null;
    }
    if (!PORT_MATCH_OPERATOR.equals(portSpec.operator)) {
      throw new IllegalArgumentException("Invalid port operator " + portSpec.operator);
    }
    return portSpec.port;
  }

  private Integer resolveTcpDst(TpSpec tcp) {
    if (tcp == null || !FROM_DEVICE_POLICY.equals(tcp.direction)) {
      return null;
    }
    return tcp.destinationPort.port;
  }

  private Integer resolveTcpSrc(TpSpec tcp) {
    if (tcp == null || !TO_DEVICE_POLICY.equals(tcp.direction)) {
      return null;
    }
    return tcp.sourcePort.port;
  }

  private String resolveIpv4Dst(String dnsDst) {
    try {
      if (dnsDst == null) {
        return null;
      }
      return Inet4Address.getByName(dnsDst).getHostAddress();
    } catch (UnknownHostException e) {
      throw new RuntimeException("Could not resolve hostname " + dnsDst);
    }
  }

  private AclSpec getAclSpec(AccessLists accessLists, PolicySpec policySpec) {
    for (AclSpec aclSpec : accessLists.acl) {
      if (policySpec.name.equals(aclSpec.name)) {
        return aclSpec;
      }
    }
    throw new IllegalArgumentException("Acl policy not found: " + policySpec);
  }

  private MudSpec getMudSpec(DeviceClassifier device) {
    try {
      File mudFile = new File(rootPath, String.format(MUD_FILE_FORMAT, device.type));
      return OBJECT_MAPPER.readValue(mudFile, MudSpec.class);
    } catch (Exception e) {
      throw new RuntimeException("While looking up mud type " + device.type, e);
    }
  }

  private Acl makeUnknownEdgeAcl(MacIdentifier mac) {
    Acl acl = new Acl();
    Rule rule = new Rule("Block " + mac, false);
    acl.add(rule);
    return acl;
  }
}
