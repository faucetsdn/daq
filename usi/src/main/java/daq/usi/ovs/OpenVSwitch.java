package daq.usi.ovs;

import daq.usi.ResponseHandler;
import daq.usi.SwitchController;
import grpc.InterfaceResponse;
import grpc.LinkStatus;
import grpc.POEStatus;
import grpc.POESupport;
import grpc.PowerResponse;
import grpc.SwitchActionResponse;
import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.net.URL;
import java.util.concurrent.TimeUnit;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class OpenVSwitch implements SwitchController {

  private static final String OVS_OUTPUT_FILE = "sec.ofctl";

  protected String getInterfaceByPort(int devicePort) throws IOException {
    URL file = OpenVSwitch.class.getClassLoader().getResource(OVS_OUTPUT_FILE);
    if (file == null) {
      throw new FileNotFoundException(OVS_OUTPUT_FILE + " is not found!");
    }
    FileReader reader = new FileReader(file.getFile());
    try (BufferedReader bufferedReader = new BufferedReader(reader)) {
      Pattern pattern = Pattern.compile("(^\\s*" + devicePort + ")(\\((.+)\\))(:.*)", 'g');
      String interfaceLine = bufferedReader.lines().filter(line -> {
        Matcher m = pattern.matcher(line);
        return m.find();
      }).findFirst().get();
      Matcher m = pattern.matcher(interfaceLine);
      m.matches();
      return m.group(3);
    }
  }

  @Override
  public void getPower(int devicePort, ResponseHandler<PowerResponse> handler) throws Exception {
    PowerResponse.Builder response = PowerResponse.newBuilder();
    PowerResponse power = response.setPoeStatus(POEStatus.State.OFF)
        .setPoeSupport(POESupport.State.DISABLED)
        .build();
    handler.receiveData(power);
  }

  @Override
  public void getInterface(int devicePort, ResponseHandler<InterfaceResponse> handler)
      throws Exception {
    InterfaceResponse.Builder response = InterfaceResponse.newBuilder();
    InterfaceResponse iface =
        response.setLinkStatus(LinkStatus.State.UP).build();
    handler.receiveData(iface);
  }

  private void managePort(int devicePort, ResponseHandler<SwitchActionResponse> handler,
                          boolean enabled)
      throws Exception {
    String iface = getInterfaceByPort(devicePort);
    ProcessBuilder processBuilder = new ProcessBuilder();
    processBuilder.command("bash", "-c", "ifconfig " + iface + (enabled ? " up" : " down"))
        .inheritIO();
    Process process = processBuilder.start();
    boolean exited = process.waitFor(10, TimeUnit.SECONDS);
    int exitCode = process.exitValue();
    handler
        .receiveData(SwitchActionResponse.newBuilder().setSuccess(exited && exitCode == 0).build());
  }

  @Override
  public void connect(int devicePort, ResponseHandler<SwitchActionResponse> handler)
      throws Exception {
    managePort(devicePort, handler, true);
  }

  @Override
  public void disconnect(int devicePort, ResponseHandler<SwitchActionResponse> handler)
      throws Exception {
    managePort(devicePort, handler, false);
  }

  public void start() {
  }
}
