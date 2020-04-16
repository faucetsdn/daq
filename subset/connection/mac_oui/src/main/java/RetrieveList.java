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
    readLocalFile();
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


  /**
   * Read the file from a URL and update mac prefixes
   * @param fileURL HTTP URL of the file to be read
   * @throws IOException - URL not reachable
   */
  public void readFileFromUrlAndUpdateMac(String fileURL) throws IOException {
    URL url = new URL(fileURL);
    HttpURLConnection httpConn = (HttpURLConnection) url.openConnection();
    int responseCode = httpConn.getResponseCode();

    // always check HTTP response code first
    if (responseCode == HttpURLConnection.HTTP_OK) {
      String fileName = "";
      String disposition = httpConn.getHeaderField("Content-Disposition");
      String contentType = httpConn.getContentType();
      int contentLength = httpConn.getContentLength();

      if (disposition != null) {
        // extracts file name from header field
        int index = disposition.indexOf("filename=");
        if (index > 0) {
          fileName = disposition.substring(index + 10,
                  disposition.length() - 1);
        }
      } else {
        // extracts file name from URL
        fileName = fileURL.substring(fileURL.lastIndexOf("/") + 1);
      }

      System.out.println("Content-Type = " + contentType);
      System.out.println("Content-Disposition = " + disposition);
      System.out.println("Content-Length = " + contentLength);
      System.out.println("fileName = " + fileName);

      // opens input stream from the HTTP connection
      InputStream inputStream = httpConn.getInputStream();
      BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(inputStream));
      String line;
      while ((line = bufferedReader.readLine()) != null) {
        if (line.length() > minimumMACAddressLength) {
          String macAddress = line.substring(0, 6);
          String manufacturer = line.substring(7);
          if (manufacturer.length() > 0) {
            macDevices.put(macAddress, manufacturer);
          }
        }
      }
      inputStream.close();

      System.out.println("File read");
    } else {
      System.out.println("No file to read. Server replied HTTP code: " + responseCode);
    }
    httpConn.disconnect();
  }
}
