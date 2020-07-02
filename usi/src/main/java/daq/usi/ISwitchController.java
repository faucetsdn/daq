package daq.usi;

import grpc.Interface;
import grpc.Power;
import grpc.SwitchActionResponse;

public interface ISwitchController {

  void getPower(int devicePort, ResponseHandler<Power> handler) throws Exception;

  void getInterface(int devicePort, ResponseHandler<Interface> handler)
      throws Exception;

  void connect(int devicePort, ResponseHandler<SwitchActionResponse> handler)
      throws Exception;

  void disconnect(int devicePort, ResponseHandler<SwitchActionResponse> handler)
      throws Exception;
}
