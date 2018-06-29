package com.google.daq.orchestrator.mudacl;

import com.google.daq.orchestrator.mudacl.DeviceTopology.MacIdentifier;
import com.google.daq.orchestrator.mudacl.DeviceTypes.DeviceClassifier;
import com.google.daq.orchestrator.mudacl.SwitchTopology.Acl;

public interface AclProvider {
  Acl makeEdgeAcl(MacIdentifier macAddress, DeviceClassifier device);
}
