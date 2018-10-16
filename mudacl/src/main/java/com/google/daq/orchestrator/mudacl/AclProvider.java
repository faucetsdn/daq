package com.google.daq.orchestrator.mudacl;

import com.google.daq.orchestrator.mudacl.DeviceMaps.DeviceSpec;
import com.google.daq.orchestrator.mudacl.DeviceTopology.MacIdentifier;
import com.google.daq.orchestrator.mudacl.SwitchTopology.Acl;
import java.util.List;

public interface AclProvider {
  Acl makeEdgeAcl(DeviceSpec device, MacIdentifier macAddress);

  Acl makeUpstreamAcl(DeviceSpec device, MacIdentifier macAddress);

  List<String> targetTypes();

  void setDeviceMaps(DeviceMaps deviceMaps);
}
