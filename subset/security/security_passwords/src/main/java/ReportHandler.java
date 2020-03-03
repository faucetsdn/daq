/** ReportHandler is responsible for writing test results to do with the current protocol. */

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class ReportHandler {

  private static String REPORT_FILE_PATH = "reports/%s_report.txt";
  private static String REPORT_SKIP_MESSAGE_MAC = "RESULT skip security.passwords.%s Could not lookup password info for mac-key: %s\n";
  private static String REPORT_SKIP_MESSAGE_NOPORT = "RESULT skip security.passwords.%s Port %s is not open.\n";
  private static String REPORT_FAIL_MESSAGE = "RESULT fail security.passwords.%s Default passwords have not been changed.\n";
  private static String REPORT_PASS_MESSAGE = "RESULT pass security.passwords.%s Default passwords have been changed.\n";

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

  private static String getReportMessage(final String state, final String protocol, final String port, final String mac) {
    String reportMessage;

    switch (state) {
      case "pass": reportMessage = String.format(REPORT_PASS_MESSAGE, protocol); break;
      case "fail": reportMessage = String.format(REPORT_FAIL_MESSAGE, protocol); break;
      case "skip_mac": reportMessage = String.format(REPORT_SKIP_MESSAGE_MAC, protocol, mac); break;
      case "skip_noport": reportMessage = String.format(REPORT_SKIP_MESSAGE_NOPORT, protocol, port); break;
      default: reportMessage = "RESULT Unable to get message.";
    }

    return reportMessage;
  }

  public static void writeReportMessage(final String state, final String protocol, final String port, final String mac) {
    final String reportFilePath = getReportFilePath(protocol);
    final File reportFile = setupReportFile(reportFilePath);
    final String reportMessage = getReportMessage(state, protocol, port, mac);

    try {
      final BufferedWriter reportWriter = getFileWriter(reportFile);
      reportWriter.write(reportMessage);
      reportWriter.close();
    } catch (final IOException e) {
      System.err.println("Unable to write report");
      System.out.println(e.getMessage());
    }
  }

}
