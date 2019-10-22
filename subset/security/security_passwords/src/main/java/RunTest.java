import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class RunTest {
    private boolean foundCredentials;
    private ReportHandler reportHandler;

  public RunTest(ReportHandler reportHandler) {
    this.reportHandler = reportHandler;
  }

  public void runCommand(String command, String protocol) {
    try {
      Process process = Runtime.getRuntime().exec(command);
      BufferedReader input = new BufferedReader(new InputStreamReader(process.getInputStream()));
      String line;
      while ((line = input.readLine()) != null) {
        System.out.println(line);
        if (validateLine(line)) {
          foundCredentials = true;
        }
      }
      if (foundCredentials) {
        reportHandler.addText(
            "RESULT fail security.passwords." + protocol + " Default passwords has not been changed");
        reportHandler.writeReport();
      } else {
        reportHandler.addText(
            "RESULT pass security.passwords."+ protocol +"  Default passwords have been changed");
        reportHandler.writeReport();
      }
    } catch (IOException e) {
      e.printStackTrace();
    }
  }

  public boolean validateLine(String line) {
    return line.contains("Discovered credentials");
  }
}
