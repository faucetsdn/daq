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

    final TestSetup testSetup = new TestSetup(host, protocol, port, macAddress, domain);
    usernameList = testSetup.getUsernameList();
    passwordList = testSetup.getPasswordList();
    usernameListString = testSetup.getUsernameListString();
    passwordListString = testSetup.getPasswordListString();
  }

  private void runPasswordTest() {
    try {
      if (protocol.equals("ssh")) {
        SSHTestRunner sshTestRunner = new SSHTestRunner(usernameList, passwordList, host, protocol, port, macAddress);
        sshTestRunner.StartTest();
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
            ReportHandler.writeReportMessage("fail", protocol, port, macAddress);
          } else {
            ReportHandler.writeReportMessage("pass", protocol, port, macAddress);
          }
        }
        else {
          ReportHandler.writeReportMessage("skip_noport", protocol, port, macAddress);
        }
      }
    }
    catch (Exception e) {
      System.err.println(e.getMessage());
      // TODO: Move this elsewhere...
      ReportHandler.writeReportMessage("skip_mac", protocol, port, macAddress);
    }
  }

  public static void main(final String[] args) {
    final PasswordTest passwordTest = new PasswordTest(args);
    passwordTest.runPasswordTest();
  }

}
