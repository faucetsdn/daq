package com.google.daq.mqtt.registrar;

import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.core.JsonParser.Feature;
import com.fasterxml.jackson.core.PrettyPrinter;
import com.fasterxml.jackson.core.util.DefaultPrettyPrinter;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.util.ISO8601DateFormat;
import com.google.api.services.cloudiot.v1.model.DeviceCredential;
import com.google.common.base.Preconditions;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Sets;
import com.google.common.collect.Sets.SetView;
import com.google.daq.mqtt.util.CloudDeviceSettings;
import com.google.daq.mqtt.util.CloudIotManager;

import java.io.*;
import java.nio.charset.Charset;
import java.util.Date;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

import com.google.daq.mqtt.util.ExceptionMap;
import org.apache.commons.io.IOUtils;
import org.everit.json.schema.Schema;
import org.json.JSONObject;
import org.json.JSONTokener;

import static com.google.daq.mqtt.registrar.Registrar.*;

public class LocalDevice {

  private static final PrettyPrinter PROPER_PRETTY_PRINTER_POLICY = new ProperPrettyPrinterPolicy();

  private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper()
      .enable(SerializationFeature.INDENT_OUTPUT)
      .enable(SerializationFeature.ORDER_MAP_ENTRIES_BY_KEYS)
      .enable(Feature.ALLOW_TRAILING_COMMA)
      .enable(Feature.STRICT_DUPLICATE_DETECTION)
      .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
      .setDateFormat(new ISO8601DateFormat())
      .setSerializationInclusion(Include.NON_NULL);

  private static final String RSA_CERT_TYPE = "RSA_X509_PEM";
  private static final String RSA_PUBLIC_PEM = "rsa_public.pem";
  private static final String RSA_CERT_PEM = "rsa_cert.pem";
  private static final String RSA_PRIVATE_PEM = "rsa_private.pem";
  private static final String RSA_PRIVATE_PKCS8 = "rsa_private.pkcs8";
  private static final String PHYSICAL_TAG_FORMAT = "%s_%s";
  private static final String PHYSICAL_TAG_ERROR = "Physical asset name %s does not match expected %s";

  private static final Set<String> baseFiles = ImmutableSet.of(METADATA_JSON, RSA_PRIVATE_PEM,
      RSA_PRIVATE_PKCS8, PROPERTIES_JSON);
  private static final Set<?> OPTIONAL_FILES = ImmutableSet.of(DEVICE_ERRORS_JSON);
  private static final String KEYGEN_EXEC_FORMAT = "validator/bin/keygen %s %s";
  public static final String METADATA_SUBFOLDER = "metadata";
  private static final String ERROR_FORMAT_INDENT = "  ";

  private final String deviceId;
  private final Map<String, Schema> schemas;
  private final File deviceDir;
  private final Metadata metadata;
  private final Properties properties;
  private final ExceptionMap exceptionMap;

  private String deviceNumId;

  private CloudDeviceSettings settings;

  LocalDevice(File devicesDir, String deviceId, Map<String, Schema> schemas) {
    try {
      this.deviceId = deviceId;
      this.schemas = schemas;
      exceptionMap = new ExceptionMap("Exceptions for " + deviceId);
      deviceDir = new File(devicesDir, deviceId);
      metadata = readMetadata();
      properties = readProperties();
    } catch (Exception e) {
      throw new RuntimeException("While loading local device " + deviceId, e);
    }
  }

  static boolean deviceExists(File devicesDir, String deviceName) {
    return new File(new File(devicesDir, deviceName), METADATA_JSON).isFile();
  }

  public void validatedDeviceDir() {
    try {
      String[] files = deviceDir.list();
      Preconditions.checkNotNull(files, "No files found in " + deviceDir.getAbsolutePath());
      Set<String> expectedFiles = Sets.union(baseFiles, Set.of(publicKeyFile()));
      Set<String> actualFiles = ImmutableSet.copyOf(files);
      SetView<String> missing = Sets.difference(expectedFiles, actualFiles);
      if (!missing.isEmpty()) {
        throw new RuntimeException("Missing files: " + missing);
      }
      SetView<String> extra = Sets.difference(Sets.difference(actualFiles, expectedFiles), OPTIONAL_FILES);
      if (!extra.isEmpty()) {
        throw new RuntimeException("Extra files: " + extra);
      }
    } catch (Exception e) {
      throw new RuntimeException("While validating device directory " + deviceId, e);
    }
  }

  private Properties readProperties() {
    File propertiesFile = new File(deviceDir, PROPERTIES_JSON);
    try (InputStream targetStream = new FileInputStream(propertiesFile)) {
      schemas.get(PROPERTIES_JSON).validate(new JSONObject(new JSONTokener(targetStream)));
    } catch (Exception e) {
      throw new RuntimeException("Processing input " + propertiesFile, e);
    }
    try {
      return OBJECT_MAPPER.readValue(propertiesFile, Properties.class);
    } catch (Exception e) {
      throw new RuntimeException("While reading "+ propertiesFile.getAbsolutePath(), e);
    }
  }

  private Metadata readMetadata() {
    File metadataFile = new File(deviceDir, METADATA_JSON);
    try (InputStream targetStream = new FileInputStream(metadataFile)) {
      schemas.get(METADATA_JSON).validate(new JSONObject(new JSONTokener(targetStream)));
    } catch (Exception metadata_exception) {
      exceptionMap.put("Validating", metadata_exception);
    }
    try {
      return OBJECT_MAPPER.readValue(metadataFile, Metadata.class);
    } catch (Exception mapping_exception) {
      exceptionMap.put("Reading", mapping_exception);
    }
    return null;
  }

  private String metadataHash() {
    try {
      String savedHash = metadata.hash;
      metadata.hash = null;
      String json = metadataString();
      metadata.hash = savedHash;
      return String.format("%08x", Objects.hash(json));
    } catch (Exception e) {
      throw new RuntimeException("Converting object to string", e);
    }
  }

  private DeviceCredential loadCredential() {
    try {
      File deviceKeyFile = new File(deviceDir, publicKeyFile());
      if (!deviceKeyFile.exists()) {
        generateNewKey();
      }
      return CloudIotManager.makeCredentials(properties.key_type,
          IOUtils.toString(new FileInputStream(deviceKeyFile), Charset.defaultCharset()));
    } catch (Exception e) {
      throw new RuntimeException("While loading credential for local device " + deviceId, e);
    }
  }

  private String publicKeyFile() {
    return properties.key_type.equals(RSA_CERT_TYPE) ? RSA_CERT_PEM : RSA_PUBLIC_PEM;
  }

  private void generateNewKey() {
    String absolutePath = deviceDir.getAbsolutePath();
    try {
      String command = String.format(KEYGEN_EXEC_FORMAT, properties.key_type, absolutePath);
      System.err.println(command);
      int exitCode = Runtime.getRuntime().exec(command).waitFor();
      if (exitCode != 0) {
        throw new RuntimeException("Keygen exit code " + exitCode);
      }
    } catch (Exception e) {
      throw new RuntimeException("While generating new credential for " + deviceId, e);
    }
  }

  CloudDeviceSettings getSettings() {
    try {
      if (settings != null) {
        return settings;
      }

      settings = new CloudDeviceSettings();
      settings.credential = loadCredential();
      settings.metadata = metadataString();
      return settings;
    } catch (Exception e) {
      throw new RuntimeException("While getting settings for device " + deviceId, e);
    }
  }

  private String metadataString() {
    try {
      return OBJECT_MAPPER.writeValueAsString(metadata);
    } catch (Exception e) {
      throw new RuntimeException("While converting metadata to string", e);
    }
  }

  public void validateEnvelope(String registryId, String siteName) {
    try {
      Envelope envelope = new Envelope();
      envelope.deviceId = deviceId;
      envelope.deviceRegistryId = registryId;
      // Don't use actual project id because it should be abstracted away.
      envelope.projectId = fakeProjectId();
      envelope.deviceNumId = makeNumId(envelope);
      String envelopeJson = OBJECT_MAPPER.writeValueAsString(envelope);
      schemas.get(ENVELOPE_JSON).validate(new JSONObject(new JSONTokener(envelopeJson)));
    } catch (Exception e) {
      throw new IllegalStateException("Validating envelope " + deviceId, e);
    }
    checkConsistency(siteName);
  }

  private String fakeProjectId() {
    return metadata.system.location.site_name.toLowerCase();
  }

  private void checkConsistency(String expected_site_name) {
    String siteName = metadata.system.location.site_name;
    String desiredTag = String.format(PHYSICAL_TAG_FORMAT, siteName, deviceId);
    String assetName = metadata.system.physical_tag.asset.name;
    Preconditions.checkState(desiredTag.equals(assetName),
        String.format(PHYSICAL_TAG_ERROR, assetName, desiredTag));
    String errorMessage = "Site name " + siteName + " is not expected " + expected_site_name;
    Preconditions.checkState(expected_site_name.equals(siteName), errorMessage);
  }

  private String makeNumId(Envelope envelope) {
    int hash = Objects.hash(deviceId, envelope.deviceRegistryId, envelope.projectId);
    return Integer.toString(hash < 0 ? -hash : hash);
  }

  public void writeErrors() {
    File errorsFile = new File(deviceDir, DEVICE_ERRORS_JSON);
    System.err.println("Updating " + errorsFile);
    if (exceptionMap.isEmpty()) {
      errorsFile.delete();
      return;
    }
    try (PrintStream printStream = new PrintStream(new FileOutputStream(errorsFile))) {
      ExceptionMap.ErrorTree errorTree = ExceptionMap.format(exceptionMap, ERROR_FORMAT_INDENT);
      errorTree.write(printStream);
    } catch (Exception e) {
      throw new RuntimeException("While writing "+ errorsFile.getAbsolutePath(), e);
    }
  }

  void writeNormalized() {
    File metadataFile = new File(deviceDir, METADATA_JSON);
    try (OutputStream outputStream = new FileOutputStream(metadataFile)) {
      String writeHash = metadataHash();
      boolean update = metadata.hash == null || !metadata.hash.equals(writeHash);
      if (update) {
        metadata.timestamp = new Date();
        metadata.hash = metadataHash();
      }
      // Super annoying, but can't set this on the global static instance.
      JsonGenerator generator = OBJECT_MAPPER.getFactory()
          .createGenerator(outputStream)
          .setPrettyPrinter(PROPER_PRETTY_PRINTER_POLICY);
      OBJECT_MAPPER.writeValue(generator, metadata);
    } catch (Exception e) {
      exceptionMap.put("Writing", e);
    }
  }

  public String getDeviceId() {
    return deviceId;
  }

  public String getDeviceNumId() {
    return Preconditions.checkNotNull(deviceNumId, "deviceNumId not set");
  }

  public void setDeviceNumId(String numId) {
    deviceNumId = numId;
  }

  public ExceptionMap getErrors() {
    return exceptionMap;
  }

  public File getDeviceDir() {
    return deviceDir;
  }

  private static class Envelope {
    public String deviceId;
    public String deviceNumId;
    public String deviceRegistryId;
    public String projectId;
    public final String subFolder = METADATA_SUBFOLDER;
  }

  private static class Metadata {
    public PointsetMetadata pointset;
    public SystemMetadata system;
    public Integer version;
    public Date timestamp;
    public String hash;
  }

  private static class Properties {
    public String key_type;
    public String connect;
    public Integer version;
  }

  private static class PointsetMetadata {
    public Map<String, PointMetadata> points;
  }

  private static class SystemMetadata {
    public LocationMetadata location;
    public PhysicalTagMetadata physical_tag;
  }

  private static class PointMetadata {
    public String units;
  }

  private static class LocationMetadata {
    public String site_name;
    public String section;
    public Object position;
  }

  private static class PhysicalTagMetadata {
    public AssetMetadata asset;
  }

  private static class AssetMetadata {
    public String guid;
    public String name;
  }

  private static class ProperPrettyPrinterPolicy extends DefaultPrettyPrinter {
    @Override
    public void writeObjectFieldValueSeparator(JsonGenerator jg) throws IOException {
      jg.writeRaw(": ");
    }
  }
}
