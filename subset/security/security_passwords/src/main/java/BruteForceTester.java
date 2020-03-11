/* Runs pentesting tools ncrack and hydra to crack the passwords of the device. */

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class BruteForceTester {

  private static final String SSH = "ssh";
  private static final String TELNET = "telnet";
  private static final String HYDRA_SUCCESS_MESSAGE = "successfully completed";
  private static final String NCRACK_SUCCESS_MESSAGE = "Discovered credentials";
  private static final String NCRACK_COMMAND = "ncrack %s %s://%s:%s -U %s -P %s";
  private static final String HYDRA_COMMAND = "hydra -L %s -P %s %s %s -s %s";

  private static String getCommand(
      final String domain,
      final String protocol,
      final String host,
      final String port,
      final String usersFile,
      final String passwordsFile
  ) {
    if (protocol.equals(SSH) || protocol.equals(TELNET)) {
      return String.format(HYDRA_COMMAND, usersFile, passwordsFile, host, protocol, port);
    }
    else {
      return String.format(NCRACK_COMMAND, domain, protocol, host, port, usersFile, passwordsFile);
    }
  }

  private static BufferedReader runCommandGetReader(final String commandToRun) throws IOException {
    final Process process = Runtime.getRuntime().exec(commandToRun);
    return new BufferedReader(new InputStreamReader(process.getInputStream()));
  }

  private static boolean lineIndicatesCredentialsFound(final String protocol, final String line) {
    if (protocol.equals(SSH) || protocol.equals(TELNET)) {
      return line.contains(HYDRA_SUCCESS_MESSAGE);
    }
    else {
      return line.contains(NCRACK_SUCCESS_MESSAGE);
    }
  }

  public static String start(
      final String domain,
      final String protocol,
      final String host,
      final String port,
      final String usernamesFile,
      final String passwordsFile
  ) throws IOException {
    final String command = getCommand(domain, protocol, host, port, usernamesFile, passwordsFile);
    final BufferedReader outputReader = runCommandGetReader(command);

    ReportHandler.printMessage(command);
    String result = ReportHandler.PASS;
    String currentLine;

    while ((currentLine = outputReader.readLine()) != null) {
      ReportHandler.printMessage(currentLine);
      if (lineIndicatesCredentialsFound(protocol, currentLine)) {
        result = ReportHandler.FAIL;
      }
    }

    return result;
  }

}
