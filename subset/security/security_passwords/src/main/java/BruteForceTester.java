/** Creates and runs commands to run brute force tools, Ncrack/Hydra.
 * Ncrack is used for HTTP, HTTPS
 * Hydra is used for SSH (Ncrack currently runs into issues with SSH), and telnet (Is faster on Hydra).*/

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class BruteForceTester {

  private static String NCRACK_COMMAND_STRING = "ncrack %s %s://%s:%s -U %s -P %s";
  private static String HYDRA_COMMAND_STRING = "hydra -L %s -P %s %s %s -s %s";

  private static String getCommandToRun(
      final String domain,
      final String protocol,
      final String host,
      final String port,
      final String usernamesFile,
      final String passwordsFile
  ) {
    if (protocol.equals("ssh") || protocol.equals("telnet")) {
      return String.format(HYDRA_COMMAND_STRING, usernamesFile, passwordsFile, host, protocol, port);
    }
    else {
      return String.format(NCRACK_COMMAND_STRING, domain, protocol, host, port, usernamesFile, passwordsFile);
    }
  }

  private static BufferedReader runCommandAndGetOutputReader(final String commandToRun) throws IOException {
    final Process process = Runtime.getRuntime().exec(commandToRun);
    return new BufferedReader(new InputStreamReader(process.getInputStream()));
  }

  private static boolean lineIndicatesCredentialsFound(final String protocol, final String line) {
    if (protocol.equals("ssh") || protocol.equals("telnet")) {
      return line.contains("successfully completed");
    }
    else {
      return line.contains("Discovered credentials");
    }
  }

  public static String startTest(
      final String domain,
      final String protocol,
      final String host,
      final String port,
      final String usernamesFile,
      final String passwordsFile
  ) throws IOException {
    final String commandToRun = getCommandToRun(domain, protocol, host, port, usernamesFile, passwordsFile);
    final BufferedReader outputReader = runCommandAndGetOutputReader(commandToRun);

    System.out.println(commandToRun);
    String result = ReportHandler.RESULT_PASS;
    String currentLine;

    while ((currentLine = outputReader.readLine()) != null) {
      System.out.println(currentLine);
      if (lineIndicatesCredentialsFound(protocol, currentLine)) {
        result = ReportHandler.RESULT_FAIL;
      }
    }

    return result;
  }

}
