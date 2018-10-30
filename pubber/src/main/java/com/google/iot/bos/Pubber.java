package com.google.iot.bos;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.api.client.googleapis.auth.oauth2.GoogleCredential;
import com.google.api.client.googleapis.javanet.GoogleNetHttpTransport;
import com.google.api.client.http.HttpRequestInitializer;
import com.google.api.client.json.JsonFactory;
import com.google.api.client.json.jackson2.JacksonFactory;
import com.google.api.services.cloudiot.v1.CloudIot;
import com.google.api.services.cloudiot.v1.CloudIotScopes;
import com.google.api.services.cloudiot.v1.model.Device;
import com.google.api.services.cloudiot.v1.model.DeviceCredential;
import com.google.common.base.Joiner;
import com.google.common.base.Preconditions;
import com.google.common.collect.ImmutableSet;
import com.google.iot.bos.datafmt.AbacabMessage;
import com.google.iot.bos.datafmt.AbacabMessage.PointSet;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.GeneralSecurityException;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Pubber {

  private static final String CLOUD_CRED_EXTENSION = "cred.json";
  private static final String PRIVATE_KEY_EXTENSION = "rsa_private.pkcs8";
  private static final String MAIN_CONFIG_EXTENSION = "main.json";

  private static final Logger LOG = LoggerFactory.getLogger(Pubber.class);
  private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper()
      .setSerializationInclusion(JsonInclude.Include.NON_NULL);

  private static final String POINTSET_TOPIC = "events/pointset";
  private static final String STATE_TOPIC = "state";
  private static final String CONFIG_TOPIC = "config";

  private static final int DEFAULT_MESSAGE_DELAY = 1000;
  private static final String APPLICATION_NAME = "Atmosphere";
  private static final long CONFIG_WAIT_TIME_MS = 10000;

  private static FauxSensor FAUX_ECO2 = new FauxSensor(0.4, 0, 400, 100);
  private static FauxSensor FAUX_HIMID = new FauxSensor(0.42, 0, 50, 20);
  private static FauxSensor FAUX_PM = new FauxSensor(0.41, 0, 10, 2);
  private static FauxSensor FAUX_TVOC = new FauxSensor(0.4, 0.1, 500, 50);

  private final ScheduledExecutorService executor = Executors.newSingleThreadScheduledExecutor();

  private final Configuration configuration;
  private final CloudLogger cloudLogger;
  private final AtomicInteger messageDelayMs = new AtomicInteger(DEFAULT_MESSAGE_DELAY);
  private final CountDownLatch configLatch = new CountDownLatch(1);
  private final Set<String> deviceIds;
  private final CloudIot cloudIoT;

  private MqttPublisher mqttPublisher;
  private ScheduledFuture<?> scheduledFuture;

  public static void main(String[] args) throws Exception {
    if (args.length != 1) {
      throw new IllegalArgumentException("Expected [configPath] as argument");
    }
    Pubber pubber = new Pubber(args[0]);
    pubber.initialize();
    pubber.forEach(pubber::publishStateMessage);
    pubber.synchronizeStart();
    pubber.startExecutor();
  }


  private void startExecutor() {
    long delay = getMessageDelayMs();
    LOG.info("Starting with send message delay " + delay);
    scheduledFuture = executor
        .scheduleAtFixedRate(this::sendTestMessage, delay, delay, TimeUnit.MILLISECONDS);
  }

  private void sendTestMessage() {
    try {
      LOG.info("Sending test messages at " + new Date());
      forEach(this::sendTestMessage);
    } catch (Exception e) {
      LOG.error("Fatal error during execution", e);
      terminate();
    }
  }

  private void forEach(Consumer<String> action) {
    deviceIds.forEach(action);
  }

  private void terminate() {
    try {
      info("Terminating");
      mqttPublisher.close();
      scheduledFuture.cancel(true);
    } catch (Exception e) {
      info("Error terminating: " + e.getMessage());
    } finally {
      cloudLogger.flush();
    }
  }

  private void synchronizeStart() throws InterruptedException {
    boolean result = configLatch.await(CONFIG_WAIT_TIME_MS, TimeUnit.MILLISECONDS);
    LOG.info("synchronized start config result " + result);
  }

  private Pubber(String configRoot) {
    File credentialFile = new File(configRoot + CLOUD_CRED_EXTENSION);
    LOG.info("Configuring with credentials from " + credentialFile.getAbsolutePath());
    cloudIoT = getCloudIot(credentialFile);

    File configurationFile = new File(configRoot + MAIN_CONFIG_EXTENSION);
    LOG.info("Reading configuration from " + configurationFile.getAbsolutePath());
    try {
      configuration = OBJECT_MAPPER.readValue(configurationFile, Configuration.class);
    } catch (Exception e) {
      throw new RuntimeException("While reading configuration file " + configurationFile.getAbsolutePath(), e);
    }
    cloudLogger = new CloudLogger(Pubber.class, credentialFile);
    info("Starting instance for registry " + configuration.registryId);

    if (configuration.deviceId != null) {
      deviceIds = ImmutableSet.of(configuration.deviceId);
    } else {
      deviceIds = listDevices();
    }

    LOG.info("Publishing to device set " + Joiner.on(", ").join(deviceIds));
    configuration.keyFile = configRoot + PRIVATE_KEY_EXTENSION;
  }

  private CloudIot getCloudIot(File credentialFile) {
    try {
      GoogleCredential credential = GoogleCredential
          .fromStream(new FileInputStream(credentialFile))
          .createScoped(CloudIotScopes.all());
      JsonFactory jsonFactory = JacksonFactory.getDefaultInstance();
      HttpRequestInitializer init = new RetryHttpInitializerWrapper(credential);
      return new CloudIot.Builder(
          GoogleNetHttpTransport.newTrustedTransport(), jsonFactory, init)
          .setApplicationName(APPLICATION_NAME).build();
    } catch (GeneralSecurityException | IOException e) {
      LOG.warn("Could not load GCP credentials: " + e.getMessage());
      return null;
    }
  }

  private void initialize() {
    Preconditions.checkState(mqttPublisher == null, "mqttPublisher already defined");
    Preconditions.checkNotNull(configuration.keyFile, "configuration keyFile not defined");
    configuration.keyBytes = getFileBytes(configuration.keyFile);
    mqttPublisher = new MqttPublisher(configuration, this::onMqttReceiveError);

    if (configuration.gatewayId != null) {
      mqttPublisher.registerHandler(configuration.registryId, configuration.gatewayId,
          CONFIG_TOPIC, this::configHandler, AbacabMessage.Config.class);
    } else {
      deviceIds.forEach((deviceId) -> mqttPublisher
          .registerHandler(configuration.registryId, deviceId, CONFIG_TOPIC,
              this::configHandler, AbacabMessage.Config.class));
    }
  }

  private void onMqttReceiveError(Exception e) {
    LOG.error("Error receiving message", e);
  }

  private void info(String msg) {
    LOG.info(msg);
    cloudLogger.info(msg);
  }

  private void configHandler(AbacabMessage.Config config) {
    info("Received new config " + config);
    messageDelayMs.set(DEFAULT_MESSAGE_DELAY);
    info("Publish delay set to " + messageDelayMs.get());
    configLatch.countDown();
  }

  private byte[] getFileBytes(String dataFile) {
    Path dataPath = Paths.get(dataFile);
    try {
      return Files.readAllBytes(dataPath);
    } catch (Exception e) {
      throw new RuntimeException("While getting data from " + dataPath.toAbsolutePath(), e);
    }
  }

  private void sendTestMessage(String deviceId) {
    if (deviceId.equals(configuration.gatewayId)) {
      return;
    }
    info(String.format("Sending test message for %s/%s", configuration.registryId, deviceId));
    PointSet message = new PointSet();
    message.points.put("rht_temp_celsius", FAUX_PM.getReading(deviceId));
    message.points.put("rht_temp_farenheit", FAUX_HIMID.getReading(deviceId));
    message.points.put("rht_humidity_pct", FAUX_HIMID.getReading(deviceId));
    message.points.put("tvoc_eco2_ppm", FAUX_ECO2.getReading(deviceId));
    message.points.put("tvoc_ppb", FAUX_TVOC.getReading(deviceId));
    message.points.put("co2_ppm", FAUX_PM.getReading(deviceId));
    mqttPublisher.publish(configuration.registryId, deviceId, POINTSET_TOPIC, message);
  }

  private void publishStateMessage(String deviceId) {
    info("Sending state message for device " + deviceId);
    AbacabMessage.State message = new AbacabMessage.State();
    mqttPublisher.publish(configuration.registryId, deviceId, STATE_TOPIC, message);
  }

  private long getMessageDelayMs() {
    return messageDelayMs.get();
  }

  private Set<String> listDevices() {
    final String registryPath = String.format("projects/%s/locations/%s/registries/%s",
        configuration.projectId, configuration.cloudRegion, configuration.registryId);

    if (cloudIoT == null) {
      throw new IllegalStateException("No GCP credentials configured.");
    }
    try {
      List<Device> devices = cloudIoT
              .projects()
              .locations()
              .registries()
              .devices()
              .list(registryPath)
              .execute()
              .getDevices();

      Set<String> deviceSet = new HashSet<>();
      if (devices == null) {
        throw new RuntimeException("Devices list is empty");
      }

      devices.stream()
          .filter(this::isProxiedDevice)
          .forEach(device -> deviceSet.add(device.getId()));

      return deviceSet;
    } catch (Exception e) {
      throw new RuntimeException("While fetching devices from " + registryPath, e);
    }
  }

  private boolean isProxiedDevice(Device device) {
    final String devicePath = String.format("projects/%s/locations/%s/registries/%s/devices/%s",
        configuration.projectId, configuration.cloudRegion, configuration.registryId, device.getId());
    try {
      List<DeviceCredential> deviceCredentials = cloudIoT.projects().locations().registries()
          .devices()
          .get(devicePath).execute().getCredentials();
      boolean useProxy = deviceCredentials == null || deviceCredentials.isEmpty();
      LOG.info("Device " + device.getId() + " proxy " + useProxy);
      return useProxy;
    } catch (Exception e) {
      throw new RuntimeException("While getting device config " + devicePath, e);
    }
  }
}
