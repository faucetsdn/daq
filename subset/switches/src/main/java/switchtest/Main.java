package switchtest;

import switchtest.allied.AlliedTelesisX230;
import switchtest.cisco.Cisco9300;

public class Main {

  public static void main(String[] args) throws Exception {

    if (args.length < 4) {
      throw new IllegalArgumentException(
          "Expected ipAddress && port && supportPOE && switchModel as arguments");
    }

    String ipAddress = args[0];

    int interfacePort = Integer.parseInt(args[1]);

    boolean supportsPOE = args[2].equals("true");

    SupportedSwitchModelsEnum switchModel = null;
    try {
      switchModel = SupportedSwitchModelsEnum.valueOf(args[3]);
    } catch (Exception e) {
      System.out.println("Unknown Switch Model: " + args[3]);
      throw e;
    }

    String user = null;
    if (args.length >= 5) {
      user = args[4];
    }
    String password = null;
    if (args.length >= 6) {
      password = args[5];
    }

    SwitchInterrogator switchInterrogator = null;
    switch (switchModel) {
      case CISCO_9300:
        switchInterrogator = new Cisco9300(ipAddress, interfacePort, supportsPOE, user, password);
        break;
      case ALLIED_TELESIS_X230:
        switchInterrogator =
            new AlliedTelesisX230(ipAddress, interfacePort, supportsPOE, user, password);
    }
    Thread switchInterrogatorThread = new Thread(switchInterrogator);
    switchInterrogatorThread.start();
  }
}
