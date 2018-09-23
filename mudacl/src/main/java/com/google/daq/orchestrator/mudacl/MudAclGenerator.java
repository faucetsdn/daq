package com.google.daq.orchestrator.mudacl;

import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import com.google.daq.orchestrator.mudacl.AclHelper.PortAcl;
import com.google.daq.orchestrator.mudacl.DeviceTopology.MacIdentifier;
import com.google.daq.orchestrator.mudacl.DeviceTopology.Placement;
import com.google.daq.orchestrator.mudacl.DeviceTypes.DeviceClassifier;
import com.google.daq.orchestrator.mudacl.SwitchTopology.Ace;
import com.google.daq.orchestrator.mudacl.SwitchTopology.Acl;
import com.google.daq.orchestrator.mudacl.SwitchTopology.Interface;
import com.google.daq.orchestrator.mudacl.SwitchTopology.Rule;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.OutputStream;
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;
import java.util.Map.Entry;
import java.util.TreeMap;
import java.util.concurrent.Callable;
import java.util.function.BiConsumer;

public class MudAclGenerator {

  private static final ObjectMapper YAML_MAPPER = new ObjectMapper(new YAMLFactory())
      .setSerializationInclusion(Include.NON_NULL);
  private static final ObjectMapper JSON_MAPPER = new ObjectMapper()
      .setSerializationInclusion(Include.NON_NULL);

  private static final String ACL_NAME_FORMAT = "%s_acl";
  private static final String ACL_FILE_FORMAT = "%s.yaml";
  private static final String MAC_TEMPLATE_PREFIX = "@mac:";
  private static final String MAC_TEMPLATE_FORMAT = MAC_TEMPLATE_PREFIX + "%s";
  private static final String FROM_TEMPLATE_FORMAT = "@from:%s";
  private static final String TO_TEMPLATE_FORMAT = "@to:%s";
  private static final String BASELINE_KEYWORD = "baseline";
  private static final String RAW_ACL_KEYWORD = "raw";
  private static final int SYSTEM_ERROR_RETURN = -1;
  private static final byte[] NEWLINE_BYTES = "\n".getBytes();
  private static final File ERROR_RESULT_FILE = new File("build/mud_errors.json");
  private static final String UPSTREAM_ACL_FORMAT = "dp_%s_upstream";

  private DeviceTopology deviceTopology;
  private SwitchTopology switchTopology;
  private DeviceTypes deviceTypes;
  private AclProvider aclProvider;

  public static void main(String[] argv) {
    try {
      if (argv.length != 2 && argv.length != 6) {
        System.err
            .println("Usage: [switch_topology] [mud_dir] [template_dir] ([device_types] [device_topology] [output_dir])");
        throw new ExpectedException(new IllegalArgumentException("Incorrect arg count"));
      }
      MudAclGenerator generator = new MudAclGenerator();
      generator.setAclProvider(new MudConverter(new File(argv[0])));
      writePortAcls(new File(argv[1]), prettyErrors(generator::makePortAclMap));
      if (argv.length > 2) {
        generator.setSwitchTopology(YAML_MAPPER.readValue(new File(argv[2]), SwitchTopology.class));
        generator.setDeviceTypes(YAML_MAPPER.readValue(new File(argv[3]), DeviceTypes.class));
        generator
            .setDeviceTopology(YAML_MAPPER.readValue(new File(argv[4]), DeviceTopology.class));
        writePortAcls(new File(argv[5]), prettyErrors(generator::makePortAclMap));
      }
    } catch (ExpectedException e) {
      System.err.println(e.toString());
      System.exit(SYSTEM_ERROR_RETURN);
    } catch (Exception e) {
      e.printStackTrace();
      System.exit(SYSTEM_ERROR_RETURN);
    }
  }

  private static <T> T prettyErrors(Callable<T> input) {
    try {
      return input.call();
    } catch (Exception e) {
      try {
        ErrorTree errorTree = formatError(e, "", "  ", System.err);
        System.err.println("Writing errors to " + ERROR_RESULT_FILE.getAbsolutePath());
        JSON_MAPPER.writeValue(ERROR_RESULT_FILE, errorTree);
      } catch (Exception e2) {
        throw new RuntimeException("While pretty-printing errors", e2);
      }
      throw new ExpectedException(e);
    }
  }

  private static ErrorTree formatError(Throwable e, final String prefix,
      final String indent, OutputStream outputStream) {
    final ErrorTree errorTree = new ErrorTree();
    try {
      errorTree.message = e.getMessage();
      outputStream.write(prefix.getBytes());
      outputStream.write(errorTree.message.getBytes());
      outputStream.write(NEWLINE_BYTES);
    } catch (IOException ioe) {
      throw new ExpectedException(ioe);
    }
    final String newPrefix = prefix + indent;
    if (e instanceof ExceptionMap) {
      ((ExceptionMap) e).forEach(
          (key, sub) -> errorTree.causes.put(key, formatError(sub, newPrefix, indent, outputStream)));
    } else if (e.getCause() != null) {
      errorTree.cause = formatError(e.getCause(), newPrefix, indent, outputStream);
    }
    if (errorTree.causes.isEmpty()) {
      errorTree.causes = null;
    }
    return errorTree;
  }

  static class ErrorTree {
    public String message;
    public ErrorTree cause;
    public Map<String, ErrorTree> causes = new TreeMap<>();
  }

  static class ExpectedException extends RuntimeException {
    ExpectedException(Exception e) {
      super(e);
    }
  }

  static class ExceptionMap extends RuntimeException {
    final Map<String, Exception> exceptions;
    ExceptionMap(String description, Map<String, Exception> exceptions) {
      super(description);
      this.exceptions = exceptions;
    }

    public void forEach(BiConsumer<String, Exception> consumer) {
      exceptions.forEach(consumer);
    }
  }

  private static void writePortAcls(File outputDir, Map<String, PortAcl> portAclMap) {
    if (!outputDir.isDirectory()) {
      throw new ExpectedException(
          new FileNotFoundException("Missing output directory " + outputDir.getAbsolutePath()));
    }
    System.out.println("Writing output files to " + outputDir.getAbsolutePath());
    Map<String, Acl> upstreamAcls = new HashMap<>();
    try {
      for (Entry<String, PortAcl> entry: portAclMap.entrySet()) {
        PortAcl portAcl = entry.getValue();
        Placement placement = portAcl.placement;
        String aclName = makeAclName(placement.edgeName());
        File outFile = new File(outputDir, String.format(ACL_FILE_FORMAT, aclName));
        YAML_MAPPER.writeValue(outFile, makeAclInclude(aclName, portAcl));
        if (!placement.isTemplate()) {
          upstreamAcls.computeIfAbsent(placement.dpName, key -> new Acl()).addAll(portAcl.upstreamAcl);
        }
      }
      for (String dpName : upstreamAcls.keySet()) {
        String aclName = String.format(UPSTREAM_ACL_FORMAT, dpName);
        File outFile = new File(outputDir, String.format(ACL_FILE_FORMAT, aclName));
        YAML_MAPPER.writeValue(outFile, makeUpstreamInclude(aclName, upstreamAcls.get(dpName)));
      }
    } catch (Exception e) {
      throw new ExpectedException(e);
    }
  }

  private static String makeAclName(String root) {
    return String.format(ACL_NAME_FORMAT, root);
  }

  private static SwitchTopology makeUpstreamInclude(String aclName, Acl aces) {
    SwitchTopology topology = new SwitchTopology();
    topology.dps = null;
    topology.vlans = null;
    topology.acls.put(aclName, aces);
    return topology;
  }

  private static SwitchTopology makeAclInclude(String aclName, PortAcl portAcl) {
    SwitchTopology topology = new SwitchTopology();
    topology.dps = null;
    topology.vlans = null;
    boolean isTemplate = portAcl.placement.isTemplate();
    String fromKeyValue = isTemplate ? String.format(FROM_TEMPLATE_FORMAT, aclName) : aclName;
    topology.acls.put(fromKeyValue, portAcl.edgeAcl);
    if (isTemplate) {
      topology.acls.put(String.format(TO_TEMPLATE_FORMAT, aclName), portAcl.upstreamAcl);
    }
    return topology;
  }

  private Map<String,PortAcl> makePortAclMap() {
    Map<String, PortAcl> portAclMap = new TreeMap<>();
    Map<MacIdentifier, Placement> targetMap = getDeviceTargetMap();
    Map<String, Exception> errors = new TreeMap<>();
    for (Entry<MacIdentifier, Placement> target : targetMap.entrySet()) {
      MacIdentifier targetSrc = target.getKey();
      DeviceClassifier classifier = getDeviceClassifier(targetSrc);
      try {
        Placement placement = validatePlacement(target.getValue());
        String aclName = placement.edgeName();
        PortAcl portAcl = portAclMap
            .computeIfAbsent(aclName, (baseName) -> new PortAcl(placement));
        portAcl.edgeAcl.addAll(aclSanity(aclProvider.makeEdgeAcl(classifier, targetSrc), true));
        portAcl.upstreamAcl.addAll(aclSanity(aclProvider.makeUpstreamAcl(classifier, targetSrc), false));
      } catch (Exception e) {
        errors.put(classifier.type, e);
      }
    }
    if (!errors.isEmpty()) {
      String description = errors.size() + " type errors";
      throw new ExceptionMap(description, errors);
    }
    if (isTemplate()) {
      addTemplateEntries(portAclMap);
    } else {
      for (PortAcl portAcl : portAclMap.values()) {
        AclHelper.addBaselineRules(portAcl.edgeAcl);
      }
    }
    return portAclMap;
  }

  private Collection<Ace> aclSanity(Acl aces, boolean isEdge) {
    for (Ace ace : aces) {
      Rule rule = ace.rule;
      try {
        checkWhitelistedRules(rule);
        checkWildcardedAcls(isEdge, rule);
      } catch (Exception e) {
        throw new RuntimeException("While processing " + rule.description, e);
      }
    }
    return aces;
  }

  private void checkWhitelistedRules(Rule rule) {
    if (AclHelper.UDP_NTP_PORT.equals(rule.udp_src) ||
        AclHelper.UDP_NTP_PORT.equals(rule.udp_dst)) {
      throw new IllegalArgumentException("Should not include NTP ports in ACLs");
    }
    if (AclHelper.UDP_DNS_PORT.equals(rule.udp_src) ||
        AclHelper.UDP_DNS_PORT.equals(rule.udp_dst) ||
        AclHelper.TCP_DNS_PORT.equals(rule.tcp_src) ||
        AclHelper.TCP_DNS_PORT.equals(rule.tcp_dst)) {
      throw new IllegalArgumentException("Should not include DNS ports in ACLs");
    }
    if (AclHelper.UDP_DHCP_CLIENT_PORT.equals(rule.udp_src) ||
        AclHelper.UDP_DHCP_CLIENT_PORT.equals(rule.udp_dst) ||
        AclHelper.UDP_DHCP_SERVER_PORT.equals(rule.udp_src) ||
        AclHelper.UDP_DHCP_SERVER_PORT.equals(rule.udp_dst)) {
      throw new IllegalArgumentException("Should not include DHCP ports in ACLs");
    }
  }

  private void checkWildcardedAcls(boolean isEdge, Rule rule) {
    boolean validDstPort = (AclHelper.NW_PROTO_TCP.equals(rule.nw_proto) ? rule.tcp_dst : rule.udp_dst) != null;
    boolean validDstAddr = rule.nw_dst != null;
    boolean validSrcPort = (AclHelper.NW_PROTO_TCP.equals(rule.nw_proto) ? rule.tcp_src : rule.udp_src) != null;
    boolean validSrcAddr = rule.nw_src != null;
    if (isEdge && !validDstPort && !validDstAddr) {
      throw new RuntimeException("Cowardly refusing to create wildcarded edge ACL " + rule.description);
    }
    if (!isEdge && !validSrcPort && !validSrcAddr) {
      throw new RuntimeException("Cowardly refusing to create wildcarded upstream ACL " + rule.description);
    }
  }

  private void addTemplateEntries(Map<String, PortAcl> portAclMap) {
    {
      Placement placement = new Placement();
      placement.dpName = RAW_ACL_KEYWORD;
      String aclName = placement.edgeName();
      PortAcl portAcl = portAclMap
          .computeIfAbsent(aclName, (baseName) -> new PortAcl(placement));
      AclHelper.addRawRules(portAcl.edgeAcl);
    }

    {
      Placement placement = new Placement();
      placement.dpName = BASELINE_KEYWORD;
      String aclName = placement.edgeName();
      PortAcl portAcl = portAclMap
          .computeIfAbsent(aclName, (baseName) -> new PortAcl(placement));
      AclHelper.addBaselineRules(portAcl.edgeAcl);
    }
  }

  private DeviceClassifier getDeviceClassifier(MacIdentifier targetSrc) {
    String targetSrcStr = targetSrc.toString();
    if (targetSrcStr.startsWith(MAC_TEMPLATE_PREFIX)) {
      String templateName = targetSrcStr.substring(MAC_TEMPLATE_PREFIX.length(),
          targetSrcStr.length());
      return DeviceTypes.templateClassifier(templateName);
    } else {
      DeviceClassifier defaultClassifier = DeviceTypes.templateClassifier("default");
      Map<MacIdentifier, DeviceClassifier> macAddrs = deviceTypes.macAddrs;
      return macAddrs.containsKey(targetSrc) ? macAddrs.get(targetSrc) : defaultClassifier;
    }
  }

  private Map<MacIdentifier, Placement> getDeviceTargetMap() {
    return isTemplate() ? makeTemplateDeviceTargetMap() : deviceTopology.macAddrs;
  }

  private boolean isTemplate() {
    return deviceTopology == null;
  }

  private Map<MacIdentifier,Placement> makeTemplateDeviceTargetMap() {
    Map<MacIdentifier, Placement> templateMap = new HashMap<>();
    for (String targetType : aclProvider.targetTypes()) {
      String templateMac = String.format(MAC_TEMPLATE_FORMAT, targetType);
      Placement templatePlacement = new Placement();
      templatePlacement.dpName = targetType;
      templateMap.put(new MacIdentifier(templateMac), templatePlacement);
    }
    return templateMap;
  }

  private Placement validatePlacement(Placement value) {
    if (isTemplate()) {
      return value;
    }
    SwitchTopology.DataPlane dataPlane = switchTopology.dps.get(value.dpName);
    if (dataPlane == null) {
      throw new IllegalArgumentException("Invalid data plane for " + value);
    }
    Interface port = dataPlane.interfaces.get(value.portNum);
    if (port == null) {
      throw new IllegalArgumentException("Invalid port for " + value);
    }
    if (!makeAclName(value.edgeName()).equals(port.acl_in)) {
      throw new IllegalArgumentException("Bad acl_in " + port.acl_in + " for " + value);
    }
    return value;
  }

  private void setDeviceTopology(DeviceTopology deviceTopology) {
    this.deviceTopology = deviceTopology;
  }

  private void setSwitchTopology(SwitchTopology switchTopology) {
    this.switchTopology = switchTopology;
  }

  private void setDeviceTypes(DeviceTypes deviceTypes) {
    this.deviceTypes = deviceTypes;
  }

  private void setAclProvider(AclProvider aclProvider) {
    this.aclProvider = aclProvider;
  }

}
