package helper;

import com.serotonin.bacnet4j.LocalDevice;
import com.serotonin.bacnet4j.RemoteDevice;

import java.util.List;

public class BacnetValidation {
  LocalDevice localDevice = null;

  public BacnetValidation(LocalDevice localDevice) {
    this.localDevice = localDevice;
  }

  public boolean checkIfBacnetSupported() {
    List<RemoteDevice> remoteDevices = localDevice.getRemoteDevices();
    if (remoteDevices.size() > 0) {
      return true;
    }
    return false;
  }
}
