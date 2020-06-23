package switchtest;

import grpc.*;
import io.grpc.stub.StreamObserver;
import switchtest.allied.AlliedTelesisX230;
import switchtest.cisco.Cisco9300;

import java.util.HashMap;
import java.util.Map;

public class USIImpl extends USIServiceGrpc.USIServiceImplBase {
  private Map<String, SwitchController> switchControllers;

  public USIImpl() {
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
      }
      new Thread(sc).start();
    }
    return sc;
  }

  @Override
  public void getPower(SwitchInfo request, StreamObserver<Power> responseObserver) {
    SwitchController sc = getSwitchController(request);
    try {
      sc.getPower(request.getDevicePort(), power -> {
        responseObserver.onNext(power);
      });
    } catch (Exception e) {
      e.printStackTrace();
      responseObserver.onError(e);
    }
  }

  @Override
  public void getInterface(SwitchInfo request, StreamObserver<Interface> responseObserver) {
    SwitchController sc = getSwitchController(request);
    try {
      sc.getInterface(request.getDevicePort(), iface -> {
        responseObserver.onNext(iface);
      });
    } catch (Exception e) {
      e.printStackTrace();
      responseObserver.onError(e);
    }
  }

  @Override
  public void connect(SwitchInfo request, StreamObserver<SwitchActionResponse> responseObserver) {
    SwitchController sc = getSwitchController(request);
    try {
      sc.connect(request.getDevicePort(), response -> {
        responseObserver.onNext(response);
      });
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
      sc.disconnect(request.getDevicePort(), response -> {
        responseObserver.onNext(response);
      });
    } catch (Exception e) {
      e.printStackTrace();
      responseObserver.onError(e);
    }
  }
}