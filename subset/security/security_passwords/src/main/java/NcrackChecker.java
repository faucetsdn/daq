/** Builds, runs and parses the result of an ncrack command to check if the credentials were
 * discovered. */

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class NcrackChecker {

  private static String NCRACK_COMMAND_STRING = "ncrack %s %s://%s:%s --user %s --pass %s";

  private static String getCommandToRun(
      final String domain,
      final String protocol,
      final String host,
      final String port,
      final String usernames,
      final String passwords
  ) {
    return String.format(NCRACK_COMMAND_STRING, domain, protocol, host, port, usernames, passwords);
  }

  private static BufferedReader runCommandAndGetOutputReader(final String commandToRun) throws IOException {
    final Process process = Runtime.getRuntime().exec(commandToRun);
    return new BufferedReader(new InputStreamReader(process.getInputStream()));
  }

  private static boolean lineSaysDiscoveredCredentials(final String line) {
    return line.contains("Discovered credentials");
  }

  public static boolean isDiscoveredCredentials(
      final String domain,
      final String protocol,
      final String host,
      final String port,
      final String usernames,
      final String passwords
  ) throws IOException {
    final String ncrackCommand = getCommandToRun(domain, protocol, host, port, usernames, passwords);
    System.out.println(ncrackCommand);
    final BufferedReader outputReader = runCommandAndGetOutputReader(ncrackCommand);
    boolean discoveredCredentials = false;
    String currentLine;

    while ((currentLine = outputReader.readLine()) != null) {
      System.out.println(currentLine);
      if (lineSaysDiscoveredCredentials(currentLine)) {
        discoveredCredentials = true;
      }
    }

    return discoveredCredentials;
  }

}
