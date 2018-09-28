package com.google.daq.orchestrator.mudacl;

import com.google.daq.orchestrator.mudacl.DeviceTopology.MacIdentifier;
import com.google.daq.orchestrator.mudacl.DeviceTypes.DeviceClassifier;
import com.google.daq.orchestrator.mudacl.SwitchTopology.Ace;
import com.google.daq.orchestrator.mudacl.SwitchTopology.Acl;
import java.util.Collection;
import java.util.List;

public interface AclProvider {
  Acl makeEdgeAcl(DeviceClassifier device, MacIdentifier macAddress);

  Acl makeUpstreamAcl(DeviceClassifier device, MacIdentifier macAddress);

  List<String> targetTypes();

  void setDeviceTypes(DeviceTypes deviceTypes);
}
