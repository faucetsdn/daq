import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class Report {
  private final String reportFilename = "tmp/report.txt";

  public void writeReport(String certificateReport) {
    try {
      String[] directory = reportFilename.split("/");

      File dir = new File(directory[directory.length - 2]);
      if (!dir.exists()) dir.mkdirs();

      BufferedWriter writer = new BufferedWriter(new FileWriter(reportFilename));
      writer.write(certificateReport);
      writer.close();
    } catch (IOException e) {
      System.out.println("Exception writeReport:" + e.getMessage());
    }
  }
}

