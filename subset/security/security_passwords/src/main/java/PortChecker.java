/* Runs nmap to check if HTTP, HTTPS, Telnet and SSH ports are open. */

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class PortChecker {

  private static final String NMAP_COMMAND_STRING = "nmap %s";
  private static final String PORT_CHECK_STRING = "%s/tcp";
  private static final String OPEN_CHECK_STRING = "open";

  private static String getCommand(final String host) {
    return String.format(NMAP_COMMAND_STRING, host);
  }

  private static BufferedReader runCommandGetReader(final String command) throws IOException {
    final Process process = Runtime.getRuntime().exec(command);
    return new BufferedReader(new InputStreamReader(process.getInputStream()));
  }

  private static boolean checkIfDesiredPortOpen(
      final BufferedReader bufferedReader,
      final String port,
      final String protocol
  ) throws IOException {
    boolean isPortOpen = false;

    String currentLine;
    while ((currentLine = bufferedReader.readLine()) != null) {
      ReportHandler.printMessage(currentLine);
      if (currentLine.contains(String.format(PORT_CHECK_STRING, port)) &&
          currentLine.contains(protocol) &&
          currentLine.contains(OPEN_CHECK_STRING)) {
        isPortOpen = true;
      }
    }

    return isPortOpen;
  }

  private static void closeBufferedReader(final BufferedReader bufferedReader) throws IOException {
    bufferedReader.close();
  }

  public static boolean checkDesiredPortOpen(
      final String hostAddress,
      final String port,
      final String protocol
  ) throws IOException {
    final String command = getCommand(hostAddress);
    final BufferedReader bufferedReader = runCommandGetReader(command);
    final boolean desiredPortIsOpen = checkIfDesiredPortOpen(bufferedReader, port, protocol);

    ReportHandler.printMessage(command);

    closeBufferedReader(bufferedReader);

    return desiredPortIsOpen;
  }

}
