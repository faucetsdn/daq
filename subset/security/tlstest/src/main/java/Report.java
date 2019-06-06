import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class Report {

  boolean debug = true;

  String reportFilename = "tmp/report.txt";

  public void writeReport(String certificateReport) {
    try {
      if (debug) {
        System.out.println("report:" + certificateReport);
      }

      String[] directory = reportFilename.split("/");

      File dir = new File(directory[directory.length - 2]);
      if (!dir.exists()) dir.mkdirs();

      BufferedWriter writer = new BufferedWriter(new FileWriter(reportFilename));
      writer.write(certificateReport);
      writer.close();
    } catch (IOException e) {
      System.err.println("Exception writeReport:" + e.getMessage());
    }
  }
}