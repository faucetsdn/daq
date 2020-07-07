package daq.usi;

import grpc.InterfaceResponse;
import grpc.PowerResponse;
import grpc.SwitchActionResponse;

public interface SwitchController {

  void getPower(int devicePort, ResponseHandler<PowerResponse> handler) throws Exception;

  void getInterface(int devicePort, ResponseHandler<InterfaceResponse> handler)
      throws Exception;

  void connect(int devicePort, ResponseHandler<SwitchActionResponse> handler)
      throws Exception;

  void disconnect(int devicePort, ResponseHandler<SwitchActionResponse> handler)
      throws Exception;

  void start();
}
