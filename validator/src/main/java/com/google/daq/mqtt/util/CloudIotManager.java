package com.google.daq.mqtt.util;

import static com.google.daq.mqtt.util.ConfigUtil.readCloudIotConfig;
import static com.google.daq.mqtt.util.ConfigUtil.readGcpCreds;

import com.google.api.client.googleapis.auth.oauth2.GoogleCredential;
import com.google.api.client.googleapis.javanet.GoogleNetHttpTransport;
import com.google.api.client.googleapis.json.GoogleJsonResponseException;
import com.google.api.client.http.HttpRequestInitializer;
import com.google.api.client.json.JsonFactory;
import com.google.api.client.json.jackson2.JacksonFactory;
import com.google.api.services.cloudiot.v1.CloudIot;
import com.google.api.services.cloudiot.v1.model.Device;
import com.google.api.services.cloudiot.v1.model.DeviceCredential;
import com.google.api.services.cloudiot.v1.model.PublicKeyCredential;
import com.google.common.base.Preconditions;
import com.google.common.collect.ImmutableList;
import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 */
public class CloudIotManager {

  private static final String DEVICE_UPDATE_MASK = "blocked,credentials,metadata";
  private static final String PROFILE_KEY = "profile";
  private static final String SCHEMA_KEY = "schema_name";
  private static final int LIST_PAGE_SIZE = 1000;

  private final GcpCreds configuration;
  private final CloudIotConfig cloudIotConfig;

  private final String registryId;

  private CloudIot cloudIotService;
  private String projectPath;
  private CloudIot.Projects.Locations.Registries cloudIotRegistries;
  private Map<String, Device> deviceMap;
  private String schemaName;

  public CloudIotManager(File gcpCred, File iotConfigFile, String schemaName) {
    configuration = readGcpCreds(gcpCred);
    cloudIotConfig = validate(readCloudIotConfig(iotConfigFile));
    registryId = cloudIotConfig.registry_id;
    this.schemaName = schemaName;
    initializeCloudIoT(gcpCred);
  }

  private static CloudIotConfig validate(CloudIotConfig cloudIotConfig) {
    Preconditions.checkNotNull(cloudIotConfig.registry_id, "registry_id not defined");
    Preconditions.checkNotNull(cloudIotConfig.cloud_region, "cloud_region not defined");
    Preconditions.checkNotNull(cloudIotConfig.site_name, "site_name not defined");
    return cloudIotConfig;
  }

  private String getRegistryPath(String registryId) {
    return projectPath + "/registries/" + registryId;
  }

  private String getDevicePath(String registryId, String deviceId) {
    return getRegistryPath(registryId) + "/devices/" + deviceId;
  }

  private void initializeCloudIoT(File gcpCredFile) {
    projectPath = "projects/" + configuration.project_id + "/locations/" + cloudIotConfig.cloud_region;
    try {
      GoogleCredential credential = ConfigUtil.authorizeServiceAccount(gcpCredFile);
      System.err.println(String.format("Using service account %s/%s",
          credential.getServiceAccountId(), credential.getServiceAccountUser()));
      JsonFactory jsonFactory = JacksonFactory.getDefaultInstance();
      HttpRequestInitializer init = new RetryHttpInitializerWrapper(credential);
      cloudIotService =
          new CloudIot.Builder(GoogleNetHttpTransport.newTrustedTransport(), jsonFactory, init)
              .setApplicationName("com.google.iot.bos")
              .build();
      cloudIotRegistries = cloudIotService.projects().locations().registries();
      System.err.println("Created service for project " + configuration.project_id);
    } catch (Exception e) {
      throw new RuntimeException("While initializing Cloud IoT project " + projectPath, e);
    }
  }

  public boolean registerDevice(String deviceId, CloudDeviceSettings settings) {
    try {
      Preconditions.checkNotNull(cloudIotService, "CloudIoT service not initialized");
      Preconditions.checkNotNull(deviceMap, "deviceMap not initialized");
      Device device = deviceMap.get(deviceId);
      if (device == null) {
        createDevice(deviceId, settings);
        return true;
      } else {
        updateDevice(deviceId, settings, device);
      }
      return false;
    } catch (Exception e) {
      throw new RuntimeException("While registering device " + deviceId, e);
    }
  }

  public void blockDevice(String deviceId, boolean blocked) {
    try {
      Device device = new Device();
      device.setBlocked(blocked);
      String path = getDevicePath(registryId, deviceId);
      cloudIotRegistries.devices().patch(path, device).setUpdateMask("blocked").execute();
    } catch (Exception e) {
      throw new RuntimeException(String.format("While (un)blocking device %s/%s=%s", registryId, deviceId, blocked), e);
    }
  }

  private Device makeDevice(String deviceId, CloudDeviceSettings settings,
      Device oldDevice) {
    Map<String, String> metadataMap = oldDevice == null ? null : oldDevice.getMetadata();
    if (metadataMap == null) {
      metadataMap = new HashMap<>();
    }
    metadataMap.put(PROFILE_KEY, settings.metadata);
    metadataMap.put(SCHEMA_KEY, schemaName);
    return new Device()
        .setId(deviceId)
        .setCredentials(ImmutableList.of(settings.credential))
        .setMetadata(metadataMap);
  }

  private void createDevice(String deviceId, CloudDeviceSettings settings) throws IOException {
    try {
      cloudIotRegistries.devices().create(getRegistryPath(registryId),
          makeDevice(deviceId, settings, null)).execute();
    } catch (GoogleJsonResponseException e) {
      throw new RuntimeException("Remote error creating device " + deviceId, e);
    }
  }

  private void updateDevice(String deviceId, CloudDeviceSettings settings,
      Device oldDevice) {
    try {
      Device device = makeDevice(deviceId, settings, oldDevice)
          .setId(null)
          .setNumId(null);
      cloudIotRegistries
          .devices()
          .patch(getDevicePath(registryId, deviceId), device).setUpdateMask(DEVICE_UPDATE_MASK)
          .execute();
    } catch (Exception e) {
      throw new RuntimeException("Remote error patching device " + deviceId, e);
    }
  }

  public static DeviceCredential makeCredentials(String keyFormat, String keyData) {
    PublicKeyCredential publicKeyCredential = new PublicKeyCredential();
    publicKeyCredential.setFormat(keyFormat);
    publicKeyCredential.setKey(keyData);

    DeviceCredential deviceCredential = new DeviceCredential();
    deviceCredential.setPublicKey(publicKeyCredential);
    return deviceCredential;
  }

  public List<Device> fetchDeviceList() {
    Preconditions.checkNotNull(cloudIotService, "CloudIoT service not initialized");
    try {
      deviceMap = new HashMap<>();
      List<Device> devices = cloudIotRegistries
          .devices()
          .list(getRegistryPath(registryId))
          .setPageSize(LIST_PAGE_SIZE)
          .execute()
          .getDevices();
      if (devices.size() == LIST_PAGE_SIZE) {
        throw new RuntimeException("Returned exact page size, likely not fetched all devices");
      }
      return devices;
    } catch (Exception e) {
      throw new RuntimeException("While listing devices for registry " + registryId, e);
    }
  }

  public Device fetchDevice(String deviceId) {
    return deviceMap.computeIfAbsent(deviceId, this::fetchDeviceFromCloud);
  }

  private Device fetchDeviceFromCloud(String deviceId) {
    try {
      return cloudIotRegistries.devices().get(getDevicePath(registryId, deviceId)).execute();
    } catch (Exception e) {
      if (e instanceof GoogleJsonResponseException
          && ((GoogleJsonResponseException) e).getDetails().getCode() == 404) {
        return null;
      }
      throw new RuntimeException("While fetching " + deviceId, e);
    }
  }

  public String getRegistryId() {
    return cloudIotConfig.registry_id;
  }

  public String getProjectId() {
    return configuration.project_id;
  }

  public String getSiteName() {
    return cloudIotConfig.site_name;
  }
}
