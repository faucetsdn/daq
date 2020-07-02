package daq.usi.ovs;

import daq.usi.ISwitchController;
import daq.usi.ResponseHandler;
import grpc.Interface;
import grpc.LinkStatus;
import grpc.POEStatus;
import grpc.POESupport;
import grpc.Power;
import grpc.SwitchActionResponse;

public class OpenVSwitch implements ISwitchController {
  private String fauxIface;

  public OpenVSwitch(String fauxIface) {
    this.fauxIface = fauxIface;
  }

  @Override
  public void getPower(int devicePort, ResponseHandler<Power> handler) throws Exception {
    Power.Builder response = Power.newBuilder();
    Power power = response.setPoeStatus(POEStatus.OFF)
        .setPoeSupport(POESupport.DISABLED)
        .setMaxPowerConsumption(0)
        .setCurrentPowerConsumption(0).build();
    handler.receiveData(power);
  }

  @Override
  public void getInterface(int devicePort, ResponseHandler<Interface> handler) throws Exception {
    Interface.Builder response = Interface.newBuilder();
    Interface iface = response.setLinkStatus(LinkStatus.UP)
        .setDuplex("")
        .setLinkSpeed(0)
        .build();
    handler.receiveData(iface);
  }

  private void managePort(int devicePort, ResponseHandler<SwitchActionResponse> handler,
                          boolean enabled) throws Exception {
    ProcessBuilder processBuilder = new ProcessBuilder();
    processBuilder.command("bash", "-c", "ifconfig " + fauxIface + (enabled ? " up" : " down"));
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
