package com.google.daq.orchestrator.mudacl;

import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import com.google.daq.orchestrator.mudacl.AclHelper.PortAcl;
import com.google.daq.orchestrator.mudacl.DeviceTopology.MacIdentifier;
import com.google.daq.orchestrator.mudacl.DeviceTopology.Placement;
import com.google.daq.orchestrator.mudacl.DeviceTypes.DeviceClassifier;
import com.google.daq.orchestrator.mudacl.SwitchTopology.Acl;
import com.google.daq.orchestrator.mudacl.SwitchTopology.Interface;
import java.io.File;
import java.io.FileNotFoundException;
import java.util.HashMap;
import java.util.Map;
import java.util.Map.Entry;
import java.util.TreeMap;

public class MudAclGenerator {

  private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper(new YAMLFactory())
      .setSerializationInclusion(Include.NON_NULL);

  private static final String ACL_NAME_FORMAT = "%s_acl";
  private static final String ACL_FILE_FORMAT = "%s.yaml";
  private static final String SRC_MAC_TEMPLATE_PREFIX = "@src_mac:";
  private static final String SRC_MAC_TEMPLATE_FORMAT = SRC_MAC_TEMPLATE_PREFIX + "%s";
  private static final String ACL_TEMPLATE_FORMAT = "@acl:%s";
  private static final String BASELINE_KEYWORD = "baseline";

  private DeviceTopology deviceTopology;
  private SwitchTopology switchTopology;
  private DeviceTypes deviceTypes;
  private AclProvider aclProvider;

  public static void main(String[] argv) {
    try {
      if (argv.length != 3 && argv.length != 6) {
        System.err
            .println("Usage: [switch_topology] [mud_dir] [template_dir] ([device_types] [device_topology] [output_dir])");
        throw new ExpectedException(new IllegalArgumentException("Incorrect arg count"));
      }
      MudAclGenerator generator = new MudAclGenerator();
      generator.setSwitchTopology(OBJECT_MAPPER.readValue(new File(argv[0]), SwitchTopology.class));
      generator.setAclProvider(new MudConverter(new File(argv[1])));
      writePortAcls(new File(argv[2]), generator.makePortAclMap());
      if (argv.length > 3) {
        generator.setDeviceTypes(OBJECT_MAPPER.readValue(new File(argv[3]), DeviceTypes.class));
        generator
            .setDeviceTopology(OBJECT_MAPPER.readValue(new File(argv[4]), DeviceTopology.class));
        writePortAcls(new File(argv[5]), generator.makePortAclMap());
      }
    } catch (ExpectedException e) {
      System.err.println(e.toString());
    } catch (Exception e) {
      e.printStackTrace();
    }
  }

  static class ExpectedException extends RuntimeException {
    ExpectedException(Exception e) {
      super(e);
    }
  }

  private static void writePortAcls(File outputDir, Map<String, PortAcl> portAclMap) {
    if (!outputDir.isDirectory()) {
      throw new ExpectedException(
          new FileNotFoundException("Missing output directory " + outputDir.getAbsolutePath()));
    }
    System.out.println("Writing output files to " + outputDir.getAbsolutePath());
    for (Entry<String, PortAcl> entry: portAclMap.entrySet()) {
      try {
        Placement placement = entry.getValue().placement;
        String aclName = makeAclName(placement);
        File outFile = new File(outputDir, String.format(ACL_FILE_FORMAT, aclName));
        OBJECT_MAPPER.writeValue(outFile, makeAclInclude(aclName, entry.getValue().acl, placement.isTemplate()));
      } catch (Exception e) {
        throw new ExpectedException(e);
      }
    }
  }

  private static String makeAclName(Placement placement) {
    return String.format(ACL_NAME_FORMAT, placement.toString());
  }

  private static SwitchTopology makeAclInclude(String aclName, Acl value, boolean isTemplate) {
    SwitchTopology topology = new SwitchTopology();
    topology.dps = null;
    topology.vlans = null;
    String aclKeyValue = isTemplate ? String.format(ACL_TEMPLATE_FORMAT, aclName) : aclName;
    topology.acls.put(aclKeyValue, value);
    return topology;
  }

  private Map<String,PortAcl> makePortAclMap() {
    Map<String, PortAcl> portAclMap = new TreeMap<>();
    Map<MacIdentifier, Placement> targetMap = getDeviceTargetMap();
    for (Entry<MacIdentifier, Placement> target : targetMap.entrySet()) {
      Placement placement = validatePlacement(target.getValue());
      String aclName = placement.toString();
      PortAcl portAcl = portAclMap.computeIfAbsent(aclName, (baseName) -> new PortAcl(placement, new Acl()));
      MacIdentifier targetSrc = target.getKey();
      DeviceClassifier classifier = getDeviceClassifier(targetSrc);
      portAcl.acl.addAll(aclProvider.makeEdgeAcl(targetSrc, classifier));
    }
    if (isTemplate()) {
      Placement placement = new Placement();
      placement.dpName = BASELINE_KEYWORD;
      String aclName = placement.toString();
      PortAcl portAcl = portAclMap.computeIfAbsent(aclName, (baseName) -> new PortAcl(placement, new Acl()));
      AclHelper.addBaselineRules(portAcl.acl);
    } else {
      for (PortAcl portAcl : portAclMap.values()) {
        AclHelper.addBaselineRules(portAcl.acl);
      }
    }
    return portAclMap;
  }

  private DeviceClassifier getDeviceClassifier(MacIdentifier targetSrc) {
    String targetSrcStr = targetSrc.toString();
    if (targetSrcStr.startsWith(SRC_MAC_TEMPLATE_PREFIX)) {
      String templateName = targetSrcStr.substring(SRC_MAC_TEMPLATE_PREFIX.length(),
          targetSrcStr.length());
      return DeviceTypes.templateClassifier(templateName);
    } else {
      return deviceTypes.macAddrs.get(targetSrc);
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
      String templateMac = String.format(SRC_MAC_TEMPLATE_FORMAT, targetType);
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
    if (!makeAclName(value).equals(port.acl_in)) {
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
