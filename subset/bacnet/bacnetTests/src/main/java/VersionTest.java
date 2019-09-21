import java.util.Map;
import com.serotonin.bacnet4j.LocalDevice;
import com.serotonin.bacnet4j.RemoteDevice;
import com.serotonin.bacnet4j.exception.BACnetException;
import com.serotonin.bacnet4j.npdu.ip.IpNetwork;
import com.serotonin.bacnet4j.service.unconfirmed.WhoIsRequest;
import com.serotonin.bacnet4j.type.Encodable;
import com.serotonin.bacnet4j.type.enumerated.PropertyIdentifier;
import com.serotonin.bacnet4j.util.RequestUtils;
import helper.BacnetValidation;
import helper.Connection;
import helper.Report;

public class VersionTest {

  private Connection connection;
  private BacnetValidation validator;
  private static LocalDevice localDevice;
  private String localIp = "";
  private String broadcastIp = "";
  private String appendixText = "";
  private boolean testPassed = false;
  boolean bacnetSupported = false;
  private String testName = "protocol.bacnet.version";
  private String infoReportText = String.format("RESULT info %s", testName);
  private String skippedReportText = String.format("RESULT skip %s", testName);
  private String errorPropertyMessage = "errorClass=Property, errorCode=Unknown property";
  private String protocolVersionText = "";

  public VersionTest(String localIp, String broadcastIp) throws Exception {
    this.localIp = localIp;
    this.broadcastIp = broadcastIp;
    discoverDevices();
  }

  public void discoverDevices() throws Exception {
    connection = new Connection(broadcastIp, IpNetwork.DEFAULT_PORT, localIp);
    while (!connection.isTerminate()) {
      localDevice = connection.getLocalDevice();
      System.err.println("Sending whois...");
      localDevice.sendGlobalBroadcast(new WhoIsRequest());
      System.err.println("Waiting...");
      Thread.sleep(5000);
      System.err.println("Processing...");
      validator = new BacnetValidation(localDevice);
      bacnetSupported = validator.checkIfBacnetSupported();
      if (bacnetSupported) {
        checkDevicesVersionAndGenerateReport();
      } else {
        appendixText += " Bacnet device not found.\n";
        System.out.println(appendixText);
        generateReport("");
      }
      connection.doTerminate();
    }
  }

  private void checkDevicesVersionAndGenerateReport() {
    for (RemoteDevice remoteDevice : localDevice.getRemoteDevices()) {
      Map<PropertyIdentifier, Encodable> values =
          getDeviceVersionProperties(localDevice, remoteDevice);
      checkDeviceVersion(values);
      String formattedDeviceMacAddress =
          remoteDevice.getAddress().getMacAddress().toString().replaceAll("\\[|\\]", "");
      generateReport(formattedDeviceMacAddress);
    }
    System.out.println(appendixText);
  }

  private Map<PropertyIdentifier, Encodable> getDeviceVersionProperties(
      LocalDevice localDevice, RemoteDevice remoteDevice) {
    Map<PropertyIdentifier, Encodable> values = null;
    try {
      values =
          RequestUtils.getProperties(
              localDevice,
              remoteDevice,
              null,
              PropertyIdentifier.vendorIdentifier,
              PropertyIdentifier.vendorName,
              PropertyIdentifier.objectList,
              PropertyIdentifier.objectName,
              PropertyIdentifier.modelName,
              PropertyIdentifier.firmwareRevision,
              PropertyIdentifier.applicationSoftwareVersion,
              PropertyIdentifier.description,
              PropertyIdentifier.location,
              PropertyIdentifier.protocolVersion);
    } catch (BACnetException e) {
      System.out.println(e.getMessage());
      connection.doTerminate();
    }
    return values;
  }

  private void checkDeviceVersion(Map<PropertyIdentifier, Encodable> values) {
    appendixText += ("\n");
    for (Map.Entry<PropertyIdentifier, Encodable> property : values.entrySet()) {
      String key = property.getKey().toString();
      String value = property.getValue().toString();
      // Format the Object List property to be more legible
      if (key.equals("Object list")) {
        formatProperty(property);
          testPassed = true;
      } else {
          // This error is returned if device does not have the property
          if (value.equals(errorPropertyMessage)) { value = ""; };
          appendixText += key + " : " + value + "\n";
          if (!value.isEmpty()) {
              testPassed = true;
          }
          if (key.equals("Protocol version")) protocolVersionText = " Protocol version: " + value + "\n";
      }
    }
    appendixText += ("\n\n\n");
  }

  private void formatProperty(Map.Entry<PropertyIdentifier, Encodable> property) {
    String key = property.getKey().toString();
    String[] value = property.getValue().toString().split(",");
    appendixText += key + " : ";
    for (int i = 0; i < value.length; i++) {
      if (i == 0) {
        appendixText += value[i];
      } else {
        appendixText += String.format("%-14s%-20s", "", value[i]);
      }
      if (i % 2 == 0) {
        appendixText += "\n";
      }
    }
    appendixText += "\n";
  }

  private void generateReport(String deviceMacAddress) {
    Report report = new Report("tmp/" + deviceMacAddress + "_BacnetVersionTestReport.txt");
    Report appendices = new Report("tmp/" + deviceMacAddress + "_BacnetVersionTest_APPENDIX.txt");
    if (bacnetSupported && testPassed) {
        report.writeReport(infoReportText + protocolVersionText);
    } else {
      report.writeReport(skippedReportText);
    }
    appendices.writeReport(appendixText);
  }
}
