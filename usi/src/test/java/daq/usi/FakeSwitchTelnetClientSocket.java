package daq.usi;

public class FakeSwitchTelnetClientSocket extends SwitchTelnetClientSocket {

  public FakeSwitchTelnetClientSocket(
      String remoteIpAddress, int remotePort, BaseSwitchController interrogator, boolean debug) {
    super(remoteIpAddress, remotePort, interrogator, debug);
  }

  @Override
  public void writeData(String data) {
    System.out.println(data);
  }

  @Override
  public void disposeConnection() {
    System.out.println("disposing connection.");
  }
}