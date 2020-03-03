/** Reads from defaultPasswords.json and macList.txt files to make an ncrack command, and a list
 * usernames and passwords to use. */

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.*;

public class TestSetup {

  private static final String DEFAULT_PASSWORDS_JSON_FILE = "/defaultPasswords.json";
  private static final String MAC_AND_MANUFACTURER_LIST_FILE = "/macList.txt";
  private static final int MINIMUM_MAC_ADDRESS_LENGTH = 5;
  private static final int ADDRESS_START_POSITION = 0;
  private static final int ADDRESS_END_POSITION = 6;
  private static final int MANUFACTURER_NAME_POSITION = 7;

  private String protocol;
  private String hostAddress;
  private String port;
  private String macAddress;
  private String domain;

  private Map<String, String> macDeviceAndManufacturerMap = new HashMap<>();
  private ArrayList<String> usernameList;
  private ArrayList<String> passwordList;
  private String usernameListString;
  private String passwordListString;
  private String ncrackCommand;

  public TestSetup(String hostAddress, String protocol, String port, String macAddress, String domain) {
    this.hostAddress = hostAddress;
    this.protocol = protocol;
    this.port = port;
    this.macAddress = macAddress;
    this.domain = domain;

    final JsonObject deviceUsernamePasswordData = getUsernameAndPasswordDataFromJson();
    usernameList = getUsernameListFromJSONObject(deviceUsernamePasswordData);
    passwordList = getPasswordListFromJSONObject(deviceUsernamePasswordData);
//  ncrackCommand = createNcrackCommandString(usernameList, passwordList);

    usernameListString = getUsernameListStringFromArrayList(usernameList);
    passwordListString = getUsernameListStringFromArrayList(passwordList);

    readMacListIntoDeviceAndManufacturerMap();
  }

  private JsonObject getUsernameAndPasswordDataFromJson() {
    final Gson gsonController = new Gson();
    final InputStream jsonStream = this.getClass().getResourceAsStream(DEFAULT_PASSWORDS_JSON_FILE);
    final JsonObject jsonFileContents = gsonController.fromJson(new InputStreamReader(jsonStream), JsonObject.class);
    return jsonFileContents.getAsJsonObject(getFormattedMacAddress());
  }

  private boolean isLineInMacListRightLength(final String line) {
    return line.length() > MINIMUM_MAC_ADDRESS_LENGTH;
  }

  private boolean isManufacturerInfoPresentInMacListLine(final String manufacturer) {
    return manufacturer.length() > ADDRESS_START_POSITION;
  }

  private String getMacAddressFromMacListLine(final String line) {
    return line.substring(ADDRESS_START_POSITION, ADDRESS_END_POSITION);
  }

  private String getManufacturerFromMacListLine(final String line) {
    return line.substring(MANUFACTURER_NAME_POSITION);
  }

  private String getFormattedMacAddress() {
    final String simpleMacAddress = macAddress.replace(":", "");
    final String macAddressOUI = simpleMacAddress.substring(ADDRESS_START_POSITION, ADDRESS_END_POSITION);
    return macAddressOUI.toUpperCase();
  }

  private ArrayList<String> getUsernameListFromJSONObject(final JsonObject deviceUsernamePasswordData) {
    JsonArray usernameJSONArray = deviceUsernamePasswordData.getAsJsonArray("Usernames");
    ArrayList<String> usernameList = new ArrayList<>();

    for (int i = 0; i < usernameJSONArray.size(); i++){
      usernameList.add(usernameJSONArray.get(i).getAsString());
    }

    return usernameList;
  }

  private ArrayList<String> getPasswordListFromJSONObject(final JsonObject deviceUsernamePasswordData) {
    JsonArray passwordJSONArray = deviceUsernamePasswordData.getAsJsonArray("Passwords");
    ArrayList<String> passwordList = new ArrayList<>();

    for (int i = 0; i < passwordJSONArray.size(); i++) {
      passwordList.add(passwordJSONArray.get(i).getAsString());
    }

    return passwordList;
  }

  private String getUsernameListStringFromArrayList(final ArrayList<String> usernameList) {
    final StringBuilder stringBuilder = new StringBuilder();

    for (String username : usernameList) {
      stringBuilder.append(username);

      if (usernameList.indexOf(username) < usernameList.size() - 1) {
        stringBuilder.append(",");
      }
    }

    return stringBuilder.toString();
  }

  private String getPasswordListStringFromArrayList(final ArrayList<String> passwordList) {
    final StringBuilder stringBuilder = new StringBuilder();

    for (String username : passwordList) {
      stringBuilder.append(username);

      if (passwordList.indexOf(username) < passwordList.size() - 1) {
        stringBuilder.append(",");
      }
    }

    return stringBuilder.toString();
  }

//  private String createNcrackCommandString(ArrayList<String> usernameList, ArrayList<String> passwordList) {
//    String command;
//    command = "ncrack ";
//
//    if (protocol.equals("https") || protocol.equals("http")) {
//      command += domain + " ";
//    }
//
//    command += protocol + "://";
//    command += hostAddress + ":";
//    command += port + " ";
//    command += "--user ";
//
//    StringBuilder str = new StringBuilder(command);
//
//    for (String username : usernameList) {
//      if (usernameList.indexOf(username) != (usernameList.size() - 1)) {
//        str.append(username + ",");
//      } else {
//        str.append(username + " --pass ");
//      }
//    }
//    for (String password : passwordList) {
//      if (passwordList.indexOf(password) != (passwordList.size() - 1)) {
//        str.append(password + ",");
//      } else {
//        str.append(password + " ");
//      }
//    }
//
//    return str.toString();
//  }

  private void readMacListIntoDeviceAndManufacturerMap() {
    try {
      InputStream inputStream = this.getClass().getResourceAsStream(MAC_AND_MANUFACTURER_LIST_FILE);
      BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(inputStream));
      String line;

      while ((line = bufferedReader.readLine()) != null) {

        if (isLineInMacListRightLength(line)) {
          final String macAddress = getMacAddressFromMacListLine(line);
          final String manufacturer = getManufacturerFromMacListLine(line);

          if (isManufacturerInfoPresentInMacListLine(manufacturer)) {
            macDeviceAndManufacturerMap.put(macAddress, manufacturer);
          }
        }
      }

    } catch (Exception e) {
      e.printStackTrace();
    }
  }

  public ArrayList<String> getUsernameList() {
    return usernameList;
  }

  public ArrayList<String> getPasswordList() {
    return passwordList;
  }

  public String getUsernameListString() {
    return usernameListString;
  }

  public String getPasswordListString() {
    return passwordListString;
  }

  public String getNcrackCommand() {
    return ncrackCommand;
  }

}
