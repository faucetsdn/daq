import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class ReportHandler {
  String report = "Mac OUI Test\n";
  File reportFile = new File("report/report.txt");

  public void addText(String text) {
    report += text + '\n';
  }

  public void writeReport() {
    try {
      reportFile.getParentFile().mkdirs();
      try (BufferedWriter writer = new BufferedWriter(new FileWriter(reportFile))) {
        writer.write(report);
      }
    } catch (IOException e) {
      System.err.println("could not write report");
      System.out.println(e);
    }
  }
}
