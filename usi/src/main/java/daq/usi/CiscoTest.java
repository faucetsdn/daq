package daq.usi;

import daq.usi.allied.AlliedTelesisX230;
import daq.usi.cisco.Cisco9300;

public class CiscoTest {
  public static void main(String[] args) throws Exception {
    // TODO Change me!
    BaseSwitchController cs = new AlliedTelesisX230("192.168.1.1","manager", "friend", true);
    cs.start();
    Thread.sleep(6000);
    System.out.println("authorized " + cs.userAuthorised + " enabled: " + cs.userEnabled);
    cs.getPower(1, data -> {
      System.out.println("power consumption: " + data.getCurrentPowerConsumption());
      System.out.println("Max power: " + data.getMaxPowerConsumption());
      System.out.println("Poe status: " + data.getPoeStatus());
      System.out.println("Poe support: " + data.getPoeSupport());
      cs.getInterface(1, iface -> {
        System.out.println("Link status: " + iface.getLinkStatus());
        System.out.println("Link speed: " + iface.getLinkSpeed());
        System.out.println("Link Duplex: " + iface.getDuplex());
        cs.disconnect(1, res -> {
          System.out.println("Disconnect success? " + res.getSuccess());
          Thread.sleep(5000);
          cs.connect(1, res2 -> {
            System.out.println("connect success? " + res2.getSuccess());
          });
        });
      });
    });
    while (true) {
      Thread.sleep(1000);
    }
  }
}
