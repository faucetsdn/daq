package com.google.daq.mqtt.validator;

import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.google.cloud.ServiceOptions;
import com.google.cloud.pubsub.v1.AckReplyConsumer;
import com.google.cloud.pubsub.v1.MessageReceiver;
import com.google.cloud.pubsub.v1.Subscriber;
import com.google.cloud.pubsub.v1.SubscriptionAdminClient;
import com.google.cloud.pubsub.v1.SubscriptionAdminClient.ListSubscriptionsPagedResponse;
import com.google.pubsub.v1.ProjectName;
import com.google.pubsub.v1.ProjectSubscriptionName;
import com.google.pubsub.v1.ProjectTopicName;
import com.google.pubsub.v1.PubsubMessage;
import com.google.pubsub.v1.PushConfig;
import com.google.pubsub.v1.Subscription;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingDeque;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.BiConsumer;

class PubSubClient {

  private static final String CONNECT_ERROR_FORMAT = "While connecting to %s/%s";

  private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper()
      .enable(SerializationFeature.INDENT_OUTPUT)
      .setSerializationInclusion(Include.NON_NULL);
  private static final String SUBSCRIPTION_NAME = "daq-validator";
  private static final String
      REFRESH_ERROR_FORMAT = "While refreshing subscription to topic %s subscription %s";

  private static final String PROJECT_ID = ServiceOptions.getDefaultProjectId();
  private static final int REFRESH_DELAY_MS = 5000;

  private final AtomicBoolean active = new AtomicBoolean();
  private final BlockingQueue<PubsubMessage> messages = new LinkedBlockingDeque<>();

  private Subscriber subscriber;

  PubSubClient(String topicId) {
    try {
      ProjectSubscriptionName subscriptionName = ProjectSubscriptionName.of(
          PROJECT_ID, SUBSCRIPTION_NAME);
      refreshSubscription(ProjectTopicName.of(PROJECT_ID, topicId), subscriptionName);
      subscriber = Subscriber.newBuilder(subscriptionName, new MessageProcessor()).build();
      subscriber.startAsync().awaitRunning();
      active.set(true);
    } catch (Exception e) {
      throw new RuntimeException(String.format(CONNECT_ERROR_FORMAT, PROJECT_ID, topicId), e);
    }
  }

  boolean isActive() {
    return active.get();
  }

  @SuppressWarnings("unchecked")
  void processMessage(BiConsumer<Map<String, Object>, Map<String, String>> handler) {
    try {
      PubsubMessage message = messages.take();
      Map<String, String> attributes = message.getAttributesMap();
      String data = message.getData().toStringUtf8();
      Map<String, Object> asMap;
      try {
        asMap = OBJECT_MAPPER.readValue(data, TreeMap.class);
      } catch (JsonProcessingException e) {
        asMap = new ErrorContainer(e, data);
      }
      handler.accept(asMap, attributes);
    } catch (Exception e) {
      throw new RuntimeException("Processing pubsub message for " + getSubscriptionId(), e);
    }
  }

  static class ErrorContainer extends TreeMap<String, Object> {
    ErrorContainer(Exception e, String message) {
      put("exception", e.toString());
      put("message", message);
    }
  }

  private void stop() {
    if (subscriber != null) {
      active.set(false);
      subscriber.stopAsync();
    }
  }

  String getSubscriptionId() {
    return subscriber.getSubscriptionNameString();
  }

  private class MessageProcessor implements MessageReceiver {
    @Override
    public void receiveMessage(PubsubMessage message, AckReplyConsumer consumer) {
      messages.offer(message);
      consumer.ack();
    }
  }

  private Subscription refreshSubscription(ProjectTopicName topicName,
      ProjectSubscriptionName subscriptionName) {
    // Best way to flush the PubSub queue is to turn it off and back on again.
    try (SubscriptionAdminClient subscriptionAdminClient = SubscriptionAdminClient.create()) {
      if (subscriptionExists(subscriptionAdminClient, topicName, subscriptionName)) {
        subscriptionAdminClient.deleteSubscription(subscriptionName);
      }

      Subscription subscription = subscriptionAdminClient.createSubscription(
          subscriptionName, topicName, PushConfig.getDefaultInstance(), 0);

      return subscription;
    } catch (Exception e) {
      throw new RuntimeException(
          String.format(REFRESH_ERROR_FORMAT, topicName, subscriptionName), e);
    }
  }

  private boolean subscriptionExists(SubscriptionAdminClient subscriptionAdminClient,
      ProjectTopicName topicName, ProjectSubscriptionName subscriptionName) {
    ListSubscriptionsPagedResponse listSubscriptionsPagedResponse = subscriptionAdminClient
        .listSubscriptions(ProjectName.of(PROJECT_ID));
    for (Subscription subscription : listSubscriptionsPagedResponse.iterateAll()) {
      if (subscription.getName().equals(subscriptionName.toString())) {
        return true;
      }
    }
    return false;
  }
}
