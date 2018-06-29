package com.google.bos.orchestrator.mudacl;

import com.google.bos.orchestrator.mudacl.DeviceTopology.MacIdentifier;
import com.google.bos.orchestrator.mudacl.DeviceTypes.DeviceClassifier;
import com.google.bos.orchestrator.mudacl.SwitchTopology.Acl;

public interface AclProvider {
  Acl makeEdgeAcl(MacIdentifier macAddress, DeviceClassifier device);
}
