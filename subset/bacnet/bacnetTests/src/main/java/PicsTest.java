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
  private String testName = "protocol.bacnet.pic";
  private String passedTestReport = String.format("RESULT pass %s\n", testName);
  private String failedTestReport = String.format("RESULT fail %s The device does not match the PICS\n", testName);
  private String skippedTestReport = String.format("RESULT skip %s Bacnet device not found.", testName);
  private String reportAppendix = "";
  private String additionalReportAppendix = "";
  private Csv csv;
  private static LocalDevice localDevice;
  private String localIp = "";
  private String broadcastIp = "";
  boolean bacnetSupported = false;
  boolean csvFound = true;
  boolean verboseOutput = false;

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
      bacnetSupported = validator.checkIfBacnetSupported();
      if (bacnetSupported) {
        performPicsChecks();
      } else {
        // Results in a 'skip' result
        reportAppendix += " Bacnet device not found... Pics check cannot be performed.\n";
        System.out.println(reportAppendix);
        generateReport();
      }
      connection.doTerminate();
    }
  }

  private void performPicsChecks() {
    try {
      for (RemoteDevice remoteDevice : localDevice.getRemoteDevices()) {
        FileManager fileManager = new FileManager();
        bacnetPoints.get(localDevice);
        Multimap<String, Map<String, String>> bacnetPointsMap = bacnetPoints.getBacnetPointsMap();
        boolean csvExists = fileManager.checkDevicePicCSV();
        if(!csvExists) {
          additionalReportAppendix = " pics.csv not found in device_types/../aux/ directory \n";
          skippedTestReport += additionalReportAppendix;
          this.csvFound = false;
          generateReport();
          return;
        }
        validatePics(bacnetPointsMap, fileManager);
        generateReport();
      }
    } catch (Exception e) {
        e.printStackTrace();
      System.err.println("Error performing pics check: " + e.getMessage());
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
      System.out.println("reportAppendix: "+reportAppendix);
      if (testPassed) {
        report.writeReport(passedTestReport);
      } else {
        report.writeReport(failedTestReport);
      }
      appendix.writeReport(additionalReportAppendix+reportAppendix);
    } else {
      report.writeReport(skippedTestReport);
      appendix.writeReport(reportAppendix);
    }
  }
}
