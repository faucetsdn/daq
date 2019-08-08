package switchtest;

public class Main {

  public static void main(String[] args) throws Exception {

    if (args.length != 3) {
      throw new IllegalArgumentException("Expected ipAddress && port && supportPOE as arguments");
    }

    String ipAddress = args[0];

    int interfacePort = Integer.parseInt(args[1]);

    boolean supportsPOE = args[2].equals("true");

    SwitchInterrogator switchInterrogator = new SwitchInterrogator(ipAddress, interfacePort, supportsPOE);

    Thread switchInterrogatorThread = new Thread(switchInterrogator);
    switchInterrogatorThread.start();
  }
}