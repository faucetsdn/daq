package daq.usi.ovs;

import daq.usi.ResponseHandler;
import daq.usi.SwitchController;
import grpc.InterfaceResponse;
import grpc.LinkStatus;
import grpc.POEStatus;
import grpc.POESupport;
import grpc.PowerResponse;
import grpc.SwitchActionResponse;

public class OpenVSwitch implements SwitchController {
  private final String fauxInterface;

  public OpenVSwitch(String fauxInterface) {
    this.fauxInterface = fauxInterface;
  }

  @Override
  public void getPower(int devicePort, ResponseHandler<PowerResponse> handler) throws Exception {
    PowerResponse.Builder response = PowerResponse.newBuilder();
    PowerResponse power = response.setPoeStatus(POEStatus.OFF)
        .setPoeSupport(POESupport.DISABLED)
        .setMaxPowerConsumption(0)
        .setCurrentPowerConsumption(0).build();
    handler.receiveData(power);
  }

  @Override
  public void getInterface(int devicePort, ResponseHandler<InterfaceResponse> handler)
      throws Exception {
    InterfaceResponse.Builder response = InterfaceResponse.newBuilder();
    InterfaceResponse iface = response.setLinkStatus(LinkStatus.UP)
        .setDuplex("")
        .setLinkSpeed(0)
        .build();
    handler.receiveData(iface);
  }

  private void managePort(int devicePort, ResponseHandler<SwitchActionResponse> handler,
                          boolean enabled) throws Exception {
    ProcessBuilder processBuilder = new ProcessBuilder();
    processBuilder.command("bash", "-c", "ifconfig " + fauxInterface + (enabled ? " up" : " down"));
    Process process = processBuilder.start();
    int exitCode = process.waitFor();
    handler.receiveData(SwitchActionResponse.newBuilder().setSuccess(exitCode == 0).build());
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
}
