package com.google.daq.mqtt.util;

import static com.google.daq.mqtt.util.ConfigUtil.readCloudIotConfig;
import static com.google.daq.mqtt.util.ConfigUtil.readGcpCreds;

import com.google.api.core.ApiFuture;
import com.google.cloud.ServiceOptions;
import com.google.cloud.pubsub.v1.Publisher;
import com.google.common.base.Preconditions;
import com.google.protobuf.ByteString;
import com.google.pubsub.v1.ProjectTopicName;
import com.google.pubsub.v1.PubsubMessage;
import com.google.pubsub.v1.PubsubMessage.Builder;
import io.grpc.LoadBalancerProvider;
import io.grpc.LoadBalancerRegistry;
import io.grpc.internal.AutoConfiguredLoadBalancerFactory;
import io.grpc.internal.PickFirstLoadBalancerProvider;
import java.io.File;
import java.nio.charset.Charset;
import java.util.Map;

public class PubSubPusher {

  public static final String PROJECT_MISMATCH_FORMAT = "project mismatch %s != %s";
  private final String projectId = ServiceOptions.getDefaultProjectId();

  private final GcpCreds configuration;
  private final CloudIotConfig cloudIotConfig;
  private final Publisher publisher;
  private final String registrar_topic;

  {
    // Why this needs to be done there is no rhyme or reason.
    LoadBalancerRegistry.getDefaultRegistry().register(new PickFirstLoadBalancerProvider());
  }

  public PubSubPusher(File gcpCred, File iotConfigFile) {
    try {
      configuration = readGcpCreds(gcpCred);
      cloudIotConfig = validate(readCloudIotConfig(iotConfigFile));
      registrar_topic = cloudIotConfig.registrar_topic;
      ProjectTopicName topicName =
          ProjectTopicName.of(configuration.project_id, registrar_topic);
      Preconditions.checkState(projectId.equals(configuration.project_id),
          String.format(PROJECT_MISMATCH_FORMAT, projectId, configuration.project_id));
      publisher = Publisher.newBuilder(topicName).build();
    } catch (Exception e) {
      throw new RuntimeException("While creating PubSubPublisher", e);
    }
  }

  public String sendMessage(Map<String, String> attributes, String body) {
    try {
      PubsubMessage message = PubsubMessage.newBuilder()
          .setData(ByteString.copyFrom(body, Charset.defaultCharset()))
          .putAllAttributes(attributes)
          .build();
      ApiFuture<String> publish = publisher.publish(message);
      return publish.get();
    } catch (Exception e) {
      throw new RuntimeException("While sending to topic " + registrar_topic, e);
    }
  }

  public void shutdown() {
    try {
      publisher.publishAllOutstanding();
      publisher.shutdown();
      System.err.println("Done with PubSubPusher");
    } catch (Exception e) {
      throw new RuntimeException("While shutting down publisher" + registrar_topic, e);
    }
  }

  private CloudIotConfig validate(CloudIotConfig readCloudIotConfig) {
    Preconditions.checkNotNull(readCloudIotConfig.registrar_topic, "registrar_topic not defined");
    return readCloudIotConfig;
  }
}
