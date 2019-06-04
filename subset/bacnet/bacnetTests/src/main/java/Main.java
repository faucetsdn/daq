public class Main {

  public static void main(String[] args) throws Exception {
    if (args.length < 3) {
      throw new IllegalArgumentException("Usage: bacnetTestId broadcastIp localIp");
    }

    String bacnetTestId = args[0];
    String broadcastIp = args[1];
    String localIp = args[2];

    switch (bacnetTestId) {
      case "bacnet_VERSION":
        new VersionTest(localIp, broadcastIp);
        break;

      default:
        throw new IllegalArgumentException("Invalid bacnetTestId.");
    }
  }
}
