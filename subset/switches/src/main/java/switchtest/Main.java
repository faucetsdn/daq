package switchtest;

public class Main {

  public static void main(String[] args) throws Exception {

    if (args.length != 1) {
      throw new IllegalArgumentException("Expected ipAddress && port as argument");
    }

    String ipAddress = args[0];

    int interfacePort = Integer.parseInt(args[1]);

    SwitchInterrogator switchInterrogator = new SwitchInterrogator(ipAddress, interfacePort);

    Thread switchInterrogatorThread = new Thread(switchInterrogator);
    switchInterrogatorThread.start();
  }
}

