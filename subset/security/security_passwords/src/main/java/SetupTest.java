import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.*;

public class SetupTest {
  String protocol;
  String hostAddress;
  String port;
  String macAddress;
  String domain;
  private static final int minimumMACAddressLength = 5;
  private static final int addressStartPosition = 0;
  private static final int addressEndPosition = 6;
  private static final int manufacturerNamePosition = 7;
  Map<String, String> macDevices = new HashMap<String, String>();
  private InputStream jsonStream = this.getClass().getResourceAsStream("/defaultPasswords.json");
  ReportHandler reportHandler;
  String[] usernames;
  String[] passwords;
  Gson gsonController = new Gson();

  public void readMacList() {
    try {
      InputStream inputStream = this.getClass().getResourceAsStream("/macList.txt");
      StringBuilder resultStringBuilder = new StringBuilder();
      BufferedReader br = new BufferedReader(new InputStreamReader(inputStream));
      String line;
      while ((line = br.readLine()) != null) {
        resultStringBuilder.append(line).append("\n");
        String macAddress;
        String manufacturer;
        if (line.length() > minimumMACAddressLength) {
          macAddress = line.substring(addressStartPosition, addressEndPosition);
          manufacturer = line.substring(manufacturerNamePosition);
          if (manufacturer.length() > addressStartPosition) {
            macDevices.put(macAddress, manufacturer);
          }
        }
      }
    } catch (Exception e) {
      e.printStackTrace();
    }
  }

  private void getMacAddress() {
    String formattedMac;
    try {
      macAddress = macAddress.replace(":", "");
      formattedMac = macAddress.substring(addressStartPosition, addressEndPosition).toUpperCase();
      getJsonFile(formattedMac);
    } catch (Exception e) {
      System.err.println(e.getMessage());
      reportHandler.addText(
          "RESULT skip security.passwords."+ protocol +" Device does not have a valid mac address");
      reportHandler.writeReport();
    }
  }

  public void getJsonFile(String macAddress) {
    JsonObject jsonFileContents =
        gsonController.fromJson(new InputStreamReader(jsonStream), JsonObject.class);
    JsonObject manufacturer = jsonFileContents.getAsJsonObject(macAddress);
    JsonArray userArray = manufacturer.getAsJsonArray("Usernames");
    JsonArray passwordArray = manufacturer.getAsJsonArray("Passwords");
    ArrayList<String> usernameList = new ArrayList<String>();
    ArrayList<String> passwordList = new ArrayList<String>();
    for (int i = 0; i < passwordArray.size(); i++){
      passwordList.add(passwordArray.get(i).getAsString());
    }
    for (int i = 0; i < userArray.size(); i++){
      usernameList.add(userArray.get(i).getAsString());
    }
    if (protocol.equals("ssh")) {
      RunSshTest runSshTest =
          new RunSshTest(usernameList, passwordList, hostAddress, port, reportHandler);
      Thread sshThread = new Thread(runSshTest);
      sshThread.start();
    } else {
      createConsoleCommand(usernameList, passwordList);
    }
  }

  public SetupTest(
      String protocol, String hostAddress, String port, String macAddress, String domain) {
    this.protocol = protocol;
    this.hostAddress = hostAddress;
    this.port = port;
    this.macAddress = macAddress;
    this.domain = domain;
    this.reportHandler = new ReportHandler(protocol);

    readMacList();
    getMacAddress();
  }

  private void createConsoleCommand(ArrayList<String> usernameList, ArrayList<String> passwordList) {

    String command;
    command = "ncrack ";

    if (protocol.equals("https") || protocol.equals("http")) {
      command += domain + " ";
    }

    command += protocol + "://";
    command += hostAddress + ":";
    command += port + " ";
    command += "--user ";

    StringBuilder str = new StringBuilder(command);

    for (String username : usernameList) {
      if (usernameList.indexOf(username) != (usernameList.size() - 1)) {
        str.append(username + ",");
      } else {
        str.append(username + " --pass ");
      }
    }
    for (String password : passwordList) {
      if (passwordList.indexOf(password) != (passwordList.size() - 1)) {
        str.append(password + ",");
      } else {
        str.append(password + " ");
      }
    }

    String finalCommand = str.toString();
    RunTest runnable = new RunTest(reportHandler);
    System.out.println("command is : " + finalCommand);
    runnable.runCommand(finalCommand, protocol);
  }
}
