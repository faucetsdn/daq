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
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

public class SwitchTest {

  enum Result {
    PASS,
    FAIL,
    SKIP
  }

  private final USIServiceGrpc.USIServiceBlockingStub blockingStub;
  protected String reportFilename = "tmp/report.txt";
  protected boolean debug;
  protected boolean deviceConfigPoeEnabled;
  protected int rpcTimeoutSec;
  protected List<String> results = new ArrayList<>();
  /**
   * Generic switch test.
   * @param channel GRPC channel
   * @param rpcTimeoutSec Timeout in seconds for rpc calls
   * @param deviceConfigPoeEnabled poe config from module_config
   * @param debug print debug output
   */

  public SwitchTest(Channel channel, int rpcTimeoutSec, boolean deviceConfigPoeEnabled,
                    boolean debug) {
    this.debug = debug;
    blockingStub = USIServiceGrpc.newBlockingStub(channel);
    this.deviceConfigPoeEnabled = deviceConfigPoeEnabled;
    this.rpcTimeoutSec = rpcTimeoutSec;
  }

  protected void captureResult(String test, Result result, String additional) {
    results.add("RESULT " + result.name().toLowerCase() + " " + test + " " + additional);
  }

  protected void testLink(InterfaceResponse interfaceResponse) {
    final String testName = "connection.switch.port_link";
    if (interfaceResponse.getLinkStatus() == LinkStatus.State.UP) {
      captureResult(testName, Result.PASS, "Link is up");
    } else {
      captureResult(testName, Result.FAIL, "Link is down");
    }
  }

  protected void testSpeed(InterfaceResponse interfaceResponse) {
    final String testName = "connection.switch.port_speed";
    int linkSpeed = interfaceResponse.getLinkSpeed();
    if (linkSpeed > 0) {
      if (linkSpeed >= 10) {
        captureResult(testName, Result.PASS,
            "Speed auto-negotiated successfully. Speed is greater than 10 MBPS");
      } else {
        captureResult(testName, Result.FAIL,
            "Speed is too slow. Speed is less than or equal to 10 mbps");
      }
    } else {
      captureResult(testName, Result.FAIL, "Cannot detect current speed");
    }
  }

  protected void testDuplex(InterfaceResponse interfaceResponse) {
    final String testName = "connection.switch.port_duplex";
    String duplex = interfaceResponse.getDuplex();
    if (duplex != null) {
      if (duplex.equals("full")) {
        captureResult(testName, Result.PASS, "Full duplex mode detected");
      } else {
        captureResult(testName, Result.FAIL, "Incorrect duplex mode set");
      }
    } else {
      captureResult(testName, Result.FAIL, " Cannot detect duplex mode");
    }
  }

  protected void testPower(PowerResponse powerResponse) {
    if (!deviceConfigPoeEnabled) {
      captureResult("poe.switch.power", Result.SKIP, "This test is disabled");
      return;
    }

    POEStatus.State poeStatus = powerResponse.getPoeStatus();
    // Determine PoE power test result
    if (poeStatus == POEStatus.State.ON) {
      if (powerResponse.getMaxPowerConsumption() >= powerResponse.getCurrentPowerConsumption()) {
        captureResult("poe.switch.power", Result.PASS, "PoE is applied to device");
      } else {
        captureResult("poe.switch.power", Result.FAIL, "device wattage exceeds the max wattage");
      }
    } else if (poeStatus == POEStatus.State.OFF) {
      captureResult("poe.switch.power", Result.FAIL, "No PoE is applied");
    } else if (poeStatus == POEStatus.State.FAULT) {
      captureResult("poe.switch.power", Result.FAIL,
          "Device detection or a powered device is in a faulty state");
    } else {
      captureResult("poe.switch.power", Result.FAIL, "A powered device is detected, "
          + "but no PoE is available, or the maximum wattage exceeds the "
          + "detected powered-device maximum.");
    }
  }

  protected void writeReport() {
    try {
      String report = String.join("\n", results);
      if (debug) {
        System.out.println("report:" + report);
      }

      String[] directory = reportFilename.split("/");

      File dir = new File(directory[directory.length - 2]);
      dir.mkdirs();

      BufferedWriter writer = new BufferedWriter(new FileWriter(reportFilename));
      writer.write(report);
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
    final PowerResponse powerResponse = blockingStub
        .withDeadlineAfter(rpcTimeoutSec, TimeUnit.SECONDS).getPower(switchInfo);
    final InterfaceResponse interfaceResponse = blockingStub
        .withDeadlineAfter(rpcTimeoutSec, TimeUnit.SECONDS).getInterface(switchInfo);
    results.add(interfaceResponse.getRawOutput());
    results.add(powerResponse.getRawOutput());
    testLink(interfaceResponse);
    testSpeed(interfaceResponse);
    testDuplex(interfaceResponse);
    testPower(powerResponse);
    writeReport();
  }
}

