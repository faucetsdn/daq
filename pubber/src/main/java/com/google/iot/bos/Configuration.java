package com.google.iot.bos;

/**
 */
public class Configuration {
  public String bridgeHostname = "mqtt.googleapis.com";
  public String bridgePort = "8883";
  public String projectId;
  public String cloudRegion;
  public String registryId;
  public String deviceId;
  public String gatewayId;
  public String keyFile;
  public byte[] keyBytes;
  public String algorithm;
  public String clientName = "proxyClient";
  public Integer proxyPort = 1883;
  public int logIntervalMs;
  public int publishSpacingMs;
}