public class Main {

  public static void main(String[] args) throws Exception {
    if (args.length < 4) {
      throw new IllegalArgumentException("Usage: bacnetTestId broadcastIp localIp verboseOutput");
    }

    String bacnetTestId = args[0];
    String broadcastIp = args[1];
    String localIp = args[2];
    boolean verboseOutput = Boolean.parseBoolean(args[3]);

    switch (bacnetTestId) {
      case "bacnet_VERSION":
        new VersionTest(localIp, broadcastIp);
        break;
      case "bacnet_PICS":
        new PicsTest(localIp, broadcastIp, verboseOutput);
        break;
      default:
        throw new IllegalArgumentException("Invalid bacnetTestId.");
    }
  }
}
