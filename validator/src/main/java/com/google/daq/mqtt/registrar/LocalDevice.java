package com.google.daq.mqtt.registrar;

import static com.google.daq.mqtt.registrar.Registrar.ENVELOPE_JSON;
import static com.google.daq.mqtt.registrar.Registrar.METADATA_JSON;
import static com.google.daq.mqtt.registrar.Registrar.PROPERTIES_JSON;

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
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.Charset;
import java.util.Date;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.apache.commons.io.IOUtils;
import org.everit.json.schema.Schema;
import org.json.JSONObject;
import org.json.JSONTokener;

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

  private static final String RSA_PUBLIC_PEM = "rsa_public.pem";
  private static final String RSA_PRIVATE_PEM = "rsa_private.pem";
  private static final String RSA_PRIVATE_PKCS8 = "rsa_private.pkcs8";
  private static final String PHYSICAL_TAG_FORMAT = "%s_%s";
  private static final String PHYSICAL_TAG_ERROR = "Physical asset name %s does not match expected %s";

  private static final Set<String> allowedFiles = ImmutableSet.of(METADATA_JSON, RSA_PUBLIC_PEM, RSA_PRIVATE_PEM,
      RSA_PRIVATE_PKCS8, PROPERTIES_JSON);
  private static final String KEYGEN_EXEC_FORMAT = "validator/bin/keygen %s %s";
  public static final String METADATA_SUBFOLDER = "metadata";

  private final String deviceId;
  private final Map<String, Schema> schemas;
  private final File deviceDir;
  private final Metadata metadata;
  private final Properties properties;

  private String deviceNumId;

  private CloudDeviceSettings settings;

  LocalDevice(File devicesDir, String deviceId, Map<String, Schema> schemas) {
    try {
      this.deviceId = deviceId;
      this.schemas = schemas;
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
      ImmutableSet<String> actualFiles = ImmutableSet.copyOf(files);
      SetView<String> missing = Sets.difference(allowedFiles, actualFiles);
      if (!missing.isEmpty()) {
        throw new RuntimeException("Missing files: " + missing);
      }
      SetView<String> extra = Sets.difference(actualFiles, allowedFiles);
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
    } catch (Exception e1) {
      throw new RuntimeException("Processing input " + metadataFile, e1);
    }
    try {
      return OBJECT_MAPPER.readValue(metadataFile, Metadata.class);
    } catch (Exception e) {
      throw new RuntimeException("While reading "+ metadataFile.getAbsolutePath(), e);
    }
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
      File deviceKeyFile = new File(deviceDir, RSA_PUBLIC_PEM);
      if (!deviceKeyFile.exists()) {
        generateNewKey();
      }
      return CloudIotManager.makeCredentials(properties.key_type,
          IOUtils.toString(new FileInputStream(deviceKeyFile), Charset.defaultCharset()));
    } catch (Exception e) {
      throw new RuntimeException("While loading credential for local device " + deviceId, e);
    }
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

  public void validate(String registryId, String siteName) {
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
      throw new RuntimeException("While writing "+ metadataFile.getAbsolutePath(), e);
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
