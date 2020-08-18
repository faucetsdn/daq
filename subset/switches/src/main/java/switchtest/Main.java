package switchtest;

import grpc.SwitchInfo;
import grpc.SwitchModel;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;

public class Main {

  /**
   * Switch test runner.
   * @param args args
   */
  public static void main(String[] args) {

    if (args.length < 6) {
      throw new IllegalArgumentException(
          "args: usiUrl rpcTimeoutSec switchIpAddress port supportPOE switchModel"
              + " [username] [password]");
    }

    String usiUrl = args[0];
    int rpcTimeoutSec = Integer.parseInt(args[1]);
    String ipAddress = args[2];

    int interfacePort = Integer.parseInt(args[3]);
    boolean supportsPoe = args[4].equals("true");
    SwitchModel switchModel = SwitchModel.valueOf(args[5]);
    String username = "";
    String password = "";
    if (args.length > 6) {
      username = args[6];
    }
    if (args.length > 7) {
      password = args[7];
    }
    SwitchInfo switchInfo = SwitchInfo.newBuilder()
        .setDevicePort(interfacePort)
        .setIpAddr(ipAddress)
        .setModel(switchModel)
        .setUsername(username)
        .setPassword(password).build();
    ManagedChannel channel = ManagedChannelBuilder.forTarget(usiUrl).usePlaintext().build();
    SwitchTest switchTest = new SwitchTest(channel, rpcTimeoutSec, supportsPoe, false);
    switchTest.test(switchInfo);
  }
}
