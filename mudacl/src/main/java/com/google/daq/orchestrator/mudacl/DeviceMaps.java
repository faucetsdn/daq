package com.google.daq.orchestrator.mudacl;

import com.google.daq.orchestrator.mudacl.DeviceTopology.ControllerIdentifier;
import com.google.daq.orchestrator.mudacl.DeviceTopology.MacIdentifier;
import java.util.Map;
import java.util.TreeMap;

public class DeviceMaps {
  public Map<MacIdentifier, DeviceSpec> macAddrs = new TreeMap<>();

  /**
   * Create a device specification that's used for creating template ACLs,
   * which are without host information.
   *
   * @param type Type of template device.
   * @return Device spec suitable for templates.
   */
  static DeviceSpec templateSpec(String type) {
    DeviceSpec spec = new DeviceSpec();
    spec.type = type;
    spec.isTemplate = true;
    return spec;
  }

  static class DeviceSpec {
    public String type;
    public String hostname;
    public String ipAddr;
    public Map<ControllerIdentifier, Controller> controllers;
    public boolean isTemplate;
  }

  static class Controller {
    public Map<ControllerIdentifier, Controlee> controlees;
  }

  static class Controlee {
    public String hostname;
  }
}
