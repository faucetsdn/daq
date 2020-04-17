/* ReportHandler writes test results for the current protocol, and also does console output. */

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class ReportHandler {

  public final static String PASS = "pass";
  public final static String FAIL = "fail";
  public final static String SKIP_NOPORT = "skip_noport";
  public final static String SKIP_NOMAC = "skip_mac";
  public final static String SKIP_NOMAC_NOPORT = "skip_nomac_noport";

  private final static String PRINT_MESSAGE_STRING = "%s";
  private final static String UNABLE_TO_WRITE_REPORT_MESSAGE = "Unable to write message.";
  private final static String REPORT_FILE_PATH = "reports/%s_result.txt";

  private final static String SKIP_MESSAGE_NOMAC =
      "RESULT skip security.passwords.%s Could not lookup password info for mac-key: %s\n";
  private final static String SKIP_MESSAGE_NOPORT =
      "RESULT skip security.passwords.%s Port %s is not open on target device.\n";
  private final static String SKIP_MESSAGE_NOMAC_NOPORT =
      "RESULT skip security.passwords.%s Port %s is not open, %s not in password file.\n";
  private final static String FAIL_MESSAGE =
      "RESULT fail security.passwords.%s Default passwords have not been changed.\n";
  private final static String PASS_MESSAGE =
      "RESULT pass security.passwords.%s Default passwords have been changed.\n";
  private final static String NO_MESSAGE =
      "RESULT Unable to get message.";

  private static String getReportFilePath(final String protocol) {
    return String.format(REPORT_FILE_PATH, protocol);
  }

  private static File setupReportFile(final String reportFilePath) {
    final File reportFile = new File(reportFilePath);
    reportFile.getParentFile().mkdirs();
    return reportFile;
  }

  private static BufferedWriter getFileWriter(final File reportFile) throws IOException {
    return new BufferedWriter(new FileWriter(reportFile));
  }

  private static String getReportMessage(
      final String result,
      final String protocol,
      final String port,
      final String mac
  ) {
    String reportMessage;

    switch (result) {
      case PASS: {
        reportMessage = String.format(PASS_MESSAGE, protocol);
        break;
      }
      case FAIL: {
        reportMessage = String.format(FAIL_MESSAGE, protocol);
        break;
      }
      case SKIP_NOMAC: {
        reportMessage = String.format(SKIP_MESSAGE_NOMAC, protocol, mac);
        break;
      }
      case SKIP_NOPORT: {
        reportMessage = String.format(SKIP_MESSAGE_NOPORT, protocol, port);
        break;
      }
      case SKIP_NOMAC_NOPORT: {
        reportMessage = String.format(SKIP_MESSAGE_NOMAC_NOPORT, protocol, port, mac);
        break;
      }
      default: {
        reportMessage = NO_MESSAGE;
      }
    }

    return reportMessage;
  }

  public static void writeReportMessage(
      final String result,
      final String protocol,
      final String port,
      final String mac
  ) {
    final String reportFilePath = getReportFilePath(protocol);
    final File reportFile = setupReportFile(reportFilePath);
    final String reportMessage = getReportMessage(result, protocol, port, mac);

    try {
      final BufferedWriter reportWriter = getFileWriter(reportFile);
      reportWriter.write(reportMessage);
      reportWriter.close();
    } catch (final IOException e) {
      printMessage(UNABLE_TO_WRITE_REPORT_MESSAGE);
      printMessage(e.getMessage());
    }
  }

  public static void printMessage(final String message) {
    System.out.println(String.format(PRINT_MESSAGE_STRING, message));
  }

}
