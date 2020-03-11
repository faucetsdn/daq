/* Main entry point for test. */

import java.io.IOException;

public class TestPassword {

  private static final int REQUIRED_PARAMETERS = 5;
  private static final String NMAP_MESSAGE = "Starting NMAP check...";
  private static final String BRUTE_FORCE_MESSAGE = "Starting brute force...";
  private static final String FINISH_MESSAGE = "Done.";

  private static final String HELP_STRING =
      "Usage: target_ip protocol(http(s)/ssh/telnet) target_port target_mac domain";
  private static final String STARTUP_MESSAGE =
      "[STARTING WITH IP:%s, MAC:%s, PROTOCOL: %s]";

  private String host;
  private String protocol;
  private String port;
  private String mac;
  private String domain;

  public TestPassword(final String[] args) {
    if (args.length != REQUIRED_PARAMETERS) {
      throw new IllegalArgumentException(HELP_STRING);
    }
    else {
      host = args[0];
      protocol = args[1];
      port = args[2];
      mac = args[3];
      domain = args[4];
    }
  }

  public void runPasswordTest() {
    try {
      ReportHandler.printMessage(String.format(STARTUP_MESSAGE, host, mac, protocol));
      ReportHandler.printMessage(NMAP_MESSAGE);
      final boolean desiredPortOpen = PortChecker.checkDesiredPortOpen(host, port, protocol);
      final boolean macIsInCredentialsFile = DefaultCredentials.credentialsFileHasMacAddress(mac);

      if (macIsInCredentialsFile && desiredPortOpen) {
        DefaultCredentials.writeUsernamesToFile(mac, protocol);
        DefaultCredentials.writePasswordsToFile(mac, protocol);

        final String users = DefaultCredentials.getUsernameFilePath(protocol);
        final String passwords = DefaultCredentials.getPasswordFilePath(protocol);

        ReportHandler.printMessage(BRUTE_FORCE_MESSAGE);
        final String result = BruteForceTester.start(domain, protocol, host, port, users, passwords);
        ReportHandler.writeReportMessage(result, protocol, port, mac);
      }
      else if (!macIsInCredentialsFile && !desiredPortOpen) {
        ReportHandler.writeReportMessage(ReportHandler.SKIP_NOMAC_NOPORT, protocol, port, mac);
      }
      else if (!macIsInCredentialsFile) {
        ReportHandler.writeReportMessage(ReportHandler.SKIP_NOMAC, protocol, port, mac);
      }
      else {
        ReportHandler.writeReportMessage(ReportHandler.SKIP_NOPORT, protocol, port, mac);
      }

      ReportHandler.printMessage(FINISH_MESSAGE);
    }
    catch (final IOException e) {
      ReportHandler.printMessage(e.getMessage());
    }
  }

  public static void main(final String[] args) {
    final TestPassword testPassword = new TestPassword(args);
    testPassword.runPasswordTest();
  }

}
