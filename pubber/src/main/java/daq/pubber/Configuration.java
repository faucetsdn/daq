package daq.pubber;

/**
 */
public class Configuration {
  public String bridgeHostname = "mqtt.googleapis.com";
  public String bridgePort = "443";
  public String projectId;
  public String cloudRegion;
  public String registryId;
  public String gatewayId;
  public String keyFile = "local/pubber_private.pkcs8";
  public byte[] keyBytes;
  public String algorithm = "RS256";
}