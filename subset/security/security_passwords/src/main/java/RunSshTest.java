import com.jcraft.jsch.Channel;
import com.jcraft.jsch.JSch;
import com.jcraft.jsch.JSchException;
import com.jcraft.jsch.Session;
import java.util.*;

public class RunSshTest implements Runnable {
  private ReportHandler reportHandler;
  private Session session;
  Channel channel;
  private JSch jsch = new JSch();
  private ArrayList<String>  usernames = new ArrayList<String>();
  private ArrayList<String> passwords = new ArrayList<String>();
  private String hostAddress;
  private int port;
  private boolean testFinished = false;
  private int passwordIndex = 0;
  private int usernameIndex = 0;
  private int attempts = -1;

  public RunSshTest(
      ArrayList<String> usernames,
      ArrayList<String> passwords,
      String hostAddress,
      String port,
      ReportHandler reportHandler) {
    this.usernames = usernames;
    this.passwords = passwords;
    this.hostAddress = hostAddress;
    this.port = Integer.parseInt(port);
    this.reportHandler = reportHandler;
  }

  public void StartTest() {
    while (!testFinished) {
      if (passwordIndex == passwords.size()) {
        usernameIndex++;
        passwordIndex = 0;
      }
      if (usernameIndex > usernames.size() - 1) {
        testFinished = true;
        reportHandler.addText("RESULT pass security.passwords.ssh Default passwords have been changed");
      } else {
        attempts++;
        try {
          session = jsch.getSession(usernames.get(usernameIndex), hostAddress, port);
          session.setPassword(passwords.get(passwordIndex));
          try {
            Properties config = new Properties();
            config.put("StrictHostKeyChecking", "no");
            session.setConfig(config);
            session.connect();
            reportHandler.addText(
                "RESULT fail security.passwords.ssh Default passwords have not been changed");
            testFinished = true;
          } catch (JSchException e) {
            if (e.toString().contains("Connection refused")) {
              reportHandler.addText(
                  "RESULT skip security.passwords.ssh SSH is not enabled on selected device");
              testFinished = true;
              break;
            } else {
              passwordIndex++;
            }
          }
        } catch (JSchException e) {
          e.printStackTrace();
        }
      }
    }
    reportHandler.writeReport();
    session.disconnect();
  }

  @Override
  public void run() {
    StartTest();
  }
}
