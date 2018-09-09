package com.google.daq.mqtt.validator;

import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.common.collect.ImmutableList;
import com.google.daq.mqtt.validator.ExceptionMap.ErrorTree;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import org.everit.json.schema.Schema;
import org.everit.json.schema.ValidationException;
import org.everit.json.schema.loader.SchemaLoader;
import org.json.JSONObject;
import org.json.JSONTokener;

public class Validator {

  private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper().setSerializationInclusion(Include.NON_NULL);
  private static final String ERROR_FORMAT_INDENT = "  ";
  private static final String JSON_SUFFIX = ".json";
  private static final String SCHEMA_VALIDATION_FORMAT = "Validating %d schemas";
  private static final String TARGET_VALIDATION_FORMAT = "Validating %d files against %s";
  private static final String PUBSUB_PREFIX = "pubsub:";
  private static final String MESSAGE_FILE_FORMAT = "out/message%s.json";
  private static final Pattern DEVICE_ID_PATTERN = Pattern.compile("[a-zA-Z]+[a-zA-Z0-9_]+[a-zA-Z0-9]+");
  private static final String DEVICE_MATCH_FORMAT = "DeviceId %s must match pattern %s";

  public static void main(String[] args) {
    Validator validator = new Validator();
    try {
      if (args.length != 2) {
        throw new IllegalArgumentException("Args: [schema] [target]");
      }
      String schemaSpec = args[0];
      String targetSpec = args[1];
      if (targetSpec.startsWith(PUBSUB_PREFIX)) {
        validator.validatePubSub(schemaSpec, targetSpec.substring(PUBSUB_PREFIX.length()));
      } else {
        validator.validateFilesOutput(schemaSpec, targetSpec);
      }
    } catch (ExceptionMap | ValidationException processingException) {
      System.exit(2);
    } catch (Exception e) {
      e.printStackTrace();
      System.exit(-1);
    }
    System.exit(0);
  }

  private void validatePubSub(String schemaSpec, String topicName) {
    System.out.println("Connecting to pubsub topic " + topicName);
    List<File> schemaFiles = makeFileList(schemaSpec);
    if (schemaFiles.size() != 1) {
      throw new IllegalArgumentException("Can only validate stream against single schema");
    }
    Schema schema = getSchema(schemaFiles.get(0));
    PubSubClient client = new PubSubClient(topicName);
    FirestoreDataSink dataSink = new FirestoreDataSink(topicName);
    System.out.println("Results will be uploaded to " + dataSink.getViewUrl());
    System.out.println("Entering pubsub message loop on " + client.getSubscriptionId());
    while(client.isActive()) {
      client.processMessage((data, attributes) -> {
        String deviceId = attributes.get("deviceId");
        String devicePostfix = "_" + deviceId;
        File messageFile = new File(String.format(MESSAGE_FILE_FORMAT, devicePostfix));
        writeClientMessage(data, messageFile);
        try {
          validateDeviceId(deviceId);
          validateString(schema, data);
          dataSink.validationResult(deviceId, attributes, data, null);
        } catch (Exception e) {
          System.out.println(
              "Error validating " + messageFile + ": " + e.getMessage());
          ErrorTree errorTree = ExceptionMap.format(e, ERROR_FORMAT_INDENT, null);
          dataSink.validationResult(deviceId, attributes, data, errorTree);
        }
      });
    }
    System.out.println("Message loop complete");
  }

  private String validateDeviceId(String deviceId) {
    if (!DEVICE_ID_PATTERN.matcher(deviceId).matches()) {
      throw new RuntimeException(String.format(DEVICE_MATCH_FORMAT, deviceId, DEVICE_ID_PATTERN.pattern()));
    }
    return deviceId;
  }

  private void writeClientMessage(Object message, File messageFile) {
    try {
      OBJECT_MAPPER.writeValue(messageFile, message);
    } catch (Exception e) {
      throw new RuntimeException("While writing message to " + messageFile.getAbsolutePath(), e);
    }
  }

  void validateFiles(String schemaSpec, String targetSpec) {
    List<File> schemaFiles = makeFileList(schemaSpec);
    List<File> targetFiles = makeFileList(targetSpec);
    ExceptionMap schemaExceptions = new ExceptionMap(String.format(SCHEMA_VALIDATION_FORMAT, schemaFiles.size()));
    for (File schemaFile : schemaFiles) {
      try {
        Schema schema = getSchema(schemaFile);
        ExceptionMap validateExceptions = new ExceptionMap(String.format(TARGET_VALIDATION_FORMAT, targetFiles.size(), schemaFile));
        for (File targetFile : targetFiles) {
          try {
            validateFile(targetFile, schema);
          } catch (Exception e) {
            validateExceptions.put(targetFile.getName(), e);
          }
        }
        validateExceptions.throwIfNotEmpty();
      } catch (Exception e) {
        schemaExceptions.put(schemaFile.getName(), e);
      }
    }
    schemaExceptions.throwIfNotEmpty();
  }

  void validateFilesOutput(String schemaSpec, String targetSpec) throws IOException {
    try {
      validateFiles(schemaSpec, targetSpec);
    } catch (ExceptionMap | ValidationException processingException) {
      ExceptionMap
          .format(processingException, ERROR_FORMAT_INDENT, System.err);
      throw processingException;
    }
  }

  private Schema getSchema(File schemaFile) {
    try (InputStream schemaStream = new FileInputStream(schemaFile)) {
      JSONObject rawSchema = new JSONObject(new JSONTokener(schemaStream));
      return SchemaLoader.load(rawSchema);
    } catch (Exception e) {
      throw new RuntimeException("While loading schema " + schemaFile.getAbsolutePath(), e);
    }
  }

  private List<File> makeFileList(String spec) {
    File target = new File(spec);
    if (target.isFile()) {
      return ImmutableList.of(target);
    } else {
      String[] fileNames = Objects
          .requireNonNull(target.list((dir, file) -> file.endsWith(JSON_SUFFIX)), "Invalid directory " + target.getAbsolutePath());
      return Arrays.stream(fileNames).map(name -> new File(spec, name))
          .collect(Collectors.toList());
    }
  }

  private void validateString(Schema schema, Object message) {
    String stringMessage;
    try {
      stringMessage = OBJECT_MAPPER.writeValueAsString(message);
    } catch (Exception e) {
      throw new RuntimeException("While converting to string", e);
    }
    schema.validate(new JSONObject(new JSONTokener(stringMessage)));
  }

  private void validateFile(File targetFile, Schema schema) {
    try (InputStream targetStream = new FileInputStream(targetFile)) {
      schema.validate(new JSONObject(new JSONTokener(targetStream)));
    } catch (Exception e) {
      throw new RuntimeException("Against target file " + targetFile, e);
    }
  }


}
