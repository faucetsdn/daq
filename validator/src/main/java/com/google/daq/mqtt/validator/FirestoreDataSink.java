package com.google.daq.mqtt.validator;

import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.api.core.ApiFuture;
import com.google.auth.Credentials;
import com.google.auth.oauth2.GoogleCredentials;
import com.google.cloud.ServiceOptions;
import com.google.cloud.firestore.DocumentReference;
import com.google.cloud.firestore.Firestore;
import com.google.cloud.firestore.FirestoreOptions;
import com.google.cloud.firestore.WriteResult;
import com.google.daq.mqtt.validator.ExceptionMap.ErrorTree;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.Executor;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicReference;

public class FirestoreDataSink {

  private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper().setSerializationInclusion(Include.NON_NULL);
  private static final String CREDENTIAL_ERROR_FORMAT = "Credential file %s defined by %s not found.";
  private static final String VIEW_URL_FORMAT = "https://console.cloud.google.com/firestore/project/%s/database/firestore/data~2Fvalidations~2F%s~2Fdevices";

  private final Firestore db;
  private final String topicName;
  private final String projectId;
  private Executor executor = Executors.newSingleThreadExecutor();
  private final AtomicReference<RuntimeException> oldError = new AtomicReference<>();

  public FirestoreDataSink(String topicName) {
    this.topicName = topicName;
    this.projectId = ServiceOptions.getDefaultProjectId();
    try {
      FirestoreOptions firestoreOptions =
          FirestoreOptions.getDefaultInstance().toBuilder()
              .setCredentials(getProjectCredentials())
              .setProjectId(projectId)
              .setTimestampsInSnapshotsEnabled(true)
              .build();

      db = firestoreOptions.getService();
    } catch (Exception e) {
      throw new RuntimeException("While creating Firestore connection to " + projectId, e);
    }
  }

  private Credentials getProjectCredentials() throws IOException {
    File credentialFile = new File(System.getenv(ServiceOptions.CREDENTIAL_ENV_NAME));
    if (!credentialFile.exists()) {
      throw new RuntimeException(String.format(CREDENTIAL_ERROR_FORMAT, credentialFile.getAbsolutePath(), ServiceOptions.CREDENTIAL_ENV_NAME));
    }
    FileInputStream serviceAccount = new FileInputStream(credentialFile);
    return GoogleCredentials.fromStream(serviceAccount);
  }

  public void validationResult(String deviceId, Map<String, String> attributes, Object data,
      ErrorTree errorTree) {
    if (oldError.get() != null) {
      throw oldError.getAndSet(null);
    }
    try {
      DocumentReference deviceDoc = db.collection("validations").document(topicName)
          .collection("devices").document(deviceId);
      DevicePojo pojo = new DevicePojo();
      pojo.data = data;
      pojo.attributes = attributes;
      pojo.errors = errorTree;
      Object dataMap = OBJECT_MAPPER
          .readValue(OBJECT_MAPPER.writeValueAsString(pojo), HashMap.class);
      ApiFuture<WriteResult> resultApiFuture = deviceDoc.set(dataMap);
      resultApiFuture.addListener(new ResultListener(resultApiFuture), executor);
    } catch (Exception e) {
      throw new RuntimeException("While writing result for " + deviceId, e);
    }
  }

  public String getViewUrl() {
    return String.format(VIEW_URL_FORMAT, projectId, topicName);
  }

  static class DevicePojo {
    public Object data;
    public Map<String, String> attributes;
    public ErrorTree errors;
  }

  class ResultListener implements Runnable {

    final private ApiFuture<WriteResult> resultApiFuture;

    public ResultListener(ApiFuture<WriteResult> resultApiFuture) {
      this.resultApiFuture = resultApiFuture;
    }

    @Override
    public void run() {
      try {
        resultApiFuture.get();
      } catch (Exception e) {
        oldError.set(new RuntimeException("Write future", e));
      }
    }
  }
}
