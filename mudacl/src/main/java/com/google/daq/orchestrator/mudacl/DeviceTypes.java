package com.google.daq.orchestrator.mudacl;

import com.google.daq.orchestrator.mudacl.DeviceTopology.MacIdentifier;
import java.util.Map;
import java.util.TreeMap;

public class DeviceTypes {
  public Map<MacIdentifier, DeviceClassifier> macAddrs = new TreeMap<>();

  static DeviceClassifier templateClassifier(String type) {
    DeviceClassifier classifier = new DeviceClassifier();
    classifier.type = type;
    classifier.isTemplate = true;
    return classifier;
  }

  static class DeviceClassifier {
    public String type;
    public String hostname;
    public String ipAddr;
    public Map<String, Controller> controllers;
    public boolean isTemplate;
  }

  static class Controller {
    public Map<String, Controlee> controlees;
  }

  static class Controlee {
    public String hostname;
  }
}
