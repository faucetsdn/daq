package com.google.daq.orchestrator.mudacl;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.daq.orchestrator.mudacl.DeviceTopology.MacIdentifier;
import com.google.daq.orchestrator.mudacl.DeviceTypes.Controller;
import com.google.daq.orchestrator.mudacl.DeviceTypes.DeviceClassifier;
import com.google.daq.orchestrator.mudacl.MudAclGenerator.ExceptionMap;
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
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.stream.Collectors;

public class MudConverter implements AclProvider {

  private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

  private static final String MUD_FILE_FORMAT = "%s.json";
  private static final String FROM_DEVICE_POLICY = "from-device";
  private static final String TO_DEVICE_POLICY = "to-device";
  private static final String PORT_MATCH_EQ_OPERATOR = "eq";
  private static final String EDGE_DEVICE_DESCRIPTION_FORMAT = "type %s rule %s";
  private static final String JSON_SUFFIX = ".json";
  private static final String DNS_TEMPLATE_FORMAT = "@dns:%s";
  private static final String CONTROLER_PREFIX = "@ctrl:";
  private static final String CONTROLLER_TEMPLATE_FORMAT = CONTROLER_PREFIX + "%s";
  private static final String MUD_FILE_SUFFIX = ".json";
  private static final String ACL_TYPE_ERROR_FORMAT = "type was %s, expected ipv4-acl-type";
  private static final String TEST_DNS_NAME = "unit.test.address";
  private static final String TEST_IP_ADDRESS = "127.0.1.1";

  private final File rootPath;

  private DeviceTypes deviceTypes;
  private Map<String, String> hostLookup = new HashMap<>();

  MudConverter(File rootPath) {
    if (!rootPath.isDirectory()) {
      throw new IllegalArgumentException(
          "Missing mud root directory " + rootPath.getAbsolutePath());
    }
    this.rootPath = rootPath;
  }

  @Override
  public void setDeviceTypes(DeviceTypes deviceTypes) {
    this.deviceTypes = deviceTypes;
    deviceTypes.macAddrs.values().stream()
        .filter(device -> device.hostname != null)
        .forEach(device -> {
          if (hostLookup.put(device.hostname, device.ipAddr) != null) {
            throw new RuntimeException("Duplicate hosts specified for host " + device.hostname);
          }
        });
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
  public Acl makeEdgeAcl(DeviceClassifier device, MacIdentifier edgeDevice) {
    Acl acl = device == null ? makeUnknownEdgeAcl(edgeDevice) : makeEdgeAcl(device);
    List<Ace> toRemove = new ArrayList<>();
    for (Ace ace : acl) {
      ace.rule.dl_src = edgeDevice.toString();
      if (!device.isTemplate) {
        if (!maybeResolveControllerDst(ace.rule, edgeDevice) &&
            !maybeResolveControllerSrc(ace.rule, edgeDevice)) {
          toRemove.add(ace);
        }
      }
    }
    for (Ace ace : toRemove) {
      acl.remove(ace);
    }
    return acl;
  }

  private boolean maybeResolveControllerDst(Rule rule, MacIdentifier edgeDevice) {
    rule.nw_dst = maybeResolveController(rule.nw_dst, edgeDevice);
    return rule.nw_dst != null;
  }

  private boolean maybeResolveControllerSrc(Rule rule, MacIdentifier edgeDevice) {
    rule.nw_src = maybeResolveController(rule.nw_src, edgeDevice);
    return rule.nw_src != null;
  }

  private String maybeResolveController(String nwEntry, MacIdentifier edgeDevice) {
    if (nwEntry == null || !nwEntry.startsWith(CONTROLER_PREFIX)) {
      return nwEntry;
    }
    DeviceClassifier deviceClassifier = deviceTypes.macAddrs.get(edgeDevice);
    if (deviceClassifier == null) {
      throw new RuntimeException("Missing device mapping for " + edgeDevice);
    }
    String controllerName = nwEntry.substring(CONTROLER_PREFIX.length());
    List<String> targets = new ArrayList<>();
    Controller controller = deviceClassifier.controllers.get(controllerName);
    if (controller == null) {
      return null;
    }
    controller.controlees.forEach((key, value) -> targets.add(value.hostname));
    if (targets.size() > 1) {
      throw new RuntimeException("Multiple controllers not supported for " + edgeDevice);
    }
    if (targets.size() == 0) {
      return null;
    }
    return hostLookup.get(targets.get(0)).toString();
  }

  private Acl makeEdgeAcl(DeviceClassifier device) {
    try {
      MudSpec mudSpec = getMudSpec(device);
      Acl acl = expandAcl(mudSpec.mudDescriptor.fromDevicePolicy, mudSpec.accessLists,
          device.isTemplate, true);
      for (Ace ace : acl) {
        ace.rule.description = String.format(
            EDGE_DEVICE_DESCRIPTION_FORMAT, device.type, ace.rule.description);
      }
      return acl;
    } catch (Exception e) {
      throw new RuntimeException("While processing edge acl for " + device.type, e);
    }
  }

  @Override
  public Acl makeUpstreamAcl(DeviceClassifier device, MacIdentifier edgeDevice) {
    Acl acl = device == null ? makeUnknownEdgeAcl(edgeDevice) : makeUpstreamAcl(device);
    for (Ace ace : acl) {
      ace.rule.dl_dst = edgeDevice.toString();
    }
    return acl;
  }

  private Acl makeUpstreamAcl(DeviceClassifier device) {
    try {
      MudSpec mudSpec = getMudSpec(device);
      Acl acl = expandAcl(mudSpec.mudDescriptor.toDevicePolicy, mudSpec.accessLists,
          device.isTemplate, false);
      for (Ace ace : acl) {
        ace.rule.description = String.format(
            EDGE_DEVICE_DESCRIPTION_FORMAT, device.type, ace.rule.description);
      }
      return acl;
    } catch (Exception e) {
      throw new RuntimeException("While processing upstream acl for " + device.type, e);
    }
  }

  private Acl expandAcl(DevicePolicy devicePolicy, AccessLists accessLists, boolean isTemplate,
      boolean isEdge) {
    Acl acl = new Acl();
    Map<String, Exception> errors = new TreeMap<>();
    if (devicePolicy != null) {
      for (PolicySpec policySpec : devicePolicy.accessLists.accessList) {
        AclSpec aclSpec = getAclSpec(accessLists, policySpec);
        for (AclAce aclAce : aclSpec.aces.ace) {
          try {
            acl.add(makeAclRule(aclAce, isTemplate, isEdge));
          } catch (Exception e) {
            errors.put(String.format("%s/%s", policySpec.name, aclAce.name), e);
          }
        }
      }
    }
    if (!errors.isEmpty()) {
      String description = errors.size() + " ACL errors";
      throw new ExceptionMap(description, errors);
    }
    return acl;
  }

  private Rule makeAclRule(AclAce aclAce, boolean isTemplate, boolean isEdge) {
    try {
      boolean accept = aclAce.actions.forwarding.equals("accept");
      if (!accept && !aclAce.actions.forwarding.equals("drop")) {
        throw new IllegalArgumentException(
            "Unrecognized forwarding clause " + aclAce.actions.forwarding);
      }

      Rule rule = new Rule(aclAce.name, accept);
      Matches matches = aclAce.matches;
      Integer protocol = resolveIp(rule, matches);
      resolveNw(rule, matches, protocol, isTemplate, isEdge);
      resolveTcp(rule, matches, protocol, isEdge);
      resolveUdp(rule, matches, protocol);
      return rule;
    } catch (Exception e) {
      throw new RuntimeException("While processing rule " + aclAce.name, e);
    }
  }

  private Integer resolveIp(Rule rule, Matches matches) {
    if (matches.ipv4 == null) {
      throw new IllegalArgumentException("Missing ipv4 match criteria");
    }
    if (matches.ipv6 != null) {
      throw new IllegalArgumentException("ipv6 criteria not supported");
    }
    rule.dl_type = AclHelper.DL_TYPE_IPv4;
    Integer protocol = matches.ipv4.protocol;
    if (protocol != AclHelper.NW_PROTO_TCP && protocol != AclHelper.NW_PROTO_UDP) {
      throw new IllegalArgumentException("IP protocol not supported: " + protocol);
    }
    return protocol;
  }

  private void resolveNw(Rule rule, Matches matches, Integer protocol, boolean isTemplate,
      boolean isEdge) {
    rule.nw_proto = protocol;
    rule.nw_dst = resolveNwAddr(matches, false, isTemplate, isEdge);
    rule.nw_src = resolveNwAddr(matches, true, isTemplate, isEdge);
  }

  private void resolveUdp(Rule rule, Matches matches, Integer protocol) {
    if (protocol != AclHelper.NW_PROTO_UDP) {
      return;
    }
    if (matches.tcp != null) {
      throw new IllegalArgumentException("Superfluous tcp section");
    }
    if (matches.udp == null) {
      throw new IllegalArgumentException("Missing udp section");
    }
    rule.udp_src = resolvePort(matches.udp.sourcePort);
    rule.udp_dst = resolvePort(matches.udp.destinationPort);
    if (rule.udp_dst == null && rule.udp_src == null){
      throw new IllegalArgumentException("No udp src/dst port");
    }
  }

  private void resolveTcp(Rule rule, Matches matches, Integer protocol, boolean isEdge) {
    if (protocol != AclHelper.NW_PROTO_TCP) {
      return;
    }
    if (matches.udp != null) {
      throw new IllegalArgumentException("Superfluous udp section");
    }
    if (matches.tcp == null) {
      throw new IllegalArgumentException("Missing tcp section");
    }
    rule.tcp_dst = resolvePort(matches.tcp.destinationPort);
    rule.tcp_src = resolvePort(matches.tcp.sourcePort);

    boolean fromDevice = isFromDevice(matches.tcp.directionInitiated);
    boolean requireSrc = isEdge != fromDevice;
    assertFalse((requireSrc ? rule.tcp_src : rule.tcp_dst) == null,
        "Tcp %s missing for tcp initiated direction", requireSrc ? "src" : "dst");
  }

  private void assertFalse(boolean condition, String message, String... options) {
    if (condition) {
      throw new IllegalArgumentException(String.format(message, (Object[]) options));
    }
  }

  private String resolveNwAddr(Matches matches, boolean isSrc,
      boolean isTemplate, boolean isEdge) {
    String dnsEntry = isSrc ? matches.ipv4.dnsSrc : matches.ipv4.dnsDst;
    if (matches.mud != null) {
      if (dnsEntry != null) {
        throw new RuntimeException("Both DNS and controller specified");
      }
      return (isEdge == isSrc) ? null : String.format(CONTROLLER_TEMPLATE_FORMAT, matches.mud.controller);
    }
    return dnsEntry == null
        ? null
        : isTemplate
            ? String.format(DNS_TEMPLATE_FORMAT, dnsEntry)
            : resolveIpv4Dst(dnsEntry);
  }

  private Integer resolvePort(PortSpec portSpec) {
    if (portSpec == null) {
      return null;
    }
    if (!PORT_MATCH_EQ_OPERATOR.equals(portSpec.operator)) {
      throw new IllegalArgumentException("Invalid port operator " + portSpec.operator);
    }
    return portSpec.port;
  }

  private Integer resolveTcpPort(TpSpec tcp) {
    if (tcp == null || tcp.destinationPort == null) {
      return null;
    }
    return tcp.destinationPort.port;
  }

  private Integer resolveTcpSrc(TpSpec tcp) {
    if (tcp == null || tcp.sourcePort == null) {
      return null;
    }
    return tcp.sourcePort.port;
  }

  private boolean isFromDevice(String directionInitiated) {
    if (directionInitiated == null) {
      throw new IllegalArgumentException("Missing direction-initiated");
    }
    boolean isFromDevice = FROM_DEVICE_POLICY.equals(directionInitiated);
    if (isFromDevice || TO_DEVICE_POLICY.equals(directionInitiated)) {
      return isFromDevice;
    }
    throw new RuntimeException("Invalid direction-initiated: " + directionInitiated);
  }

  private String resolveIpv4Dst(String dnsDst) {
    try {
      if (dnsDst == null) {
        return null;
      }
      if (TEST_DNS_NAME.equals(dnsDst)) {
        return TEST_IP_ADDRESS;
      }
      return Inet4Address.getByName(dnsDst).getHostAddress();
    } catch (UnknownHostException e) {
      throw new RuntimeException("Could not resolve hostname " + dnsDst);
    }
  }

  private AclSpec getAclSpec(AccessLists accessLists, PolicySpec policySpec) {
    try {
      for (AclSpec aclSpec : accessLists.acl) {
        validateAcl(aclSpec);
        if (policySpec.name.equals(aclSpec.name)) {
          return aclSpec;
        }
      }
      throw new IllegalArgumentException("Acl policy not found");
    } catch (Exception e) {
      throw new RuntimeException("While processing policy " + policySpec.name, e);
    }
  }

  private void validateAcl(AclSpec aclSpec) {
    if (aclSpec.name == null) {
      throw new IllegalArgumentException("Missing acl name");
    }
    if (!aclSpec.type.equals("ipv4-acl-type")) {
      throw new IllegalArgumentException(String.format(ACL_TYPE_ERROR_FORMAT, aclSpec.type));
    }
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
