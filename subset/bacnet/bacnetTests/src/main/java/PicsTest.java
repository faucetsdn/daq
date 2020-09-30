import com.google.common.collect.Multimap;
import com.serotonin.bacnet4j.LocalDevice;
import com.serotonin.bacnet4j.RemoteDevice;
import com.serotonin.bacnet4j.npdu.ip.IpNetwork;
import com.serotonin.bacnet4j.service.unconfirmed.WhoIsRequest;
import helper.*;

import java.util.Map;

public class PicsTest {

  private Connection connection;
  private BacnetValidation validator;
  private BacnetPoints bacnetPoints = new BacnetPoints();
  private String testName = "protocol.bacext.pic";
  private String passedTestReport = String.format("RESULT pass %s The devices matches the PICS\n", testName);
  private String failedTestReport = String.format("RESULT fail %s ", testName);
  private String skippedTestReport = String.format("RESULT skip %s ", testName);
  private String testReport = "";
  private String reportAppendix = "";
  private String additionalReportAppendix = "";
  private Csv csv;
  private static LocalDevice localDevice;
  private String localIp = "";
  private String broadcastIp = "";
  boolean bacnetSupported = false;
  boolean csvFound = false;
  boolean verboseOutput = false;
  boolean errorEncountered = false;
  private String errorMessage = "";

  public PicsTest(String localIp, String broadcastIp, boolean verboseOutput) throws Exception {
    this.localIp = localIp;
    this.broadcastIp = broadcastIp;
    this.verboseOutput = verboseOutput;
    discoverDevices();
  }

  private void discoverDevices() throws Exception {
    connection = new Connection(broadcastIp, IpNetwork.DEFAULT_PORT, localIp);
    while (!connection.isTerminate()) {
      localDevice = connection.getLocalDevice();
      System.err.println("Sending whois...");
      localDevice.sendGlobalBroadcast(new WhoIsRequest());
      System.err.println("Waiting...");
      Thread.sleep(5000);
      System.err.println("Processing...");
      validator = new BacnetValidation(localDevice);
      this.bacnetSupported = validator.checkIfBacnetSupported();
      performPicsChecks();
      generateReport();
      connection.doTerminate();
    }
  }

  private void performPicsChecks() {
    try {

      // File manager moved out of devices loop
      // Currently Pics file is fixed per test
      FileManager fileManager = new FileManager();
      boolean csvExists = fileManager.checkDevicePicCSV();
      this.csvFound = csvExists;

      if(csvExists && this.bacnetSupported) {
        for (RemoteDevice remoteDevice : localDevice.getRemoteDevices()) {
          bacnetPoints.get(localDevice);
          Multimap<String, Map<String, String>> bacnetPointsMap = bacnetPoints.getBacnetPointsMap();
          validatePics(bacnetPointsMap, fileManager);
        }
      }

    } catch (Exception e) {
      e.printStackTrace();
      System.err.println("Error performing pics check: " + e.getMessage());
      
      this.errorEncountered = true;
      this.errorMessage = e.getMessage();
    }
  }

  private void validatePics(
          Multimap<String, Map<String, String>> bacnetPointsMap, FileManager fileManager) {
    String csvSheet = fileManager.getFilePath();
    System.out.println("csvSheet:" + csvSheet);
    csv = new Csv(csvSheet);
    csv.readAndValidate(bacnetPointsMap, this.verboseOutput);
  }

  private void generateReport() {
    Report report = new Report("tmp/BacnetPICSTestReport.txt");
    Report appendix = new Report("tmp/BacnetPICSTest_APPENDIX.txt");

    if (this.bacnetSupported && this.csvFound) {
      boolean testPassed = csv.getTestResult();
      String reportAppendix = csv.getTestAppendices();
      System.out.println("reportAppendix: " + reportAppendix);
      if (testPassed) {
        report.writeReport(passedTestReport);
      } else {
        failedTestReport += "The device does not match the PICS\n";
        report.writeReport(failedTestReport);
      }
      appendix.writeReport(additionalReportAppendix+reportAppendix);

    } else {  

      if (this.errorEncountered) {
        // Fail the test when there is an error
        testReport = failedTestReport;
        reportAppendix += String.format("Error encountered during test: %s \n", this.errorMessage);
      } else { 
        if (this.bacnetSupported && !this.csvFound){
          reportAppendix += "BACnet device found, but pics.csv not found in device type directory.\n";
          testReport = skippedTestReport;
        } else if (this.csvFound && !this.bacnetSupported) {
          // Test failed as expectation is there should be a BACnet device if the PICS was defined
          testReport = failedTestReport;
          reportAppendix += "PICS file defined however a BACnet device was not found.\n";
        } else if (!this.csvFound && !this.bacnetSupported) {
          reportAppendix += "BACnet device not found and pics.csv not found in device type directory.\n";
          testReport = skippedTestReport;
        }
      }
      testReport += reportAppendix;
      report.writeReport(testReport);
      appendix.writeReport(reportAppendix);
    }
  }
}
