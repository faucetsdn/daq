package com.google.daq.mqtt.util;

import com.google.api.services.cloudiot.v1.model.DeviceCredential;
import com.google.daq.mqtt.registrar.LocalDevice;

import java.util.List;

public class CloudDeviceSettings {
  public DeviceCredential credential;
  public String metadata;
  public List<String> proxyDevices;
  public String config;
}
