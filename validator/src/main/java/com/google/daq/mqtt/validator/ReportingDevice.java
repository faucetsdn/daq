package com.google.daq.mqtt.validator;

import java.util.Map;

public class ReportingDevice {

  private final String deviceId;
  private Metadata metadata;

  public ReportingDevice(String deviceId) {
    this.deviceId = deviceId;
  }

  public void setMetadata(Metadata metadata) {
    this.metadata = metadata;
  }

  public void validateMetadata(PointsetMessage message) {

  }

  public static class PointsetMessage {
    public Integer version;
    public String timestamp;
    public Map<String, PointDescriptor> points;
  }

  public static class Metadata {
    public Integer version;
    public String timestamp;
    public Object system;
    public PointSet pointset;
  }

  public static class PointSet {
    public Map<String, PointDescriptor> points;
  }

  public static class PointDescriptor {
    public String units;
    public Object present_value;
  }
}
