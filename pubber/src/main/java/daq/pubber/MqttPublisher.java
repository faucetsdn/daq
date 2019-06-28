package daq.pubber;

import static com.google.common.base.Preconditions.checkNotNull;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.util.ISO8601DateFormat;
import com.google.common.base.Preconditions;
import com.google.common.cache.CacheBuilder;
import com.google.common.cache.CacheLoader;
import com.google.common.cache.LoadingCache;
import com.google.common.cache.RemovalNotification;
import io.jsonwebtoken.JwtBuilder;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import java.security.KeyFactory;
import java.security.PrivateKey;
import java.security.spec.PKCS8EncodedKeySpec;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallback;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;
import org.joda.time.DateTime;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Handle publishing sensor data to a Cloud IoT MQTT endpoint.
 */
public class MqttPublisher {

  private static final Logger LOG = LoggerFactory.getLogger(MqttPublisher.class);

  private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper()
      .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
      .setDateFormat(new ISO8601DateFormat())
      .setSerializationInclusion(JsonInclude.Include.NON_NULL);

  // Indicate if this message should be a MQTT 'retained' message.
  private static final boolean SHOULD_RETAIN = false;

  private static final int MQTT_QOS = 1;
  private static final String CONFIG_UPDATE_TOPIC_FMT = "/devices/%s/config";
  private static final String UNUSED_ACCOUNT_NAME = "unused";
  private static final int INITIALIZE_TIME_MS = 2000;

  private static final String MESSAGE_TOPIC_FORMAT = "/devices/%s/%s";
  private static final String BROKER_URL_FORMAT = "ssl://%s:%s";
  private static final String CLIENT_ID_FORMAT = "projects/%s/locations/%s/registries/%s/devices/%s";
  private static final int ONE_HOUR_MS = 1000 * 60 * 60;
  private static final int CACHE_EXPIRE_MS = ONE_HOUR_MS;
  private static final int PUBLISH_THREAD_COUNT = 10;
  private static final int CONNECTION_LOCK_TIMEOUT_MS = 30000;
  private static final String HANDLER_KEY_FORMAT = "%s/%s";

  private final Semaphore connectionLock = new Semaphore(1);

  private final LoadingCache<String, MqttClient> mqttClientCache = CacheBuilder.newBuilder()
      .expireAfterAccess(CACHE_EXPIRE_MS, TimeUnit.MILLISECONDS)
      .removalListener(this::clientExpired)
      .build(new ClientLoader());

  private final ExecutorService publisherExecutor =
      Executors.newFixedThreadPool(PUBLISH_THREAD_COUNT);

  private final Configuration configuration;
  private final String registryId;

  private final AtomicInteger publishCounter = new AtomicInteger(0);
  private final AtomicInteger errorCounter = new AtomicInteger(0);
  private final AtomicInteger expiredCounter = new AtomicInteger(0);
  private final Map<String, Consumer<Object>> handlers = new ConcurrentHashMap<>();
  private final Map<String, Class<Object>> handlersType = new ConcurrentHashMap<>();
  private final Consumer<Exception> onError;

  MqttPublisher(Configuration configuration, Consumer<Exception> onError) {
    this.configuration = configuration;
    this.registryId = configuration.registryId;
    this.onError = onError;
    validateCloudIoTOptions();
  }

  void publish(String deviceId, String topic, Object data) {
    Preconditions.checkNotNull(deviceId, "publish deviceId");
    LOG.debug("Publishing in background " + registryId + "/" + deviceId);
    publisherExecutor.submit(() -> publishCore(deviceId, topic, data));
  }

  private void publishCore(String deviceId, String topic, Object data) {
    try {
      String payload = OBJECT_MAPPER.writeValueAsString(data);
      sendMessage(deviceId, getMessageTopic(deviceId, topic), payload.getBytes());
      LOG.debug("Publishing complete " + registryId + "/" + deviceId);
    } catch (Exception e) {
      errorCounter.incrementAndGet();
      LOG.warn(String.format("Publish failed for %s: %s", deviceId, e));
      closeDeviceClient(deviceId);
    }
  }

  private void closeDeviceClient(String deviceId) {
    mqttClientCache.invalidate(deviceId);
  }

  void close() {
    mqttClientCache.invalidateAll();
  }

  long clientCount() {
    return mqttClientCache.size();
  }

  private void validateCloudIoTOptions() {
    try {
      checkNotNull(configuration.bridgeHostname, "bridgeHostname");
      checkNotNull(configuration.bridgePort, "bridgePort");
      checkNotNull(configuration.projectId, "projectId");
      checkNotNull(configuration.cloudRegion, "cloudRegion");
      checkNotNull(configuration.keyBytes, "keyBytes");
      checkNotNull(configuration.algorithm, "algorithm");
    } catch (Exception e) {
      throw new IllegalStateException("Invalid Cloud IoT Options", e);
    }
  }

  private MqttClient newBoundClient(String gatewayId, String deviceId) throws Exception {
    MqttClient mqttClient = mqttClientCache.get(gatewayId);
    try {
      connectMqttClient(mqttClient, gatewayId);
      String topic = String.format("/devices/%s/attach", deviceId);
      byte[] payload = new byte[0];
      LOG.info("Publishing attach message to topic " + topic);
      mqttClient.publish(topic, payload, MQTT_QOS, SHOULD_RETAIN);
    } catch (Exception e) {
      LOG.error(String.format("Error while binding client %s: %s", deviceId, e.toString()));
      return null;
    }
    return mqttClient;
  }

  private MqttClient newMqttClient(String deviceId) {
    try {
      Preconditions.checkNotNull(registryId, "registryId is null");
      Preconditions.checkNotNull(deviceId, "deviceId is null");
      MqttClient mqttClient = new MqttClient(getBrokerUrl(), getClientId(deviceId),
          new MemoryPersistence());
      return mqttClient;
    } catch (Exception e) {
      errorCounter.incrementAndGet();
      throw new RuntimeException("Creating new MQTT client " + deviceId, e);
    }
  }

  private void connectMqttClient(MqttClient mqttClient, String deviceId)
      throws Exception {
    if (!connectionLock.tryAcquire(CONNECTION_LOCK_TIMEOUT_MS, TimeUnit.MILLISECONDS)) {
      throw new RuntimeException("Timeout waiting for connection lock");
    }
    try {
      if (mqttClient.isConnected()) {
        return;
      }
      LOG.info("Attempting connection to " + registryId + ":" + deviceId);

      mqttClient.setCallback(new MqttCallbackHandler(deviceId));
      mqttClient.setTimeToWait(INITIALIZE_TIME_MS);

      MqttConnectOptions options = new MqttConnectOptions();
      // Note that the the Google Cloud IoT only supports MQTT 3.1.1, and Paho requires that we
      // explicitly set this. If you don't set MQTT version, the server will immediately close its
      // connection to your device.
      options.setMqttVersion(MqttConnectOptions.MQTT_VERSION_3_1_1);
      options.setUserName(UNUSED_ACCOUNT_NAME);
      options.setMaxInflight(PUBLISH_THREAD_COUNT * 2);

      // generate the jwt password
      options.setPassword(
          createJwt(configuration.projectId, configuration.keyBytes, configuration.algorithm)
              .toCharArray());

      mqttClient.connect(options);

      subscribeToUpdates(mqttClient, deviceId);
    } finally {
      connectionLock.release();
    }
  }

  private String getClientId(String deviceId) {
    // Create our MQTT client. The mqttClientId is a unique string that identifies this device. For
    // Google Cloud IoT, it must be in the format below.
    return String.format(CLIENT_ID_FORMAT, configuration.projectId, configuration.cloudRegion,
        registryId, deviceId);
  }

  private String getBrokerUrl() {
    // Build the connection string for Google's Cloud IoT MQTT server. Only SSL connections are
    // accepted. For server authentication, the JVM's root certificates are used.
    return String.format(BROKER_URL_FORMAT, configuration.bridgeHostname, configuration.bridgePort);
  }

  private String getMessageTopic(String deviceId, String topic) {
    return String.format(MESSAGE_TOPIC_FORMAT, deviceId, topic);
  }

  private void subscribeToUpdates(MqttClient client, String deviceId) {
    String updateTopic = String.format(CONFIG_UPDATE_TOPIC_FMT, deviceId);
    try {
      client.subscribe(updateTopic);
    } catch (MqttException e) {
      throw new RuntimeException("While subscribing to MQTT topic " + updateTopic, e);
    }
  }

  public PublisherStats getStatistics() {
    return new PublisherStats();
  }

  @SuppressWarnings("unchecked")
  public <T> void registerHandler(String deviceId, String mqttTopic,
      Consumer<T> handler, Class<T> messageType) {
    String key = getHandlerKey(getMessageTopic(deviceId, mqttTopic));
    if (handler == null) {
      handlers.remove(key);
      handlersType.remove(key);
    } else if (handlers.put(key, (Consumer<Object>) handler) == null) {
      handlersType.put(key, (Class<Object>) messageType);
    } else {
      throw new IllegalStateException("Overwriting existing handler for " + key);
    }
  }

  private String getHandlerKey(String configTopic) {
    return String.format(HANDLER_KEY_FORMAT, registryId, configTopic);
  }

  public void connect(String deviceId) {
    getConnectedClient(deviceId);
  }

  private class MqttCallbackHandler implements MqttCallback {

    private final String deviceId;

    MqttCallbackHandler(String deviceId) {
      this.deviceId = deviceId;
    }

    /**
     * @see MqttCallback#connectionLost(Throwable)
     */
    public void connectionLost(Throwable cause) {
      LOG.warn("MQTT Connection Lost", cause);
    }

    /**
     * @see MqttCallback#deliveryComplete(IMqttDeliveryToken)
     */
    public void deliveryComplete(IMqttDeliveryToken token) {
    }

    /**
     * @see MqttCallback#messageArrived(String, MqttMessage)
     */
    public void messageArrived(String topic, MqttMessage message) {
      String handlerKey = getHandlerKey(topic);
      Consumer<Object> handler = handlers.get(handlerKey);
      Class<Object> type = handlersType.get(handlerKey);
      if (handler == null) {
        onError.accept(new RuntimeException("No registered handler for " + handlerKey));
      } else if (message.toString().length() == 0) {
        LOG.warn("Received message is empty for " + handlerKey);
        handler.accept(null);
      } else {
        try {
          handler.accept(OBJECT_MAPPER.readValue(message.toString(), type));
        } catch (Exception e) {
          onError.accept(e);
        }
      }
    }
  }

  private class ClientLoader extends CacheLoader<String, MqttClient>  {
    @Override
    public MqttClient load(String key) throws Exception {
      LOG.info("Creating new publisher-client for " + key);
      return newMqttClient(key);
    }
  }

  private void clientExpired(RemovalNotification<String, MqttClient> notification) {
    try {
      LOG.info("Expired publisher-client for " + notification.getKey());
      expiredCounter.incrementAndGet();
      MqttClient mqttClient = notification.getValue();
      if (mqttClient.isConnected()) {
        LOG.info("Closing connected MqttClient for " + mqttClient.getClientId());
        mqttClient.disconnect();
        mqttClient.close();
      }
    } catch (Exception e) {
      throw new RuntimeException("While closing client " + notification.getKey(), e);
    }
  }

  private void sendMessage(String deviceId, String mqttTopic,
      byte[] mqttMessage) throws Exception {
    LOG.debug("Sending message to " + mqttTopic);
    getConnectedClient(deviceId).publish(mqttTopic, mqttMessage, MQTT_QOS, SHOULD_RETAIN);
    publishCounter.incrementAndGet();
  }

  private MqttClient getConnectedClient(String deviceId) {
    try {
      MqttClient mqttClient = mqttClientCache.get(deviceId);
      connectMqttClient(mqttClient, deviceId);
      return mqttClient;
    } catch (Exception e) {
      throw new RuntimeException("While getting mqtt client " + deviceId + ": " + e.toString(), e);
    }
  }

  /** Load a PKCS8 encoded keyfile from the given path. */
  private PrivateKey loadKeyBytes(byte[] keyBytes, String algorithm) throws Exception {
    try {
      PKCS8EncodedKeySpec spec = new PKCS8EncodedKeySpec(keyBytes);
      KeyFactory kf = KeyFactory.getInstance(algorithm);
      return kf.generatePrivate(spec);
    } catch (Exception e) {
      throw new IllegalArgumentException("Loading key bytes", e);
    }
  }

  /** Create a Cloud IoT JWT for the given project id, signed with the given private key */
  protected String createJwt(String projectId, byte[] privateKeyBytes, String algorithm)
      throws Exception {
    DateTime now = new DateTime();
    // Create a JWT to authenticate this device. The device will be disconnected after the token
    // expires, and will have to reconnect with a new token. The audience field should always be set
    // to the GCP project id.
    JwtBuilder jwtBuilder =
        Jwts.builder()
            .setIssuedAt(now.toDate())
            .setExpiration(now.plusMinutes(60).toDate())
            .setAudience(projectId);

    if (algorithm.equals("RS256")) {
      PrivateKey privateKey = loadKeyBytes(privateKeyBytes, "RSA");
      return jwtBuilder.signWith(SignatureAlgorithm.RS256, privateKey).compact();
    } else if (algorithm.equals("ES256")) {
      PrivateKey privateKey = loadKeyBytes(privateKeyBytes, "EC");
      return jwtBuilder.signWith(SignatureAlgorithm.ES256, privateKey).compact();
    } else {
      throw new IllegalArgumentException(
          "Invalid algorithm " + algorithm + ". Should be one of 'RS256' or 'ES256'.");
    }
  }

  public class PublisherStats {
    public long clientCount = mqttClientCache.size();
    public int publishCount = publishCounter.getAndSet(0);
    public int errorCount = errorCounter.getAndSet(0);
  }
}
