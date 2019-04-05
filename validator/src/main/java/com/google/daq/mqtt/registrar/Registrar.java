package com.google.daq.mqtt.registrar;

import static com.google.daq.mqtt.registrar.LocalDevice.METADATA_SUBFOLDER;
import static java.util.stream.Collectors.toSet;

import com.google.api.services.cloudiot.v1.model.Device;
import com.google.api.services.cloudiot.v1.model.DeviceCredential;
import com.google.common.base.Preconditions;
import com.google.daq.mqtt.util.CloudDeviceSettings;
import com.google.daq.mqtt.util.CloudIotManager;
import com.google.daq.mqtt.util.ExceptionMap;
import com.google.daq.mqtt.util.ExceptionMap.ErrorTree;
import com.google.daq.mqtt.util.PubSubPusher;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.everit.json.schema.Schema;
import org.everit.json.schema.loader.SchemaClient;
import org.everit.json.schema.loader.SchemaLoader;
import org.json.JSONObject;
import org.json.JSONTokener;

public class Registrar {

  static final String METADATA_JSON = "metadata.json";
  static final String ENVELOPE_JSON = "envelope.json";
  static final String PROPERTIES_JSON = "properties.json";

  private static final String CLOUD_IOT_CONFIG_JSON = "cloud_iot_config.json";
  private static final String DEVICES_DIR = "devices";
  private static final String ERROR_FORMAT_INDENT = "  ";
  private String gcpCredPath;
  private CloudIotManager cloudIotManager;
  private File cloudIotConfig;
  private File siteConfig;
  private Map<String, Schema> schemas = new HashMap<>();
  private File schemaBase;
  private String schemaName;
  private PubSubPusher pubSubPusher;

  public static void main(String[] args) {
    Registrar registrar = new Registrar();
    try {
      if (args.length != 3) {
        throw new IllegalArgumentException("Args: [gcp_cred_file] [site_dir] [schema_file]");
      }
      registrar.setSchemaBase(args[2]);
      registrar.setGcpCredPath(args[0]);
      registrar.setSiteConfigPath(args[1]);
      registrar.processDevices();
      registrar.shutdown();
    } catch (ExceptionMap em) {
      ErrorTree errorTree = ExceptionMap.format(em, ERROR_FORMAT_INDENT);
      errorTree.write(System.err);
      System.exit(2);
    } catch (Exception e) {
      e.printStackTrace();
      System.exit(-1);
    }
    System.exit(0);
  }

  private void setSiteConfigPath(String siteConfigPath) {
    Preconditions.checkNotNull(schemaName, "schemaName not set yet");
    siteConfig = new File(siteConfigPath);
    cloudIotConfig = new File(siteConfig, CLOUD_IOT_CONFIG_JSON);
    cloudIotManager = new CloudIotManager(new File(gcpCredPath), cloudIotConfig, schemaName);
    pubSubPusher = new PubSubPusher(new File(gcpCredPath), cloudIotConfig);
  }

  private void processDevices() {
    ExceptionMap exceptionMap = new ExceptionMap("Error processing local devices");
    try {
      Map<String, LocalDevice> localDevices = loadLocalDevices();
      List<Device> cloudDevices = fetchDeviceList();
      Set<String> extraDevices = cloudDevices.stream().map(Device::getId).collect(toSet());
      for (String localName : localDevices.keySet()) {
        try {
          extraDevices.remove(localName);
          LocalDevice localDevice = localDevices.get(localName);
          updateCloudIoT(localDevice);
          Device device = Preconditions.checkNotNull(fetchDevice(localName),
              "missing device " + localName);
          BigInteger numId = Preconditions.checkNotNull(device.getNumId(),
              "missing deviceNumId for " + localName);
          localDevice.setDeviceNumId(numId.toString());
          sendMetadataMessage(localDevice);
        } catch (Exception e) {
          System.err.println("Deferring exception: " + e.toString());
          exceptionMap.put(localName, e);
        }
      }
      for (String extraName : extraDevices) {
        try {
          System.err.println("Blocking extra device " + extraName);
          cloudIotManager.blockDevice(extraName, true);
        } catch (Exception e) {
          exceptionMap.put(extraName, e);
        }
      }
      System.err.println(String.format("Processed %d devices", localDevices.size()));
    } catch (Exception e) {
      throw new RuntimeException("While processing devices", e);
    }
    exceptionMap.throwIfNotEmpty();
  }

  private Device fetchDevice(String localName) {
    try {
      return cloudIotManager.fetchDevice(localName);
    } catch (Exception e) {
      throw new RuntimeException("Fetching device " + localName, e);
    }
  }

  private void sendMetadataMessage(LocalDevice localDevice) {
    System.err.println("Sending metadata message for " + localDevice.getDeviceId());
    Map<String, String> attributes = new HashMap<>();
    attributes.put("deviceId", localDevice.getDeviceId());
    attributes.put("deviceNumId", localDevice.getDeviceNumId());
    attributes.put("deviceRegistryId", cloudIotManager.getRegistryId());
    attributes.put("projectId", cloudIotManager.getProjectId());
    attributes.put("subFolder", METADATA_SUBFOLDER);
    pubSubPusher.sendMessage(attributes, localDevice.getSettings().metadata);
  }

  private void updateCloudIoT(LocalDevice localDevice) {
    String localName = localDevice.getDeviceId();
    fetchDevice(localName);
    CloudDeviceSettings localDeviceSettings = localDevice.getSettings();
    if (cloudIotManager.registerDevice(localName, localDeviceSettings)) {
      System.err.println("Created new device entry " + localName);
    } else {
      System.err.println("Updated device entry " + localName);
    }
  }

  private void shutdown() {
    pubSubPusher.shutdown();
  }

  private List<Device> fetchDeviceList() {
    System.err.println("Fetching remote registry " + cloudIotManager.getRegistryId());
    return cloudIotManager.fetchDeviceList();
  }

  private Map<String,LocalDevice> loadLocalDevices() {
    File devicesDir = new File(siteConfig, DEVICES_DIR);
    String[] devices = devicesDir.list();
    Preconditions.checkNotNull(devices, "No devices found in " + devicesDir.getAbsolutePath());
    Map<String, LocalDevice> localDevices = loadDevices(devicesDir, devices);
    validateKeys(localDevices);
    validateFiles(localDevices);
    writeNormalized(localDevices);
    return localDevices;
  }

  private void validateFiles(Map<String, LocalDevice> localDevices) {
    ExceptionMap exceptionMap = new ExceptionMap("Error loading local devices");
    for (LocalDevice device : localDevices.values()) {
      try {
        device.validatedDeviceDir();
      } catch (Exception e) {
        exceptionMap.put(device.getDeviceId(), e);
      }
    }
    exceptionMap.throwIfNotEmpty();
  }

  private void writeNormalized(Map<String, LocalDevice> localDevices) {
    ExceptionMap exceptionMap = new ExceptionMap("Error loading local devices");
    for (String deviceName : localDevices.keySet()) {
      try {
        System.err.println("Writing normalized device " + deviceName);
        localDevices.get(deviceName).writeNormalized();
      } catch (Exception e) {
        exceptionMap.put(deviceName, e);
      }
    }
    exceptionMap.throwIfNotEmpty();
  }

  private void validateKeys(Map<String, LocalDevice> localDevices) {
    ExceptionMap exceptionMap = new ExceptionMap("Error loading local devices");
    Map<DeviceCredential, String> privateKeys = new HashMap<>();
    for (String deviceName : localDevices.keySet()) {
      CloudDeviceSettings settings = localDevices.get(deviceName).getSettings();
      if (privateKeys.containsKey(settings.credential)) {
        String previous = privateKeys.get(settings.credential);
        RuntimeException exception = new RuntimeException(
            String.format("Duplicate credentials found for %s & %s", previous, deviceName));
        exceptionMap.put(deviceName, exception);
      } else {
        privateKeys.put(settings.credential, deviceName);
      }
    }
    exceptionMap.throwIfNotEmpty();
  }

  private Map<String, LocalDevice> loadDevices(File devicesDir, String[] devices) {
    ExceptionMap exceptionMap = new ExceptionMap("Error loading local devices");
    HashMap<String, LocalDevice> localDevices = new HashMap<>();
    for (String deviceName : devices) {
      try {
        if (LocalDevice.deviceExists(devicesDir, deviceName)) {
          System.err.println("Loading local device " + deviceName);
          LocalDevice localDevice = new LocalDevice(devicesDir, deviceName, schemas);
          localDevice.validate(cloudIotManager.getRegistryId(), cloudIotManager.getSiteName());
          localDevices.put(deviceName, localDevice);
        }
      } catch (Exception e) {
        exceptionMap.put(deviceName, e);
      }
    }
    exceptionMap.throwIfNotEmpty();
    return localDevices;
  }

  private void setGcpCredPath(String gcpConfigPath) {
    this.gcpCredPath = gcpConfigPath;
  }

  private void setSchemaBase(String schemaBasePath) {
    schemaBase = new File(schemaBasePath);
    schemaName = schemaBase.getName();
    loadSchema(METADATA_JSON);
    loadSchema(ENVELOPE_JSON);
    loadSchema(PROPERTIES_JSON);
  }

  private void loadSchema(String key) {
    File schemaFile = new File(schemaBase, key);
    try (InputStream schemaStream = new FileInputStream(schemaFile)) {
      JSONObject rawSchema = new JSONObject(new JSONTokener(schemaStream));
      schemas.put(key, SchemaLoader.load(rawSchema, new Loader()));
    } catch (Exception e) {
      throw new RuntimeException("While loading schema " + schemaFile.getAbsolutePath(), e);
    }
  }

  private class Loader implements SchemaClient {

    public static final String FILE_PREFIX = "file:";

    @Override
    public InputStream get(String schema) {
      try {
        Preconditions.checkArgument(schema.startsWith(FILE_PREFIX));
        return new FileInputStream(new File(schemaBase, schema.substring(FILE_PREFIX.length())));
      } catch (Exception e) {
        throw new RuntimeException("While loading sub-schema " + schema, e);
      }
    }
  }
}
