package switchtest;

import grpc.InterfaceResponse;
import grpc.LinkStatus;
import grpc.POENegotiation;
import grpc.POEStatus;
import grpc.POESupport;
import grpc.PowerResponse;
import grpc.SwitchInfo;
import grpc.USIServiceGrpc;
import io.grpc.Channel;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.concurrent.TimeUnit;

public class SwitchTest {

  private final USIServiceGrpc.USIServiceBlockingStub blockingStub;
  protected String reportFilename = "tmp/report.txt";
  protected boolean debug;
  protected boolean deviceConfigPoeEnabled;
  protected int rpcTimeoutSec;

  /**
   * Generic switch test.
   * @param channel GRPC channel
   * @param rpcTimeoutSec Timeout in seconds for rpc calls
   * @param deviceConfigPoeEnabled poe config from module_config
   * @param debug print debug output
   */
  public SwitchTest(Channel channel, int rpcTimeoutSec, boolean deviceConfigPoeEnabled, boolean debug) {
    this.debug = debug;
    blockingStub = USIServiceGrpc.newBlockingStub(channel);
    this.deviceConfigPoeEnabled = deviceConfigPoeEnabled;
    this.rpcTimeoutSec = rpcTimeoutSec;
  }

  protected String testLink(InterfaceResponse interfaceResponse) {
    if (interfaceResponse.getLinkStatus() == LinkStatus.UP) {
      return "RESULT pass connection.port_link Link is up\n";
    }
    return "RESULT fail connection.port_link Link is down\n";
  }

  protected String testSpeed(InterfaceResponse interfaceResponse) {
    int linkSpeed = interfaceResponse.getLinkSpeed();
    if (linkSpeed > 0) {
      if (linkSpeed >= 10) {
        return "RESULT pass connection.port_speed Speed auto-negotiated successfully. "
            + "Speed is greater than 10 MBPS\n";
      } else {
        return "RESULT fail connection.port_speed Speed is too slow. "
            + "Speed is less than or equal to 10 mbps\n";
      }
    }
    return "RESULT fail connection.port_speed Cannot detect current speed\n";
  }

  protected String testDuplex(InterfaceResponse interfaceResponse) {
    String duplex = interfaceResponse.getDuplex();
    if (duplex != null) {
      if (duplex.equals("full")) {
        return "RESULT pass connection.port_duplex Full duplex mode detected\n";
      } else {
        return "RESULT fail connection.port_duplex Incorrect duplex mode set\n";
      }
    }
    return "RESULT fail connection.port_duplex Cannot detect duplex mode\n";
  }

  protected String testPower(PowerResponse powerResponse) {
    String testResults = "";
    if (!deviceConfigPoeEnabled) {
      testResults += "RESULT skip poe.power This test is disabled\n";
      testResults += "RESULT skip poe.negotiation This test is disabled\n";
      testResults += "RESULT skip poe.support This test is disabled\n";
      return testResults;
    }

    POEStatus poeStatus = powerResponse.getPoeStatus();
    // Determine PoE power test result
    if (poeStatus == POEStatus.ON) {
      if (powerResponse.getMaxPowerConsumption() >= powerResponse.getCurrentPowerConsumption()) {
        testResults += "RESULT pass poe.power PoE is applied to device\n";
      } else {
        testResults += "RESULT fail poe.power device wattage exceeds the max wattage.\n";
      }
    } else if (poeStatus == POEStatus.OFF) {
      testResults += "RESULT fail poe.power No poE is applied\n";
    } else if (poeStatus == POEStatus.FAULT) {
      testResults += "RESULT fail poe.power Device detection "
          + "or a powered device is in a faulty state\n";
    } else {
      testResults += "RESULT fail poe.power A powered device is detected, "
          + "but no PoE is available, or the maximum wattage exceeds the "
          + "detected powered-device maximum.\n";
    }

    // Determine PoE auto negotiation result
    if (powerResponse.getPoeNegotiation() == POENegotiation.NEGOTIATION_ENABLED) {
      testResults += "RESULT pass poe.negotiation PoE auto-negotiated successfully\n";
    } else {
      testResults += "RESULT fail poe.negotiation Incorrect privilege for negotiation\n";
    }

    // Determine PoE support result
    if (powerResponse.getPoeSupport() == POESupport.ENABLED) {
      testResults += "RESULT pass poe.support PoE supported and enabled\n";
    } else {
      testResults +=
          "RESULT fail poe.support The switch does not support PoE or it is disabled\n";
    }

    return testResults;
  }

  protected void writeReport(String loginReport) {
    try {
      if (debug) {
        System.out.println("report:" + loginReport);
      }

      String[] directory = reportFilename.split("/");

      File dir = new File(directory[directory.length - 2]);
      if (!dir.exists()) {
        dir.mkdirs();
      }

      BufferedWriter writer = new BufferedWriter(new FileWriter(reportFilename));
      writer.write(loginReport);
      writer.close();
    } catch (IOException e) {
      System.err.println("Exception when writing report:" + e.getMessage());
    }
  }

  /**
   * Run a switch test with the specified switch info.
   * @param switchInfo SwitchInfo from the USI proto file
   */
  public void test(SwitchInfo switchInfo) {
    PowerResponse powerResponse = blockingStub.withDeadlineAfter(rpcTimeoutSec, TimeUnit.SECONDS).getPower(switchInfo);
    InterfaceResponse interfaceResponse = blockingStub.withDeadlineAfter(rpcTimeoutSec, TimeUnit.SECONDS).getInterface(switchInfo);
    String report = testLink(interfaceResponse)
        + testSpeed(interfaceResponse)
        + testDuplex(interfaceResponse)
        + testPower(powerResponse);
    writeReport(report);
  }
}
