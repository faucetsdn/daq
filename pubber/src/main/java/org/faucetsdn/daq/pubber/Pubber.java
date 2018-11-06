package org.faucetsdn.daq.pubber;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.faucetsdn.daq.abacab.Message;
import com.faucetsdn.daq.abacab.Message.PointSet;
import com.faucetsdn.daq.abacab.Message.PointSetState;
import com.faucetsdn.daq.abacab.Report;
import com.faucetsdn.daq.abacab.Message.State;
import com.google.common.base.Preconditions;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Pubber {

  private static final Logger LOG = LoggerFactory.getLogger(Pubber.class);
  private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper()
      .setSerializationInclusion(JsonInclude.Include.NON_NULL);

  private static final String POINTSET_TOPIC = "events/pointset";
  private static final String STATE_TOPIC = "state";
  private static final String CONFIG_TOPIC = "config";

  private static final int MIN_REPORT_MS = 200;
  private static final int DEFAULT_REPORT_MS = 1000;
  private static final int CONFIG_WAIT_TIME_MS = 10000;
  private static final int STATE_THROTTLE_MS = 1500;
  private static final String CONFIG_ERROR_STATUS_KEY = "config_error";

  private final ScheduledExecutorService executor = Executors.newSingleThreadScheduledExecutor();

  private final Configuration configuration;
  private final AtomicInteger messageDelayMs = new AtomicInteger(DEFAULT_REPORT_MS);
  private final CountDownLatch configLatch = new CountDownLatch(1);

  private final State deviceState = new State();
  private final PointSet devicePoints = new PointSet();
  private final Set<AbstractPoint> allPoints = new HashSet<>();

  private MqttPublisher mqttPublisher;
  private ScheduledFuture<?> scheduledFuture;
  private long lastStateTimeMs;

  public static void main(String[] args) throws Exception {
    if (args.length != 1) {
      throw new IllegalArgumentException("Expected [configPath] as argument");
    }
    Pubber pubber = new Pubber(args[0]);
    pubber.initialize();
    pubber.synchronizeStart();
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

    initializeDevice();
    addPoint(new RandomPoint("superimposition_reading", 0, 100, "Celsius"));
    addPoint(new RandomPoint("recalcitrant_angle", 0, 360, "deg" ));
    addPoint(new RandomPoint("faulty_finding", 1, 1, "truth"));
  }

  private void initializeDevice() {
    deviceState.system.make_model = "DAQ_pubber";
    deviceState.system.firmware.version = "v1";
    deviceState.pointset = new PointSetState();
  }

  private void startExecutor() {
    cancelExecutor();
    int delay = messageDelayMs.get();
    LOG.info("Starting executor with send message delay " + delay);
    scheduledFuture = executor
        .scheduleAtFixedRate(this::sendMessages, delay, delay, TimeUnit.MILLISECONDS);
  }

  private void cancelExecutor() {
    if (scheduledFuture != null) {
      scheduledFuture.cancel(false);
      scheduledFuture = null;
    }
  }

  private void sendMessages() {
    try {
      sendDeviceMessage(configuration.gatewayId);
      updatePoints();
    } catch (Exception e) {
      LOG.error("Fatal error during execution", e);
      terminate();
    }
  }

  private void updatePoints() {
    allPoints.forEach(AbstractPoint::updateData);
  }

  private void terminate() {
    try {
      info("Terminating");
      mqttPublisher.close();
      cancelExecutor();
    } catch (Exception e) {
      info("Error terminating: " + e.getMessage());
    }
  }

  private void synchronizeStart() throws InterruptedException {
    boolean result = configLatch.await(CONFIG_WAIT_TIME_MS, TimeUnit.MILLISECONDS);
    LOG.info("synchronized start config result " + result);
  }

  private void addPoint(AbstractPoint point) {
    String pointName = point.getName();
    if (devicePoints.points.put(pointName, point.getData()) != null) {
      throw new IllegalStateException("Duplicate pointName " + pointName);
    }
    deviceState.pointset.points.put(pointName, point.getState());
    allPoints.add(point);
  }

  private void initialize() {
    Preconditions.checkState(mqttPublisher == null, "mqttPublisher already defined");
    Preconditions.checkNotNull(configuration.keyFile, "configuration keyFile not defined");
    configuration.keyBytes = getFileBytes(configuration.keyFile);
    mqttPublisher = new MqttPublisher(configuration, this::reportError);
    mqttPublisher.registerHandler(configuration.gatewayId, CONFIG_TOPIC,
            this::configHandler, Message.Config.class);
    mqttPublisher.connect(configuration.gatewayId);
  }

  private void reportError(Exception toReport) {
    if (toReport != null) {
      LOG.error("Error receiving message: " + toReport);
      Report report = new Report(toReport);
      deviceState.system.statuses.put(CONFIG_ERROR_STATUS_KEY, report);
      publishStateMessage(configuration.gatewayId);
    } else {
      Report previous = deviceState.system.statuses.remove(CONFIG_ERROR_STATUS_KEY);
      if (previous != null) {
        publishStateMessage(configuration.gatewayId);
      }
    }
  }

  private void info(String msg) {
    LOG.info(msg);
  }

  private void configHandler(Message.Config config) {
    try {
      info("Received new config " + config);
      int previous = messageDelayMs.get();
      if (config != null) {
        Integer reportInterval = config.system == null ? null : config.system.report_interval_ms;
        int actualInterval = Integer.max(MIN_REPORT_MS,
            reportInterval == null ? DEFAULT_REPORT_MS : reportInterval);
        messageDelayMs.set(actualInterval);
        deviceState.system.last_config = config.timestamp;
      }
      if (scheduledFuture == null || previous != scheduledFuture.getDelay(TimeUnit.MILLISECONDS)) {
        startExecutor();
      }
      configLatch.countDown();
      publishStateMessage(configuration.gatewayId);
      reportError(null);
    } catch (Exception e) {
      reportError(e);
    }
  }

  private byte[] getFileBytes(String dataFile) {
    Path dataPath = Paths.get(dataFile);
    try {
      return Files.readAllBytes(dataPath);
    } catch (Exception e) {
      throw new RuntimeException("While getting data from " + dataPath.toAbsolutePath(), e);
    }
  }

  private void sendDeviceMessage(String deviceId) {
    info(String.format("Sending test message for %s/%s", configuration.registryId, deviceId));
    mqttPublisher.publish(deviceId, POINTSET_TOPIC, devicePoints);
  }

  private void publishStateMessage(String deviceId) {
    lastStateTimeMs = sleepUntil(lastStateTimeMs + STATE_THROTTLE_MS);
    info("Sending state message for device " + deviceId);
    mqttPublisher.publish(deviceId, STATE_TOPIC, deviceState);
  }

  private long sleepUntil(long targetTimeMs) {
    long currentTime = System.currentTimeMillis();
    long delay = targetTimeMs - currentTime;
    try {
      if (delay > 0) {
        Thread.sleep(delay);
      }
      return System.currentTimeMillis();
    } catch (Exception e) {
      throw new RuntimeException("While sleeping for " + delay, e);
    }
  }
}
