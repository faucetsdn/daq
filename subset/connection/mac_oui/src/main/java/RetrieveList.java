import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.Map;

public class RetrieveList {
  String macAddress;
  Map<String, String> macDevices = new HashMap<>();
  static final int minimumMACAddressLength = 5;

  RetrieveList(String macAddress) {
    this.macAddress = macAddress;
  }

  public void startTest() {
    readLocalFile();
    MacLookup macLookup = new MacLookup(macDevices, macAddress);
    macLookup.startTest();
  }

  public void readLocalFile(){
    try {
      System.out.println("Reading local file...");
      InputStream inputStream = this.getClass().getResourceAsStream("/macList.txt");
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
