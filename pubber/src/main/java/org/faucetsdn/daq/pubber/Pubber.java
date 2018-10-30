package org.faucetsdn.daq.pubber;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.common.base.Joiner;
import com.google.common.base.Preconditions;
import com.google.common.collect.ImmutableSet;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Date;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;
import com.faucetsdn.daq.abacab.Message;
import com.faucetsdn.daq.abacab.Message.PointSet;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Pubber {

  private static final Logger LOG = LoggerFactory.getLogger(Pubber.class);
  private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper()
      .setSerializationInclusion(JsonInclude.Include.NON_NULL);

  private static final String POINTSET_TOPIC = "events/pointset";
  private static final String STATE_TOPIC = "state";
  private static final String CONFIG_TOPIC = "config";

  private static final int DEFAULT_MESSAGE_DELAY = 1000;
  private static final long CONFIG_WAIT_TIME_MS = 10000;

  private final ScheduledExecutorService executor = Executors.newSingleThreadScheduledExecutor();

  private final Configuration configuration;
  private final AtomicInteger messageDelayMs = new AtomicInteger(DEFAULT_MESSAGE_DELAY);
  private final CountDownLatch configLatch = new CountDownLatch(1);

  private MqttPublisher mqttPublisher;
  private ScheduledFuture<?> scheduledFuture;

  public static void main(String[] args) throws Exception {
    if (args.length != 1) {
      throw new IllegalArgumentException("Expected [configPath] as argument");
    }
    Pubber pubber = new Pubber(args[0]);
    pubber.initialize();
    pubber.synchronizeStart();
    pubber.startExecutor();
  }

  private void startExecutor() {
    long delay = messageDelayMs.get();
    LOG.info("Starting with send message delay " + delay);
    scheduledFuture = executor
        .scheduleAtFixedRate(this::sendTestMessage, delay, delay, TimeUnit.MILLISECONDS);
  }

  private void sendTestMessage() {
    try {
      LOG.info("Sending test messages at " + new Date());
      sendTestMessage(configuration.gatewayId);
    } catch (Exception e) {
      LOG.error("Fatal error during execution", e);
      terminate();
    }
  }

  private void terminate() {
    try {
      info("Terminating");
      mqttPublisher.close();
      scheduledFuture.cancel(true);
    } catch (Exception e) {
      info("Error terminating: " + e.getMessage());
    }
  }

  private void synchronizeStart() throws InterruptedException {
    boolean result = configLatch.await(CONFIG_WAIT_TIME_MS, TimeUnit.MILLISECONDS);
    LOG.info("synchronized start config result " + result);
  }

  private Pubber(String configFile) {
    File configurationFile = new File(configFile);
    LOG.info("Reading configuration from " + configurationFile.getAbsolutePath());
    try {
      configuration = OBJECT_MAPPER.readValue(configurationFile, Configuration.class);
    } catch (Exception e) {
      throw new RuntimeException("While reading configuration file " + configurationFile.getAbsolutePath(), e);
    }
    info("Starting instance for registry " + configuration.registryId);
  }

  private void initialize() {
    Preconditions.checkState(mqttPublisher == null, "mqttPublisher already defined");
    Preconditions.checkNotNull(configuration.keyFile, "configuration keyFile not defined");
    configuration.keyBytes = getFileBytes(configuration.keyFile);
    mqttPublisher = new MqttPublisher(configuration, this::onMqttReceiveError);

    mqttPublisher.registerHandler(configuration.registryId, configuration.gatewayId, CONFIG_TOPIC,
            this::configHandler, Message.Config.class);
  }

  private void onMqttReceiveError(Exception e) {
    LOG.error("Error receiving message", e);
  }

  private void info(String msg) {
    LOG.info(msg);
  }

  private void configHandler(Message.Config config) {
    info("Received new config " + config);
    messageDelayMs.set(DEFAULT_MESSAGE_DELAY);
    info("Publish delay set to " + messageDelayMs.get());
    configLatch.countDown();
    //publishStateMessage(configuration.gatewayId);
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
    info(String.format("Sending test message for %s/%s", configuration.registryId, deviceId));
    PointSet message = new PointSet();
    mqttPublisher.publish(configuration.registryId, deviceId, POINTSET_TOPIC, message);
  }

  private void publishStateMessage(String deviceId) {
    info("Sending state message for device " + deviceId);
    Message.State message = new Message.State();
    mqttPublisher.publish(configuration.registryId, deviceId, STATE_TOPIC, message);
  }
}
