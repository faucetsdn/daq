import java.util.Map;

public class MacLookup {
  String macAddress;
  Map macDevices;
  ReportHandler reportHandler = new ReportHandler();

  MacLookup(Map macDevices, String macAddress) {
    this.macDevices = macDevices;
    this.macAddress = macAddress;
  }

  public void startTest() {
    System.out.println("Starting connection.mac_oui test...");
    String splicedMac = macAddress.replace(":", "");
    String formattedMac = splicedMac.substring(0, 6).toUpperCase();
    System.out.println(formattedMac);
    try {
      String manufacturer = macDevices.get(formattedMac).toString();
      reportHandler.addText("RESULT pass connection.mac_oui");
      reportHandler.writeReport();
      System.out.println(formattedMac + " " + manufacturer);
    } catch (NullPointerException e) {
      System.out.println(e + " could not find the manufacturer");
      reportHandler.addText("RESULT fail connection.mac_oui Manufacturer prefix not found!");
      reportHandler.writeReport();
    }
  }
}
