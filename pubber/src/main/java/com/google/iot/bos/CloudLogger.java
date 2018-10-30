package com.google.iot.bos;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.auth.Credentials;
import com.google.auth.oauth2.GoogleCredentials;
import com.google.cloud.MonitoredResource;
import com.google.cloud.logging.LogEntry;
import com.google.cloud.logging.Logging;
import com.google.cloud.logging.LoggingOptions;
import com.google.cloud.logging.Payload;
import com.google.cloud.logging.Severity;
import com.google.common.base.Preconditions;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CloudLogger {

  private static final Logger LOG = LoggerFactory.getLogger(CloudLogger.class);

  private static final MonitoredResource MONITORED_RESOURCE =
      MonitoredResource.newBuilder("global").build();
  private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper()
      .setSerializationInclusion(JsonInclude.Include.NON_NULL);

  private final Logging logging;
  private final String logName;

  public CloudLogger(Class<?> target, File credentialFile) {
    Logging localLogger;
    this.logName = target.getSimpleName();
    try {
      Credentials credentials = GoogleCredentials.fromStream(new FileInputStream(credentialFile));
      String projectId = getProjectName(credentialFile);
      localLogger = LoggingOptions.newBuilder()
          .setProjectId(projectId)
          .setCredentials(credentials)
          .build().getService();
    } catch (FileNotFoundException e) {
      LOG.warn("Cred file not found, skipping cloud logging: " + credentialFile.getAbsolutePath());
      localLogger = null;
    } catch (Exception e) {
      throw new RuntimeException(String.format("While configuring from %s",
          credentialFile.getAbsoluteFile()), e);
    }
    logging = localLogger;
  }

  public void flush() {
    logging.flush();
  }

  public void close() throws Exception {
    logging.close();
  }

  public void warn(Object data) {
    log(Severity.WARNING, data);
  }

  void debug(Object data) {
    log(Severity.DEBUG, data);
  }

  public void info(Object data) {
    log(Severity.INFO, data);
  }

  public void error(Object data) {
    log(Severity.ERROR, data);
  }

  @SuppressWarnings("unchecked")
  void log(Severity severity, Object data) {
    if (logging == null) {
      return;
    }
    boolean primitiveType = (data == null) || data.getClass().isPrimitive();
    final LogEntry.Builder entry;
    if (primitiveType || data instanceof String) {
      entry = LogEntry.newBuilder(Payload.StringPayload.of(Objects.toString(data)));
    } else {
      Map<String, Object> jsonMap = OBJECT_MAPPER.convertValue(data, Map.class);
      entry = LogEntry.newBuilder(Payload.JsonPayload.of(jsonMap));
    }

    entry.setSeverity(severity);
    logging.write(Collections.singleton(entry.build()),
        Logging.WriteOption.logName(logName),
        Logging.WriteOption.resource(MONITORED_RESOURCE));
  }

  @SuppressWarnings("unchecked")
  private static String getProjectName(File credentialFile) throws Exception {
    Map<String, Object> mapType = new HashMap<>();
    Map<String, Object> credentialMap =
        OBJECT_MAPPER.readValue(credentialFile, mapType.getClass());
    return Preconditions
        .checkNotNull((String) credentialMap.get("project_id"), "config file projectId");
  }

}
