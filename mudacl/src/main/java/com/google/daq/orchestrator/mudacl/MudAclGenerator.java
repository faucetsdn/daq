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
import java.util.Map;
import java.util.Map.Entry;
import java.util.TreeMap;

public class MudAclGenerator {

  private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper(new YAMLFactory())
      .setSerializationInclusion(Include.NON_NULL);

  private static final String ACL_NAME_FORMAT = "%s_acl";
  private static final String ACL_FILE_FORMAT = "%s.yaml";

  private DeviceTopology deviceTopology;
  private SwitchTopology switchTopology;
  private DeviceTypes deviceTypes;
  private AclProvider aclProvider;

  public static void main(String[] argv) {
    try {
      if (argv.length != 5) {
        System.err
            .println("Usage: [switch_topology] [device_topology] [device_types] [mud_dir] [output_dir]");
        throw new ExpectedException(new IllegalArgumentException("Incorrect arg count"));
      }
      MudAclGenerator generator = new MudAclGenerator();
      generator.setSwitchTopology(OBJECT_MAPPER.readValue(new File(argv[0]), SwitchTopology.class));
      generator.setDeviceTopology(OBJECT_MAPPER.readValue(new File(argv[1]), DeviceTopology.class));
      generator.setDeviceTypes(OBJECT_MAPPER.readValue(new File(argv[2]), DeviceTypes.class));
      generator.setAclProvider(new MudConverter(new File(argv[3])));
      writePortAcls(new File(argv[4]), generator.makePortAclMap());
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
    for (Entry<String, PortAcl> entry: portAclMap.entrySet()) {
      try {
        String aclName = makeAclName(entry.getValue().placement);
        File outFile = new File(outputDir, String.format(ACL_FILE_FORMAT, aclName));
        OBJECT_MAPPER.writeValue(outFile, makeAclInclude(aclName, entry.getValue().acl));
      } catch (Exception e) {
        throw new ExpectedException(e);
      }
    }
  }

  private static String makeAclName(Placement placement) {
    return String.format(ACL_NAME_FORMAT, placement.toString());
  }

  private static SwitchTopology makeAclInclude(String aclName, Acl value) {
    SwitchTopology topology = new SwitchTopology();
    topology.dps = null;
    topology.vlans = null;
    topology.acls.put(aclName, value);
    return topology;
  }

  private Map<String,PortAcl> makePortAclMap() {
    Map<String, PortAcl> portAclMap = new TreeMap<>();
    for (Entry<MacIdentifier, Placement> target : deviceTopology.macAddrs.entrySet()) {
      Placement placement = validatePlacement(target.getValue());
      String aclName = placement.toString();
      PortAcl portAcl = portAclMap.computeIfAbsent(aclName, (baseName) -> new PortAcl(placement, new Acl()));
      DeviceClassifier classifier = deviceTypes.macAddrs.get(target.getKey());
      portAcl.acl.addAll(aclProvider.makeEdgeAcl(target.getKey(), classifier));
    }
    for (PortAcl portAcl : portAclMap.values()) {
      AclHelper.finalizeAcl(portAcl.acl);
    }
    return portAclMap;
  }

  private Placement validatePlacement(Placement value) {
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
