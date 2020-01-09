package com.google.daq.mqtt.validator;

import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.util.StdDateFormat;
import com.google.cloud.ServiceOptions;
import com.google.common.base.Preconditions;
import com.google.common.base.Strings;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.daq.mqtt.util.CloudIotConfig;
import com.google.daq.mqtt.util.ConfigUtil;
import com.google.daq.mqtt.util.ExceptionMap;
import com.google.daq.mqtt.util.ExceptionMap.ErrorTree;
import com.google.daq.mqtt.util.FirestoreDataSink;
import com.google.daq.mqtt.util.PubSubClient;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FilenameFilter;
import java.io.InputStream;
import java.io.PrintStream;
import java.net.URL;
import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import org.everit.json.schema.Schema;
import org.everit.json.schema.ValidationException;
import org.everit.json.schema.loader.SchemaClient;
import org.everit.json.schema.loader.SchemaLoader;
import org.json.JSONObject;
import org.json.JSONTokener;

public class Validator {

  private static final SimpleDateFormat DATE_FORMAT = new SimpleDateFormat("dd-MM-yyyy hh:mm");

  private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper()
      .enable(SerializationFeature.INDENT_OUTPUT)
      .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
      .setDateFormat(new StdDateFormat())
      .setSerializationInclusion(Include.NON_NULL);

  private static final String ERROR_FORMAT_INDENT = "  ";
  private static final String JSON_SUFFIX = ".json";
  private static final String SCHEMA_VALIDATION_FORMAT = "Validating %d schemas";
  private static final String TARGET_VALIDATION_FORMAT = "Validating %d files against %s";
  private static final String PUBSUB_PREFIX = "pubsub:";
  private static final File OUT_BASE_FILE = new File("validations");
  private static final String DEVICE_FILE_FORMAT = "devices/%s";
  private static final String ATTRIBUTE_FILE_FORMAT = "%s.attr";
  private static final String MESSAGE_FILE_FORMAT = "%s.json";
  private static final String ERROR_FILE_FORMAT = "%s.out";
  private static final Pattern DEVICE_ID_PATTERN =
      Pattern.compile("^([a-z][_a-z0-9-]*[a-z0-9]|[A-Z][_A-Z0-9-]*[A-Z0-9])$");
  private static final String DEVICE_MATCH_FORMAT = "DeviceId %s must match pattern %s";
  private static final String SCHEMA_SKIP_FORMAT = "Unknown schema subFolder '%s' for %s";
  private static final String ENVELOPE_SCHEMA_ID = "envelope";
  private static final String METADATA_JSON = "metadata.json";
  private static final String DEVICES_SUBDIR = "devices";
  private static final String METADATA_REPORT_JSON = "metadata_report.json";
  private static final String DEVICE_REGISTRY_ID_KEY = "deviceRegistryId";
  private FirestoreDataSink dataSink;
  private String schemaSpec;
  private final Map<String, ReportingDevice> expectedDevices = new HashMap<>();
  private final Set<String> extraDevices = new HashSet<>();
  private final Set<String> processedDevices = new HashSet<>();
  private final Set<String> base64Devices = new HashSet<>();
  private CloudIotConfig cloudIotConfig;
  public static final File METADATA_REPORT_FILE = new File(OUT_BASE_FILE, METADATA_REPORT_JSON);

  public static void main(String[] args) {
    Validator validator = new Validator();
    try {
      System.out.println(ServiceOptions.CREDENTIAL_ENV_NAME + "=" +
          System.getenv(ServiceOptions.CREDENTIAL_ENV_NAME));
      if (args.length < 3 || args.length > 4) {
        throw new IllegalArgumentException("Args: schema target inst_name [site]");
      }
      validator.setSchemaSpec(args[0]);
      String targetSpec = args[1];
      String instName = args[2];
      if (args.length >= 4) {
        validator.setSiteDir(args[3]);
      }
      if (targetSpec.startsWith(PUBSUB_PREFIX)) {
        String topicName = targetSpec.substring(PUBSUB_PREFIX.length());
        validator.validatePubSub(instName, topicName);
      } else {
        validator.validateFilesOutput(targetSpec);
      }
    } catch (ExceptionMap | ValidationException processingException) {
      System.exit(2);
    } catch (Exception e) {
      e.printStackTrace();
      System.err.flush();
      System.exit(-1);
    }
    System.exit(0);
  }

  private void setSiteDir(String siteDir) {
    File cloudConfig = new File(siteDir, "cloud_iot_config.json");
    try {
      cloudIotConfig = ConfigUtil.readCloudIotConfig(cloudConfig);
    } catch (Exception e) {
      throw new RuntimeException("While reading config file " + cloudConfig.getAbsolutePath(), e);
    }

    File devicesDir = new File(siteDir, DEVICES_SUBDIR);
    try {
      for (String device : Objects.requireNonNull(devicesDir.list())) {
        try {
          File deviceDir = new File(devicesDir, device);
          File metadataFile = new File(deviceDir, METADATA_JSON);
          ReportingDevice reportingDevice = new ReportingDevice(device);
          reportingDevice.setMetadata(
              OBJECT_MAPPER.readValue(metadataFile, ReportingDevice.Metadata.class));
          expectedDevices.put(device, reportingDevice);
        } catch (Exception e) {
          throw new RuntimeException("While loading device " + device, e);
        }
      }
      System.out.println("Loaded " + expectedDevices.size() + " expected devices");
    } catch (Exception e) {
      throw new RuntimeException(
          "While loading devices directory " + devicesDir.getAbsolutePath(), e);
    }
  }

  private void setSchemaSpec(String schemaSpec) {
    if (!schemaSpec.endsWith(File.separator)) {
      schemaSpec = schemaSpec + File.separator;
    }
    this.schemaSpec = schemaSpec;
  }

  private void validatePubSub(String instName, String topicName) {
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
    System.out.println("Results will be uploaded to " + dataSink.getViewUrl());
    OUT_BASE_FILE.mkdirs();
    System.out.println("Also found in such directories as " + OUT_BASE_FILE.getAbsolutePath());
    System.out.println("Generating report file in " + METADATA_REPORT_FILE.getAbsolutePath());
    System.out.println("Connecting to pubsub topic " + topicName);
    PubSubClient client = new PubSubClient(instName, topicName);
    System.out.println("Entering pubsub message loop on " + client.getSubscriptionId());
    while(client.isActive()) {
      try {
        client.processMessage(
            (message, attributes) -> validateMessage(schemaMap, message, attributes));
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

  private void validateMessage(Map<String, Schema> schemaMap, Map<String, Object> message,
      Map<String, String> attributes) {

    String registryId = attributes.get(DEVICE_REGISTRY_ID_KEY);
    if (cloudIotConfig != null && !cloudIotConfig.registry_id.equals(registryId)) {
      // Silently drop messages for different registries.
      return;
    }

    try {
      Exception error = null;
      String deviceId = attributes.get("deviceId");
      String subFolder = attributes.get("subFolder");
      String schemaId = subFolder;

      if (!expectedDevices.isEmpty()) {
        if (!processedDevices.add(deviceId)) {
          return;
        }
        System.out.println("Processing device #" + processedDevices.size() + ": " + deviceId);
      }

      if (attributes.get("wasBase64").equals("true")) {
        base64Devices.add(deviceId);
      }

      File deviceDir = new File(OUT_BASE_FILE, String.format(DEVICE_FILE_FORMAT, deviceId));
      deviceDir.mkdirs();

      File attributesFile = new File(deviceDir, String.format(ATTRIBUTE_FILE_FORMAT, schemaId));
      OBJECT_MAPPER.writeValue(attributesFile, attributes);

      File messageFile = new File(deviceDir, String.format(MESSAGE_FILE_FORMAT, schemaId));
      OBJECT_MAPPER.writeValue(messageFile, message);

      File errorFile = new File(deviceDir, String.format(ERROR_FILE_FORMAT, schemaId));

      try {
        Preconditions.checkNotNull(deviceId, "Missing deviceId in message");
        if (Strings.isNullOrEmpty(subFolder)
            || !schemaMap.containsKey(schemaId)) {
          throw new IllegalArgumentException(String.format(SCHEMA_SKIP_FORMAT, schemaId, deviceId));
        }
      } catch (Exception e) {
        System.out.println(e.getMessage());
        OBJECT_MAPPER.writeValue(errorFile, e.getMessage());
        error = e;
      }

      try {
        validateMessage(schemaMap.get(ENVELOPE_SCHEMA_ID), attributes);
        validateDeviceId(deviceId);
      } catch (ExceptionMap | ValidationException e) {
        processViolation(message, attributes, deviceId, ENVELOPE_SCHEMA_ID, attributesFile, errorFile, e);
        error = e;
      }

      try {
        validateMessage(schemaMap.get(schemaId), message);
        dataSink.validationResult(deviceId, schemaId, attributes, message, null);
      } catch (ExceptionMap | ValidationException e) {
        processViolation(message, attributes, deviceId, schemaId, messageFile, errorFile, e);
        error = e;
      }

      boolean updated = false;
      final ReportingDevice reportingDevice = expectedDevices.get(deviceId);
      try {
        if (expectedDevices.isEmpty()) {
          // No devices configured, so don't check metadata.
          updated = false;
        } else if (expectedDevices.containsKey(deviceId)) {
          ReportingDevice.PointsetMessage pointsetMessage =
              OBJECT_MAPPER.convertValue(message, ReportingDevice.PointsetMessage.class);
          updated = !reportingDevice.hasBeenValidated();
          reportingDevice.validateMetadata(pointsetMessage);
        } else {
          if (extraDevices.add(deviceId)) {
            updated = true;
          }
        }
      } catch (Exception e) {
        OBJECT_MAPPER.writeValue(errorFile, e.getMessage());
        error = e;
      }

      if (error == null) {
        System.out.println("Success validating device " + deviceId);
      } else if (expectedDevices.containsKey(deviceId)) {
        reportingDevice.setError(error);
        updated = true;
      }

      if (updated) {
        writeDeviceMetadataReport();
      }
    } catch (Exception e){
      e.printStackTrace();
    }
  }

  private void writeDeviceMetadataReport() {
    try {
      MetadataReport metadataReport = new MetadataReport();
      metadataReport.updated = new Date();
      metadataReport.missingDevices = new HashSet<>();
      metadataReport.extraDevices = extraDevices;
      metadataReport.successfulDevices = new HashSet<>();
      metadataReport.base64Devices = base64Devices;
      metadataReport.expectedDevices = expectedDevices.keySet();
      metadataReport.errorDevices = new HashMap<>();
      for (ReportingDevice deviceInfo : expectedDevices.values()) {
        String deviceId = deviceInfo.getDeviceId();
        if (deviceInfo.hasMetadataDiff()) {
          metadataReport.errorDevices.put(deviceId, deviceInfo.getMetadataDiff());
        } else if (deviceInfo.hasBeenValidated()) {
          metadataReport.successfulDevices.add(deviceId);
        } else {
          metadataReport.missingDevices.add(deviceId);
        }
      }
      OBJECT_MAPPER.writeValue(METADATA_REPORT_FILE, metadataReport);
    } catch (Exception e) {
      throw new RuntimeException("While generating metadata report file " + METADATA_REPORT_FILE.getAbsolutePath(), e);
    }
  }

  public static class MetadataReport {
    public Date updated;
    public Set<String> expectedDevices;
    public Set<String> missingDevices;
    public Set<String> extraDevices;
    public Set<String> successfulDevices;
    public Set<String> base64Devices;
    public Map<String, ReportingDevice.MetadataDiff> errorDevices;
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
      SchemaLoader loader = SchemaLoader.builder().schemaJson(rawSchema).httpClient(new RelativeClient()).build();
      return loader.load().build();
    } catch (Exception e) {
      throw new RuntimeException("While loading schema " + schemaFile.getAbsolutePath(), e);
    }
  }

  class RelativeClient implements SchemaClient {

    public static final String FILE_URL_PREFIX = "file:";

    @Override
    public InputStream get(String url) {
      try {
        if (!url.startsWith(FILE_URL_PREFIX)) {
          throw new IllegalStateException("Expected path to start with " + FILE_URL_PREFIX);
        }
        String new_url = FILE_URL_PREFIX + schemaSpec + url.substring(FILE_URL_PREFIX.length());
        return (InputStream) (new URL(new_url)).getContent();
      } catch (Exception e) {
        throw new RuntimeException("While loading URL " + url, e);
      }
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
