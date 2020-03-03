/** Main entry point for test. */

import java.util.ArrayList;

public class PasswordTest {

  private static int REQUIRED_PARAMETERS = 5;
  private static String HELP_STRING = "Usage: target_ip protocol(http(s)/ssh/telnet) target_port target_mac domain";

  private String host;
  private String protocol;
  private String port;
  private String macAddress;
  private String domain;

  private ReportHandler reportHandler;
  private ArrayList<String> usernameList;
  private ArrayList<String> passwordList;
  private String usernameListString;
  private String passwordListString;

  public PasswordTest(final String[] args) {
    if (args.length != REQUIRED_PARAMETERS) {
      throw new IllegalArgumentException(HELP_STRING);
    } else {
      host = args[0];
      protocol = args[1];
      port = args[2];
      macAddress = args[3];
      domain = args[4];
    }

    reportHandler = new ReportHandler(protocol);

    final TestSetup testSetup = new TestSetup(host, protocol, port, macAddress, domain);
    usernameList = testSetup.getUsernameList();
    passwordList = testSetup.getPasswordList();
    usernameListString = testSetup.getUsernameListString();
    passwordListString = testSetup.getPasswordListString();
  }

  private void runPasswordTest() {
    try {
      if (protocol.equals("ssh")) {
        SSHTestRunner sshTestRunner = new SSHTestRunner(usernameList, passwordList, host, port, reportHandler);
        Thread sshThread = new Thread(sshTestRunner);
        sshThread.start();
      }
      else {
        final boolean areAllPortsOpen = NmapPortChecker.checkAllPortsOpen(host);

        if (areAllPortsOpen) {
          final boolean isDiscoveredCredentials = NcrackChecker.isDiscoveredCredentials(
              domain,
              protocol,
              host,
              port,
              usernameListString,
              passwordListString
          );

          if (isDiscoveredCredentials) {
            reportHandler.addText("RESULT fail security.passwords." + protocol
                + " Default passwords have not been changed");
            reportHandler.writeReport();
          } else {
            reportHandler.addText("RESULT pass security.passwords." + protocol
                + "  Default passwords have been changed");
            reportHandler.writeReport();
          }
        }
        else {
          reportHandler.addText("RESULT skip security.passwords." + protocol
              + " Ports are not open!");
          reportHandler.writeReport();
        }
      }
    }
    catch (Exception e) {
      System.err.println(e.getMessage());
      reportHandler.addText(
          "RESULT skip security.passwords."+ protocol +" Could not lookup password info for mac-key " + macAddress);
      reportHandler.writeReport();
    }
  }

  public static void main(final String[] args) {
    final PasswordTest passwordTest = new PasswordTest(args);
    passwordTest.runPasswordTest();
  }

}
