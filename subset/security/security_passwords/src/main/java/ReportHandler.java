/** ReportHandler is responsible for writing test results to do with the current protocol. */

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class ReportHandler {

  public final static String RESULT_PASS = "pass";
  public final static String RESULT_FAIL = "fail";
  public final static String RESULT_SKIP_NOPORT = "skip_noport";
  public final static String RESULT_SKIP_NOMAC = "skip_mac";
  public final static String RESULT_SKIP_NOMAC_NOPORT = "skip_nomac_noport";

  private final static String REPORT_FILE_PATH = "reports/%s_report.txt";
  private final static String REPORT_SKIP_MESSAGE_NOMAC = "RESULT skip security.passwords.%s Could not lookup password info for mac-key: %s\n";
  private final static String REPORT_SKIP_MESSAGE_NOPORT = "RESULT skip security.passwords.%s Port %s is not open on target device.\n";
  private final static String REPORT_SKIP_MESSAGE_NOMAC_NOPORT = "RESULT skip security.passwords.%s Port %s is not open, %s not in password file.\n";
  private final static String REPORT_FAIL_MESSAGE = "RESULT fail security.passwords.%s Default passwords have not been changed.\n";
  private final static String REPORT_PASS_MESSAGE = "RESULT pass security.passwords.%s Default passwords have been changed.\n";
  private final static String REPORT_NO_MESSAGE = "RESULT Unable to get message.";

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

  private static String getReportMessage(final String result, final String protocol, final String port, final String mac) {
    String reportMessage;

    switch (result) {
      case RESULT_PASS: reportMessage = String.format(REPORT_PASS_MESSAGE, protocol); break;
      case RESULT_FAIL: reportMessage = String.format(REPORT_FAIL_MESSAGE, protocol); break;
      case RESULT_SKIP_NOMAC: reportMessage = String.format(REPORT_SKIP_MESSAGE_NOMAC, protocol, mac); break;
      case RESULT_SKIP_NOPORT: reportMessage = String.format(REPORT_SKIP_MESSAGE_NOPORT, protocol, port); break;
      case RESULT_SKIP_NOMAC_NOPORT: reportMessage = String.format(REPORT_SKIP_MESSAGE_NOMAC_NOPORT, protocol, port, mac); break;
      default: reportMessage = REPORT_NO_MESSAGE;
    }

    return reportMessage;
  }

  public static void writeReportMessage(final String result, final String protocol, final String port, final String mac) {
    final String reportFilePath = getReportFilePath(protocol);
    final File reportFile = setupReportFile(reportFilePath);
    final String reportMessage = getReportMessage(result, protocol, port, mac);

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
