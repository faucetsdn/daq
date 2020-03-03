/** Builds, runs and parses the result of an nmap command to check if all required ports: HTTP,
 * HTTPS, SSH and Telnet are open. */

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class NmapPortChecker {

  private static String NMAP_COMMAND_STRING = "nmap %s";

  private static String getCommandToRun(final String host) {
      return String.format(NMAP_COMMAND_STRING, host);
  }

  private static BufferedReader runCommandAndGetOutputReader(final String commandToRun) throws IOException {
    final Process process = Runtime.getRuntime().exec(commandToRun);
    return new BufferedReader(new InputStreamReader(process.getInputStream()));
  }

  private static boolean stringIndicatesHTTPIsOpen(final String lineFromOutput) {
    return lineFromOutput.contains("http") && lineFromOutput.contains("open");
  }

  private static boolean stringIndicatesHTTPSIsOpen(final String lineFromOutput) {
    return lineFromOutput.contains("https") && lineFromOutput.contains("open");
  }

  private static boolean stringIndicatesSSHIsOpen(final String lineFromOutput) {
    return lineFromOutput.contains("ssh") && lineFromOutput.contains("open");
  }

  private static boolean stringIndicatesTelnetIsOpen(final String lineFromOutput) {
    return lineFromOutput.contains("telnet") && lineFromOutput.contains("open");
  }

  private static boolean areAllDesiredPortsOpen(final BufferedReader outputReader) throws IOException {
    boolean isHTTPOpen = false;
    boolean isHTTPSOpen = false;
    boolean isSSHOpen = false;
    boolean isTelnetOpen = false;

    String currentLine;
    while ((currentLine = outputReader.readLine()) != null) {
      System.out.println(currentLine);
      if (stringIndicatesHTTPIsOpen(currentLine)) {
        isHTTPOpen = true;
      }
      if (stringIndicatesHTTPSIsOpen(currentLine)) {
        isHTTPSOpen = true;
      }
      if (stringIndicatesSSHIsOpen(currentLine)) {
        isSSHOpen = true;
      }
      if (stringIndicatesTelnetIsOpen(currentLine)) {
        isTelnetOpen = true;
      }
    }

    return isHTTPOpen && isHTTPSOpen && isSSHOpen && isTelnetOpen;
  }

  public static boolean checkAllPortsOpen(final String hostAddress) throws IOException {
    final String nmapCommand = getCommandToRun(hostAddress);
    final BufferedReader outputReader = runCommandAndGetOutputReader(nmapCommand);
    System.out.println(nmapCommand);
    return areAllDesiredPortsOpen(outputReader);
  }

}
