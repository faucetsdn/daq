public class Main {
  public static void main(String[] args) {

    if (args.length != 5) {
      throw new IllegalArgumentException(
          "Usage: target_ip protocol(http(s)/ssh/telnet) target_port target_mac domain");
    }

    String host = args[0];
    String protocol = args[1];
    String port = args[2];
    String macAddress = args[3];
    String domain = args[4];

    SetupTest setupTest = new SetupTest(protocol, host, port, macAddress, domain);
  }
}
