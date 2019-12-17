package com.google.daq.mqtt.validator;

import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public class ReportingDevice {

  private final String deviceId;
  private final MetadataDiff metadataDiff = new MetadataDiff();
  private Metadata metadata;
  private Exception error;

  public ReportingDevice(String deviceId) {
    this.deviceId = deviceId;
  }

  public void setMetadata(Metadata metadata) {
    this.metadata = metadata;
  }

  public String getDeviceId() {
    return deviceId;
  }

  public boolean hasMetadataDiff() {
    return metadataDiff.error != null
        || metadataDiff.extraPoints != null
        || metadataDiff.missingPoints != null;
  }

  public MetadataDiff getMetadataDiff() {
    return metadataDiff;
  }

  public void validateMetadata(PointsetMessage message) {
    Set<String> expectedPoints = new HashSet<>(metadata.pointset.points.keySet());
    Set<String> deliveredPoints = new HashSet<>(message.points.keySet());
    metadataDiff.extraPoints = new HashSet<>(deliveredPoints);
    metadataDiff.extraPoints.removeAll(expectedPoints);
    metadataDiff.missingPoints = new HashSet<>(expectedPoints);
    metadataDiff.missingPoints.removeAll(deliveredPoints);
  }

  public void setError(Exception error) {
    this.metadataDiff.error = error.toString();
    this.error = error;
  }

  public static class MetadataDiff {
    public String error;
    public Set<String> extraPoints;
    public Set<String> missingPoints;
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
