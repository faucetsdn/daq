package com.google.daq.mqtt.registrar;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.api.services.cloudiot.v1.model.DeviceCredential;
import com.google.common.base.Preconditions;
import com.google.daq.mqtt.util.CloudDeviceSettings;
import com.google.daq.mqtt.util.CloudIotManager;
import java.io.File;
import java.io.FileInputStream;
import java.nio.charset.Charset;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.apache.commons.io.IOUtils;

public class LocalDevice {

  private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

  private static final String RSA256_X509_PEM = "RSA_X509_PEM";
  private static final String RSA_PUBLIC_PEM = "rsa_public.pem";
  private static final String PROPERTIES_JSON = "properties.json";
  private static final String METADATA_LOCATION_KEY = "location";
  private static final String METADATA_SITE_CODE_KEY = "site_code";

  private final String deviceId;
  private final String siteCode;
  private final File deviceDir;
  private final Properties properties;

  private CloudDeviceSettings settings;

  LocalDevice(String deviceId, String siteCode, File devicesDir) {
    this.deviceId = deviceId;
    this.siteCode = siteCode;
    deviceDir = new File(devicesDir, deviceId);
    properties = readProperties();
  }

  private Properties readProperties() {
    File configFile = new File(deviceDir, PROPERTIES_JSON);
    try {
      return validate(OBJECT_MAPPER.readValue(configFile, Properties.class));
    } catch (Exception e) {
      throw new RuntimeException("While reading properties file "+ configFile.getAbsolutePath(), e);
    }
  }

  private Properties validate(Properties properties) {
    String mode = properties.mode;
    String gatewayId = properties.gateway_id;
    if ("direct".equals(mode)) {
      Preconditions.checkArgument(gatewayId == null, "direct mode gateway_id should be null");
    } else if ("gateway".equals(mode)) {
      Preconditions.checkArgument(gatewayId == null, "gateway mode gateway_id should be null");
    } else if ("proxy".equals(mode)) {
      Preconditions.checkNotNull(gatewayId, "proxy mode needs gateway_id property specified");
    } else {
      throw new RuntimeException("Unknown device mode " + mode);
    }
    Preconditions.checkNotNull(properties.location, "location property not defined");
    return properties;
  }

  private List<DeviceCredential> loadCredentials() {
    try {
      File deviceKeyFile = new File(deviceDir, RSA_PUBLIC_PEM);
      if (!deviceKeyFile.exists()) {
        generateNewKey();
      }
      return CloudIotManager.makeCredentials(RSA256_X509_PEM,
          IOUtils.toString(new FileInputStream(deviceKeyFile), Charset.defaultCharset()));
    } catch (Exception e) {
      throw new RuntimeException("While loading credentials for local device " + deviceId, e);
    }
  }

  private void generateNewKey() {
    String absolutePath = deviceDir.getAbsolutePath();
    try {
      System.err.println("Generating device credentials in " + absolutePath);
      int exitCode = Runtime.getRuntime().exec("validator/bin/keygen.sh " + absolutePath).waitFor();
      if (exitCode != 0) {
        throw new RuntimeException("Keygen exit code " + exitCode);
      }
    } catch (Exception e) {
      throw new RuntimeException("While generating new credentials for " + deviceId, e);
    }
  }

  private Map<String, String> loadMetadata() {
      Map<String, String> metaMap = new HashMap<>();
      metaMap.put(METADATA_SITE_CODE_KEY, siteCode);
      metaMap.put(METADATA_LOCATION_KEY, properties.location);
      return metaMap;
  }

  CloudDeviceSettings getSettings() {
    if (settings != null) {
      return settings;
    }

    settings = new CloudDeviceSettings();
    settings.credentials = loadCredentials();
    settings.metadata = loadMetadata();
    return settings;
  }

  private static class Properties {
    public String mode;
    public String gateway_id;
    public String location;
  }
}
