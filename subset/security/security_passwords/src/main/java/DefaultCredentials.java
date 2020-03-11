/* Reads from defaultPasswords.json to retrieve default username and password data for a mac. */

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

import java.io.*;

public class DefaultCredentials {

  public static final String DEFAULT_PASSWORDS_FILE = "/tmp/%s_passwords.txt";
  public static final String DEFAULT_USERNAMES_FILE = "/tmp/%s_usernames.txt";

  private static final String DEFAULT_PASSWORDS = "/defaultPasswords.json";
  private static final String JSON_USERNAME_ELEMENT = "Usernames";
  private static final String JSON_PASSWORD_ELEMENT = "Passwords";
  private static final String WRITE_ELEMENT_LINE = "%s\n";
  private static final String MAC_SEPARATOR = ":";
  private static final String EMPTY = "";
  private static final int MAC_ADDRESS_START = 0;
  private static final int MAC_ADDRESS_END = 6;

  private static String getFormattedMacAddress(final String macAddress) {
    final String simpleMacAddress = macAddress.replace(MAC_SEPARATOR, EMPTY);
    final String macAddressOUI = simpleMacAddress.substring(MAC_ADDRESS_START, MAC_ADDRESS_END);
    return macAddressOUI.toUpperCase();
  }

  private static JsonObject getJsonFileContentsAsObject() {
    final Gson gsonController = new Gson();
    final InputStream jsonStream = DefaultCredentials.class.getResourceAsStream(DEFAULT_PASSWORDS);
    return gsonController.fromJson(new InputStreamReader(jsonStream), JsonObject.class);
  }

  private static void writeArrayToCredentialFiles(
      final JsonArray array,
      final String filePath
  ) throws IOException {
    final File file = new File(filePath);
    final BufferedWriter bufferedWriter = new BufferedWriter(new FileWriter(file));

    for (final JsonElement element : array) {
      bufferedWriter.write(String.format(WRITE_ELEMENT_LINE, element.getAsString()));
    }

    bufferedWriter.close();
  }

  public static String getUsernameFilePath(final String protocol) {
    return String.format(DEFAULT_USERNAMES_FILE, protocol);
  }

  public static String getPasswordFilePath(final String protocol) {
    return String.format(DEFAULT_PASSWORDS_FILE, protocol);
  }

  public static void writeUsernamesToFile(
      final String macAddress,
      final String protocol
  ) throws IOException {
    final String formattedMac = getFormattedMacAddress(macAddress);
    final String formattedUsernameFile = getUsernameFilePath(protocol);
    final JsonObject fileContents = getJsonFileContentsAsObject();
    final JsonObject credentialsForMac = fileContents.getAsJsonObject(formattedMac);
    final JsonArray usernameJsonArray = credentialsForMac.getAsJsonArray(JSON_USERNAME_ELEMENT);

    writeArrayToCredentialFiles(usernameJsonArray, formattedUsernameFile);
  }

  public static void writePasswordsToFile(
      final String macAddress,
      final String protocol
  ) throws IOException {
    final String formattedMac = getFormattedMacAddress(macAddress);
    final String formattedPasswordFile = getPasswordFilePath(protocol);
    final JsonObject fileContents = getJsonFileContentsAsObject();
    final JsonObject credentialsForMac = fileContents.getAsJsonObject(formattedMac);
    final JsonArray passwordJsonArray = credentialsForMac.getAsJsonArray(JSON_PASSWORD_ELEMENT);

    writeArrayToCredentialFiles(passwordJsonArray, formattedPasswordFile);
  }

  public static boolean credentialsFileHasMacAddress(final String macAddress) {
    final String formattedMac = getFormattedMacAddress(macAddress);
    return getJsonFileContentsAsObject().has(formattedMac);
  }
}
