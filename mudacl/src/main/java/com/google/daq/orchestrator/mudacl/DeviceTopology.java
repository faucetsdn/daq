package com.google.daq.orchestrator.mudacl;

import java.util.Map;
import java.util.TreeMap;

public class DeviceTopology {

  public Map<MacIdentifier, Placement> macAddrs = new TreeMap<>();

  static class MacIdentifier extends StringId {
    public MacIdentifier(String macAddr) {
      super(macAddr);
    }

    public static MacIdentifier fromString(String macAddr) {
      return new MacIdentifier(macAddr);
    }
  }

  static class Placement {
    public String dpName;
    public Integer portNum;

    public String toString() {
      return String.format("dp_%s_port_%d", dpName, portNum);
    }
  }
}
