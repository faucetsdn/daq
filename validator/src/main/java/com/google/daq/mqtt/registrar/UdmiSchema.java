package com.google.daq.mqtt.registrar;

import java.util.Date;
import java.util.List;
import java.util.Map;

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
      public Integer version;
      public Date timestamp;
      public String hash;
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
}
