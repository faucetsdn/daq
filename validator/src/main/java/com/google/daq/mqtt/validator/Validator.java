package com.google.daq.mqtt.validator;

import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.google.common.base.Preconditions;
import com.google.common.base.Strings;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.daq.mqtt.validator.ExceptionMap.ErrorTree;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FilenameFilter;
import java.io.InputStream;
import java.io.PrintStream;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import org.everit.json.schema.Schema;
import org.everit.json.schema.ValidationException;
import org.everit.json.schema.loader.SchemaLoader;
import org.json.JSONObject;
import org.json.JSONTokener;

public class Validator {

  private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper()
      .enable(SerializationFeature.INDENT_OUTPUT)
      .setSerializationInclusion(Include.NON_NULL);
  private static final String ERROR_FORMAT_INDENT = "  ";
  private static final String JSON_SUFFIX = ".json";
  private static final String SCHEMA_VALIDATION_FORMAT = "Validating %d schemas";
  private static final String TARGET_VALIDATION_FORMAT = "Validating %d files against %s";
  private static final String PUBSUB_PREFIX = "pubsub:";
  private static final File OUT_BASE_FILE = new File("out");
  private static final String ATTRIBUTE_FILE_FORMAT = "%s_%s.attr";
  private static final String MESSAGE_FILE_FORMAT = "%s_%s.json";
  private static final String ERROR_FILE_FORMAT = "%s_%s.out";
  private static final Pattern DEVICE_ID_PATTERN =
      Pattern.compile("^([a-z][_a-z0-9-]*[a-z0-9]|[A-Z][_A-Z0-9-]*[A-Z0-9])$");
  private static final String DEVICE_MATCH_FORMAT = "DeviceId %s must match pattern %s";
  private static final String SCHEMA_SKIP_FORMAT = "Skipping schema definition '%s' for %s";
  private static final String ENVELOPE_SCHEMA_ID = "envelope";
  private FirestoreDataSink dataSink;
  private String schemaSpec;

  public static void main(String[] args) {
    Validator validator = new Validator();
    try {
      if (args.length < 2 || args.length > 3) {
        throw new IllegalArgumentException("Args: [schema] [target] [ignore_csv]?");
      }
      validator.setSchemaSpec(args[0]);
      String targetSpec = args[1];
      String ignoreSpec = args.length > 2 ? args[2] : null;
      if (targetSpec.startsWith(PUBSUB_PREFIX)) {
        String topicName = targetSpec.substring(PUBSUB_PREFIX.length());
        validator.validatePubSub(topicName, ignoreSpec);
      } else {
        validator.validateFilesOutput(targetSpec);
      }
    } catch (ExceptionMap | ValidationException processingException) {
      System.exit(2);
    } catch (Exception e) {
      e.printStackTrace();
      System.exit(-1);
    }
    System.exit(0);
  }

  private void setSchemaSpec(String schemaSpec) {
    this.schemaSpec = schemaSpec;
  }

  private void validatePubSub(String topicName, String ignoreSpec) {
    Set<String> ignoreSubSet = convertIgnoreSet(ignoreSpec);
    Map<String, Schema> schemaMap = new HashMap<>();
    for (File schemaFile : makeFileList(schemaSpec)) {
      Schema schema = getSchema(schemaFile);
       String fullName = schemaFile.getName();
      String schemaName = schemaFile.getName()
          .substring(0, fullName.length() - JSON_SUFFIX.length());
      schemaMap.put(schemaName, schema);
    }
    if (!schemaMap.containsKey(ENVELOPE_SCHEMA_ID)) {
      throw new RuntimeException("Missing schema for attribute validation: " + ENVELOPE_SCHEMA_ID);
    }
    dataSink = new FirestoreDataSink();
    System.out.println("Ignoring subfolders " + ignoreSubSet);
    System.out.println("Results will be uploaded to " + dataSink.getViewUrl());
    OUT_BASE_FILE.mkdirs();
    System.out.println("Also found in such directories as " + OUT_BASE_FILE.getAbsolutePath());
    System.out.println("Connecting to pubsub topic " + topicName);
    PubSubClient client = new PubSubClient(topicName);
    System.out.println("Entering pubsub message loop on " + client.getSubscriptionId());
    while(client.isActive()) {
      try {
        client.processMessage(
            (message, attributes) -> validateMessage(ignoreSubSet, schemaMap, message, attributes));
      } catch (Exception e) {
        e.printStackTrace();
      }
    }
    System.out.println("Message loop complete");
  }

  private Set<String> convertIgnoreSet(String ignoreSpec) {
    if (ignoreSpec == null) {
      return ImmutableSet.of();
    }
    return Arrays.stream(ignoreSpec.split(",")).collect(Collectors.toSet());
  }

  private void validateMessage(Set<String> ignoreSubSet,
      Map<String, Schema> schemaMap, Map<String, Object> message,
      Map<String, String> attributes) {
    try {
      String deviceId = attributes.get("deviceId");
      String subFolder = attributes.get("subFolder");
      String schemaId = subFolder;

      File attributesFile = new File(OUT_BASE_FILE, String.format(ATTRIBUTE_FILE_FORMAT, schemaId, deviceId));
      OBJECT_MAPPER.writeValue(attributesFile, attributes);

      File messageFile = new File(OUT_BASE_FILE, String.format(MESSAGE_FILE_FORMAT, schemaId, deviceId));
      OBJECT_MAPPER.writeValue(messageFile, message);

      File errorFile = new File(OUT_BASE_FILE, String.format(ERROR_FILE_FORMAT, schemaId, deviceId));
      errorFile.delete();

      try {
        Preconditions.checkNotNull(deviceId, "Missing deviceId in message");
        if (Strings.isNullOrEmpty(subFolder)
            || ignoreSubSet.contains(subFolder)
            || !schemaMap.containsKey(schemaId)) {
          throw new IllegalArgumentException(String.format(SCHEMA_SKIP_FORMAT, schemaId, deviceId));
        }
      } catch (Exception e) {
        System.out.println(e.getMessage());
        OBJECT_MAPPER.writeValue(errorFile, e.getMessage());
        return;
      }
      try {
        validateMessage(schemaMap.get(ENVELOPE_SCHEMA_ID), attributes);
        validateDeviceId(deviceId);
      } catch (ExceptionMap | ValidationException e) {
        processViolation(message, attributes, deviceId, ENVELOPE_SCHEMA_ID, attributesFile, errorFile, e);
      }
      try {
        validateMessage(schemaMap.get(schemaId), message);
        dataSink.validationResult(deviceId, schemaId, attributes, message, null);
        System.out.println("Success validating " + messageFile);
      } catch (ExceptionMap | ValidationException e) {
        processViolation(message, attributes, deviceId, schemaId, messageFile, errorFile, e);
      }
    } catch (Exception e){
      e.printStackTrace();
    }
  }

  private void processViolation(Map<String, Object> message, Map<String, String> attributes,
      String deviceId, String schemaId, File inputFile, File errorFile, RuntimeException e)
      throws FileNotFoundException {
    System.out.println("Error validating " + inputFile + ": " + e.getMessage());
    ErrorTree errorTree = ExceptionMap.format(e, ERROR_FORMAT_INDENT);
    dataSink.validationResult(deviceId, schemaId, attributes, message, errorTree);
    try (PrintStream errorOut = new PrintStream(errorFile)) {
      errorTree.write(errorOut);
    }
  }

  private void validateDeviceId(String deviceId) {
    if (!DEVICE_ID_PATTERN.matcher(deviceId).matches()) {
      throw new ExceptionMap(String.format(DEVICE_MATCH_FORMAT, deviceId, DEVICE_ID_PATTERN.pattern()));
    }
  }

  private void validateFiles(String schemaSpec, String targetSpec) {
    List<File> schemaFiles = makeFileList(schemaSpec);
    if (schemaFiles.size() == 0) {
      throw new RuntimeException("Cowardly refusing to validate against zero schemas");
    }
    List<File> targetFiles = makeFileList(targetSpec);
    if (targetFiles.size() == 0) {
      throw new RuntimeException("Cowardly refusing to validate against zero targets");
    }
    ExceptionMap schemaExceptions = new ExceptionMap(
        String.format(SCHEMA_VALIDATION_FORMAT, schemaFiles.size()));
    for (File schemaFile : schemaFiles) {
      try {
        Schema schema = getSchema(schemaFile);
        ExceptionMap validateExceptions = new ExceptionMap(
            String.format(TARGET_VALIDATION_FORMAT, targetFiles.size(), schemaFile));
        for (File targetFile : targetFiles) {
          try {
            System.out.println("Validating " + targetFile.getName() + " against " + schemaFile.getName());
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

  private void validateFilesOutput(String targetSpec) {
    try {
      validateFiles(schemaSpec, targetSpec);
    } catch (ExceptionMap | ValidationException processingException) {
      ErrorTree errorTree = ExceptionMap.format(processingException, ERROR_FORMAT_INDENT);
      errorTree.write(System.err);
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
    }
    boolean isDir = target.isDirectory();
    String prefix = isDir ? "" : target.getName();
    File parent = isDir ? target : target.getAbsoluteFile().getParentFile();
    if (!parent.isDirectory()) {
      throw new RuntimeException("Parent directory not found " + parent.getAbsolutePath());
    }

    FilenameFilter filter = (dir, file) -> file.startsWith(prefix) && file.endsWith(JSON_SUFFIX);
    String[] fileNames = parent.list(filter);

    return Arrays.stream(fileNames).map(name -> new File(parent, name))
        .collect(Collectors.toList());
  }

  private void validateMessage(Schema schema, Object message) {
    final String stringMessage;
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
      throw new RuntimeException("Against input " + targetFile, e);
    }
  }


}
