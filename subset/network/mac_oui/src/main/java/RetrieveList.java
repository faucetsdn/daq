import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.HashMap;
import java.util.Map;

public class RetrieveList {
  String macAddress;
  Map<String, String> macDevices = new HashMap<>();
  static final int minimumMACAddressLength = 5;
  private static final int BUFFER_SIZE = 4096;

  RetrieveList(String macAddress) {
    this.macAddress = macAddress;
  }

  public void startTest() {
    // Read the local file
    readLocalFile();
    // Map the mac prefixes
    MacLookup macLookup = new MacLookup(macDevices, macAddress);
    // Start the manufacturer lookup test
    macLookup.startTest();
  }

  public void readLocalFile(){
    try {
      System.out.println("Reading local file...");
      ClassLoader classLoader = ClassLoader.getSystemClassLoader();
      InputStream inputStream = this.getClass().getClassLoader().getResourceAsStream("macList.txt");
      StringBuilder resultStringBuilder = new StringBuilder();
      BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(inputStream));
      String line;
      while ((line = bufferedReader.readLine()) != null) {
        resultStringBuilder.append(line).append("\n");
        String macAddress;
        String manufacturer;
        if (line.length() > minimumMACAddressLength) {
          macAddress = line.substring(0, 6);
          manufacturer = line.substring(7);
          if (manufacturer.length() > 0) {
            macDevices.put(macAddress, manufacturer);
          }
        }
      }
    } catch (Exception e) {
      System.out.println(e);
      System.err.println("Can not read local file");
    }
  }

}
