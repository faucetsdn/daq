package com.google.daq.mqtt.registrar;

import java.util.*;

public class UdmiSchema {
  static class Envelope {
    public String deviceId;
    public String deviceNumId;
    public String deviceRegistryId;
    public String projectId;
    public final String subFolder = LocalDevice.METADATA_SUBFOLDER;
  }

  static class Metadata {
    public PointsetMetadata pointset;
    public SystemMetadata system;
    public GatewayMetadata gateway;
    public LocalnetMetadata localnet;
    public CloudMetadata cloud;
    public Integer version;
    public Date timestamp;
    public String hash;
  }

  static class CloudMetadata {
    public String auth_type;
  }

  static class PointsetMetadata {
    public Map<String, PointMetadata> points;
  }

  static class SystemMetadata {
    public LocationMetadata location;
    public PhysicalTagMetadata physical_tag;
  }

  static class GatewayMetadata {
    public String gateway_id;
    public List<String> proxy_ids;
  }

  static class PointMetadata {
    public String units;
    public String ref;
  }

  static class LocationMetadata {
    public String site_name;
    public String section;
    public Object position;
  }

  static class PhysicalTagMetadata {
    public AssetMetadata asset;
  }

  static class AssetMetadata {
    public String guid;
    public String name;
  }

  static class Config {
    public Integer version = 1;
    public Date timestamp = new Date();
    public GatewayConfig gateway;
    public LocalnetConfig localnet;
    public PointsetConfig pointset;
  }

  static class GatewayConfig {
    public List<String> proxy_ids = new ArrayList<>();
  }

  static class LocalnetConfig {
    public Map<String, Subsystem> subsystems = new TreeMap<>();
  }

  static class Subsystem {
  }

  static class PointsetConfig {
    public Map<String, PointConfig> points = new TreeMap<>();
  }

  static class PointConfig {
    public String ref;

    static PointConfig fromRef(String ref) {
      PointConfig pointConfig = new PointConfig();
      pointConfig.ref = ref;
      return pointConfig;
    }
  }

  static class LocalnetMetadata {
    public Map<String, LocalnetSubsystem> subsystem;
  }

  static class LocalnetSubsystem {
    public String local_id;
  }
}
