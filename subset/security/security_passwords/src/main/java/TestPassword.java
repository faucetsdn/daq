/** Main entry point for test. */

import java.io.IOException;

public class TestPassword {

  private static int REQUIRED_PARAMETERS = 5;
  private static String HELP_STRING = "Usage: target_ip protocol(http(s)/ssh/telnet) target_port target_mac domain";

  private String host;
  private String protocol;
  private String port;
  private String macAddress;
  private String domain;

  public TestPassword(final String[] args) {
    if (args.length != REQUIRED_PARAMETERS) {
      throw new IllegalArgumentException(HELP_STRING);
    }
    else {
      host = args[0];
      protocol = args[1];
      port = args[2];
      macAddress = args[3];
      domain = args[4];
    }
  }

  public void runPasswordTest() {
    try {
      final String usernamesFile = DefaultCredentials.getFormattedUsernameFileWithProtocol(protocol);
      final String passwordsFile = DefaultCredentials.getFormattedPasswordFileWithProtocol(protocol);

      final boolean desiredPortOpen = PortChecker.checkDesiredPortOpen(host, port, protocol);
      final boolean macAddressIsInCredentialsFile = DefaultCredentials.defaultCredentialsFileHasMacAddress(macAddress);

      if (macAddressIsInCredentialsFile && desiredPortOpen) {
        DefaultCredentials.writeUsernamesToFile(macAddress, protocol);
        DefaultCredentials.writePasswordsToFile(macAddress, protocol);

        final String result = BruteForceTester.startTest(domain, protocol, host, port, usernamesFile, passwordsFile);
        ReportHandler.writeReportMessage(result, protocol, port, macAddress);
      }
      else if (!macAddressIsInCredentialsFile && !desiredPortOpen) {
        ReportHandler.writeReportMessage(ReportHandler.RESULT_SKIP_NOMAC_NOPORT, protocol, port, macAddress);
      }
      else if (!macAddressIsInCredentialsFile) {
        ReportHandler.writeReportMessage(ReportHandler.RESULT_SKIP_NOMAC, protocol, port, macAddress);
      }
      else {
        ReportHandler.writeReportMessage(ReportHandler.RESULT_SKIP_NOPORT, protocol, port, macAddress);
      }
    }
    catch (final IOException e) {
      e.printStackTrace();
    }
  }

  public static void main(final String[] args) {
    final TestPassword testPassword = new TestPassword(args);
    testPassword.runPasswordTest();
  }

}
