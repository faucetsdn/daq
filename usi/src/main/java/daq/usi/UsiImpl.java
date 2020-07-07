package daq.usi;

import daq.usi.allied.AlliedTelesisX230;
import daq.usi.cisco.Cisco9300;
import grpc.Interface;
import grpc.Power;
import grpc.SwitchActionResponse;
import grpc.SwitchInfo;
import grpc.USIServiceGrpc;
import io.grpc.stub.StreamObserver;
import java.util.HashMap;
import java.util.Map;

public class UsiImpl extends USIServiceGrpc.USIServiceImplBase {
  private Map<String, SwitchController> switchControllers;

  public UsiImpl() {
    super();
    switchControllers = new HashMap<>();
  }

  private SwitchController getSwitchController(SwitchInfo switchInfo) {
    String repr = String.join(",", switchInfo.getModel().toString(), switchInfo.getIpAddr(),
        String.valueOf(switchInfo.getTelnetPort()), switchInfo.getUsername(),
        switchInfo.getPassword());
    SwitchController sc = switchControllers.get(repr);
    if (sc == null) {
      switch (switchInfo.getModel()) {
        case ALLIED_TELESIS_X230: {
          sc = new AlliedTelesisX230(switchInfo.getIpAddr(), switchInfo.getTelnetPort(),
              switchInfo.getUsername(), switchInfo.getPassword());
          break;
        }
        case CISCO_9300: {
          sc = new Cisco9300(switchInfo.getIpAddr(), switchInfo.getTelnetPort(),
              switchInfo.getUsername(), switchInfo.getPassword());
          break;
        }
        default:
          break;
      }
      new Thread(sc).start();
      switchControllers.put(repr, sc);
    }
    return sc;
  }

  @Override
  public void getPower(SwitchInfo request, StreamObserver<Power> responseObserver) {
    SwitchController sc = getSwitchController(request);
    try {
      sc.getPower(request.getDevicePort(), responseObserver::onNext);
    } catch (Exception e) {
      e.printStackTrace();
      responseObserver.onError(e);
    }
  }

  @Override
  public void getInterface(SwitchInfo request, StreamObserver<Interface> responseObserver) {
    SwitchController sc = getSwitchController(request);
    try {
      sc.getInterface(request.getDevicePort(), responseObserver::onNext);
    } catch (Exception e) {
      e.printStackTrace();
      responseObserver.onError(e);
    }
  }

  @Override
  public void connect(SwitchInfo request, StreamObserver<SwitchActionResponse> responseObserver) {
    SwitchController sc = getSwitchController(request);
    try {
      sc.connect(request.getDevicePort(), responseObserver::onNext);
    } catch (Exception e) {
      e.printStackTrace();
      responseObserver.onError(e);
    }
  }

  @Override
  public void disconnect(SwitchInfo request,
                         StreamObserver<SwitchActionResponse> responseObserver) {
    SwitchController sc = getSwitchController(request);
    try {
      sc.disconnect(request.getDevicePort(), responseObserver::onNext);
    } catch (Exception e) {
      e.printStackTrace();
      responseObserver.onError(e);
    }
  }
}