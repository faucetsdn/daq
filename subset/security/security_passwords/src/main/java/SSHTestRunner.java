import com.jcraft.jsch.JSch;
import com.jcraft.jsch.JSchException;
import com.jcraft.jsch.Session;
import java.util.*;

public class SSHTestRunner {

  private Session session;
  private JSch jsch = new JSch();
  private ArrayList<String>  usernames;
  private ArrayList<String> passwords;
  private String hostAddress;
  private int port;
  private String mac;
  private String protocol;
  private boolean testFinished = false;
  private int passwordIndex = 0;
  private int usernameIndex = 0;

  public SSHTestRunner(
      ArrayList<String> usernames,
      ArrayList<String> passwords,
      String hostAddress,
      String protocol,
      String port,
      String mac
  ) {
    this.usernames = usernames;
    this.passwords = passwords;
    this.hostAddress = hostAddress;
    this.port = Integer.parseInt(port);
    this.protocol = protocol;
    this.mac = mac;
  }

  public void StartTest() {
    while (!testFinished) {
      if (passwordIndex == passwords.size()) {
        usernameIndex++;
        passwordIndex = 0;
      }
      if (usernameIndex > usernames.size() - 1) {
        testFinished = true;
        ReportHandler.writeReportMessage("pass", protocol, String.valueOf(port), mac);
      } else {
        try {
          session = jsch.getSession(usernames.get(usernameIndex), hostAddress, port);
          session.setPassword(passwords.get(passwordIndex));
          try {
            Properties config = new Properties();
            config.put("StrictHostKeyChecking", "no");
            session.setConfig(config);
            session.connect();
            ReportHandler.writeReportMessage("fail", protocol, String.valueOf(port), mac);
            testFinished = true;
          } catch (JSchException e) {
            if (e.toString().contains("Connection refused")) {
              ReportHandler.writeReportMessage("skip_noport", protocol, String.valueOf(port), mac);
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
    session.disconnect();
  }
}
