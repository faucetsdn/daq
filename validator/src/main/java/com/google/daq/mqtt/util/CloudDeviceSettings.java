package com.google.daq.mqtt.util;

import com.google.api.services.cloudiot.v1.model.DeviceCredential;
import java.util.List;
import java.util.Map;

public class CloudDeviceSettings {
  public List<DeviceCredential> credentials;
  public Map<String, String> metadata;
}
