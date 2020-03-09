/** Builds, runs and parses the result of an nmap command to check if all required ports: HTTP,
 * HTTPS, SSH and Telnet are open. */

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class PortChecker {

  private static String NMAP_COMMAND_STRING = "nmap %s";

  private static String getCommandToRun(final String host) {
      return String.format(NMAP_COMMAND_STRING, host);
  }

  private static BufferedReader runNmapCommandAndGetOutputReader(final String commandToRun) throws IOException {
    final Process process = Runtime.getRuntime().exec(commandToRun);
    return new BufferedReader(new InputStreamReader(process.getInputStream()));
  }

  private static boolean checkIfDesiredPortOpen(final BufferedReader bufferedReader, final String port, final String protocol) throws IOException {
    boolean isPortOpen = false;

    String currentLine;
    while ((currentLine = bufferedReader.readLine()) != null) {
      System.out.println(currentLine);
      if (currentLine.contains(port + "/tcp") && currentLine.contains(protocol) && currentLine.contains("open")) {
        isPortOpen = true;
      }
    }

    return isPortOpen;
  }

  private static void closeBufferedReader(final BufferedReader bufferedReader) throws IOException {
    bufferedReader.close();
  }

  public static boolean checkDesiredPortOpen(final String hostAddress, final String port, final String protocol) throws IOException {
    final String nmapCommand = getCommandToRun(hostAddress);
    final BufferedReader bufferedReader = runNmapCommandAndGetOutputReader(nmapCommand);
    final boolean desiredPortIsOpen = checkIfDesiredPortOpen(bufferedReader, port, protocol);

    System.out.println(nmapCommand);

    closeBufferedReader(bufferedReader);

    return desiredPortIsOpen;
  }

}
