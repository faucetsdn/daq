/** Reads from defaultPasswords.json to retrieve default username and password data. */

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

import java.io.*;

public class DefaultCredentials {

  public static final String DEFAULT_PASSWORDS_FILE = "/tmp/%s_passwords.txt";
  public static final String DEFAULT_USERNAMES_FILE = "/tmp/%s_usernames.txt";

  private static final String DEFAULT_PASSWORDS_JSON_FILE = "/defaultPasswords.json";
  private static final String JSON_USERNAME_ELEMENT = "Usernames";
  private static final String JSON_PASSWORD_ELEMENT = "Passwords";
  private static final int MAC_ADDRESS_START_POSITION = 0;
  private static final int MAC_ADDRESS_END_POSITION = 6;

  private static String getFormattedMacAddress(final String macAddress) {
    final String simpleMacAddress = macAddress.replace(":", "");
    final String macAddressOUI = simpleMacAddress.substring(MAC_ADDRESS_START_POSITION, MAC_ADDRESS_END_POSITION);
    return macAddressOUI.toUpperCase();
  }

  private static JsonObject getJsonFileContentsAsObject() {
    final Gson gsonController = new Gson();
    final InputStream jsonStream = DefaultCredentials.class.getResourceAsStream(DEFAULT_PASSWORDS_JSON_FILE);
    return gsonController.fromJson(new InputStreamReader(jsonStream), JsonObject.class);
  }

  private static void writeArrayToCredentialFiles(final JsonArray array, final String filePath) throws IOException {
    final File file = new File(filePath);
    final BufferedWriter bufferedWriter = new BufferedWriter(new FileWriter(file));

    for (final JsonElement element : array) {
      bufferedWriter.write(element.getAsString() + "\n");
    }

    bufferedWriter.close();
  }

  public static String getFormattedUsernameFileWithProtocol(final String protocol) {
    return String.format(DEFAULT_USERNAMES_FILE, protocol);
  }

  public static String getFormattedPasswordFileWithProtocol(final String protocol) {
    return String.format(DEFAULT_PASSWORDS_FILE, protocol);
  }

  public static void writeUsernamesToFile(final String macAddress, final String protocol) throws IOException {
    final String formattedMac = getFormattedMacAddress(macAddress);
    final String formattedUsernameFile = getFormattedUsernameFileWithProtocol(protocol);
    final JsonObject jsonFileContentsAsObject = getJsonFileContentsAsObject();
    final JsonObject jsonFileCredentialsForMacAddress = jsonFileContentsAsObject.getAsJsonObject(formattedMac);
    final JsonArray usernameJsonArray = jsonFileCredentialsForMacAddress.getAsJsonArray(JSON_USERNAME_ELEMENT);

    writeArrayToCredentialFiles(usernameJsonArray, formattedUsernameFile);
  }

  public static void writePasswordsToFile(final String macAddress, final String protocol) throws IOException {
    final String formattedMac = getFormattedMacAddress(macAddress);
    final String formattedPasswordFile = getFormattedPasswordFileWithProtocol(protocol);
    final JsonObject jsonFileContentsAsObject = getJsonFileContentsAsObject();
    final JsonObject jsonFileCredentialsForMacAddress = jsonFileContentsAsObject.getAsJsonObject(formattedMac);
    final JsonArray passwordJsonArray = jsonFileCredentialsForMacAddress.getAsJsonArray(JSON_PASSWORD_ELEMENT);

    writeArrayToCredentialFiles(passwordJsonArray, formattedPasswordFile);
  }

  public static boolean defaultCredentialsFileHasMacAddress(final String macAddress) {
    final String formattedMac = getFormattedMacAddress(macAddress);
    return getJsonFileContentsAsObject().has(formattedMac);
  }
}
