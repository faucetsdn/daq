import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class ReportHandler {

  private String report = "";
  private String reportFilePath;
  File reportFile;

  private static String REPORT_SKIP_MESSAGE_MAC = "RESULT skip security.passwords.%s Could not lookup password info for mac-key: %s";
  private static String REPORT_SKIP_MESSAGE_NOPORT = "RESULT skip security.passwords.%s Ports are not open.";
  private static String REPORT_FAIL_MESSAGE = "RESULT fail security.passwords.%s Default passwords have not been changed.";
  private static String REPORT_PASS_MESSAGE = "RESULT pass security.passwords.%s Default passwords have been changed.";

  public ReportHandler(final String protocol) {
    this.reportFilePath = "reports/" + protocol + "_report.txt";
  }

  public void addText(final String text) {
    report += text + '\n';
  }

  public void writeReport() {
    reportFile = new File(reportFilePath);
    try {
      reportFile.getParentFile().mkdirs();
      try (BufferedWriter writer = new BufferedWriter(new FileWriter(reportFile))) {
        writer.write(report);
      }
    } catch (IOException e) {
      System.err.println("Unable to write report");
      System.out.println(e.getMessage());
    }
  }
}
