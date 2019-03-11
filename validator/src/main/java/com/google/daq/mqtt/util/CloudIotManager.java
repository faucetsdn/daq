package com.google.daq.mqtt.util;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.api.client.googleapis.auth.oauth2.GoogleCredential;
import com.google.api.client.googleapis.javanet.GoogleNetHttpTransport;
import com.google.api.client.googleapis.json.GoogleJsonResponseException;
import com.google.api.client.http.HttpRequestInitializer;
import com.google.api.client.json.JsonFactory;
import com.google.api.client.json.jackson2.JacksonFactory;
import com.google.api.services.cloudiot.v1.CloudIot;
import com.google.api.services.cloudiot.v1.CloudIotScopes;
import com.google.api.services.cloudiot.v1.model.Device;
import com.google.api.services.cloudiot.v1.model.DeviceCredential;
import com.google.api.services.cloudiot.v1.model.DeviceRegistry;
import com.google.api.services.cloudiot.v1.model.PublicKeyCredential;
import com.google.common.base.Preconditions;
import com.google.common.collect.ImmutableList;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 */
public class CloudIotManager {

  private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();
  public static final String DEVICE_UPDATE_MASK = "blocked,credentials,metadata";

  private final GcpCreds configuration;
  private final CloudIotConfig cloudIotConfig;
  private final String registryId;

  private CloudIot cloudIotService;
  private String projectPath;
  private CloudIot.Projects.Locations.Registries cloudIotRegistries;

  public CloudIotManager(File gcpCred, File iotConfigFile) {
    configuration = readGcpCreds(gcpCred);
    cloudIotConfig = readCloudIotConfig(iotConfigFile);
    registryId = cloudIotConfig.registry_id;
    initializeCloudIoT(gcpCred);
  }

  static GcpCreds readGcpCreds(File configFile) {
    try {
      return OBJECT_MAPPER.readValue(configFile, GcpCreds.class);
    } catch (Exception e) {
      throw new RuntimeException("While reading config file "+ configFile.getAbsolutePath(), e);
    }
  }

  static CloudIotConfig readCloudIotConfig(File configFile) {
    try {
      return validate(OBJECT_MAPPER.readValue(configFile, CloudIotConfig.class));
    } catch (Exception e) {
      throw new RuntimeException("While reading config file "+ configFile.getAbsolutePath(), e);
    }
  }

  private static CloudIotConfig validate(CloudIotConfig cloudIotConfig) {
    Preconditions.checkNotNull(cloudIotConfig.registry_id, "registry_id not defined");
    Preconditions.checkNotNull(cloudIotConfig.cloud_region, "cloud_region not defined");
    Preconditions.checkNotNull(cloudIotConfig.site_code, "site_code not defined");
    return cloudIotConfig;
  }

  private Set<String> fetchRegistries() {
    try {
      List<DeviceRegistry>
          existingRegistries =
          cloudIotRegistries.list(projectPath).execute().getDeviceRegistries();
      Set<String> remainingRegistries = new HashSet<>();
      existingRegistries.forEach(registry -> remainingRegistries.add(registry.getId()));
      return remainingRegistries;
    } catch (Exception e) {
      throw new RuntimeException("While fetching Cloud IoT project registries list", e);
    }
  }

  private String getRegistryPath(String registryId) {
    return projectPath + "/registries/" + registryId;
  }

  private String getDevicePath(String registryId, String deviceId) {
    return getRegistryPath(registryId) + "/devices/" + deviceId;
  }

  private GoogleCredential authorizeServiceAccount(File credFile) {
    try (FileInputStream credStream = new FileInputStream(credFile)) {
      return GoogleCredential
          .fromStream(credStream)
          .createScoped(CloudIotScopes.all());
    } catch (Exception e) {
      throw new RuntimeException("While reading cred file " + credFile.getAbsolutePath(), e);
    }
  }

  private void initializeCloudIoT(File gcpCredFile) {
    projectPath = "projects/" + configuration.project_id + "/locations/" + cloudIotConfig.cloud_region;
    try {
      GoogleCredential credential = authorizeServiceAccount(gcpCredFile);
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
      Device device = fetchDevice(deviceId);
      if (device == null) {
        createDevice(deviceId, settings);
        return true;
      } else {
        updateDevice(deviceId, settings);
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

  private Device makeDevice(String deviceId, CloudDeviceSettings settings) {
    return new Device()
        .setId(deviceId)
        .setCredentials(settings.credentials)
        .setMetadata(settings.metadata);
  }

  private void createDevice(String deviceId, CloudDeviceSettings settings) throws IOException {
    try {
      cloudIotRegistries.devices().create(getRegistryPath(registryId),
          makeDevice(deviceId, settings)).execute();
    } catch (GoogleJsonResponseException e) {
      throw new RuntimeException("Remote error creating device " + deviceId, e);
    }
  }

  private void updateDevice(String deviceId, CloudDeviceSettings settings) {
    try {
      Device device = makeDevice(deviceId, settings)
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

  public static List<DeviceCredential> makeCredentials(String keyFormat, String keyData) {
    PublicKeyCredential publicKeyCredential = new PublicKeyCredential();
    publicKeyCredential.setFormat(keyFormat);
    publicKeyCredential.setKey(keyData);

    DeviceCredential deviceCredential = new DeviceCredential();
    deviceCredential.setPublicKey(publicKeyCredential);
    return ImmutableList.of(deviceCredential);
  }

  public List<Device> fetchDevices() {
    Preconditions.checkNotNull(cloudIotService, "CloudIoT service not initialized");
    try {
      List<Device> devices = cloudIotRegistries
          .devices()
          .list(getRegistryPath(registryId))
          .execute()
          .getDevices();
      return devices == null ? ImmutableList.of() : devices;
    } catch (Exception e) {
      throw new RuntimeException("While listing devices for registry " + registryId, e);
    }
  }

  public void removeDevice(String registryId, String deviceId) throws IOException {
    try {
      cloudIotRegistries.devices().delete(getDevicePath(registryId, deviceId)).execute();
    } catch (GoogleJsonResponseException e) {
      if (e.getDetails().getCode() == 404) {
        return;
      }
      throw new RuntimeException("Remote error removing device: " + e.getDetails().getMessage());
    }
  }

  public Device fetchDevice(String deviceId) throws IOException {
    try {
      return cloudIotRegistries.devices().get(getDevicePath(registryId, deviceId)).execute();
    } catch (GoogleJsonResponseException e) {
      if (e.getDetails().getCode() == 404) {
        return null;
      }
      throw new RuntimeException("Remote error getting device: " + e.getDetails().getMessage());
    }
  }

  public String getSiteCode() {
    return cloudIotConfig.site_code;
  }
}
