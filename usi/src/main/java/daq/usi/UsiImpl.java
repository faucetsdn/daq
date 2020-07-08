package daq.usi;

import daq.usi.allied.AlliedTelesisX230;
import daq.usi.cisco.Cisco9300;
import daq.usi.ovs.OpenVSwitch;
import grpc.InterfaceResponse;
import grpc.PowerResponse;
import grpc.SwitchActionResponse;
import grpc.SwitchInfo;
import grpc.USIServiceGrpc;
import io.grpc.stub.StreamObserver;
import java.util.HashMap;
import java.util.Map;

public class UsiImpl extends USIServiceGrpc.USIServiceImplBase {
  private final Map<String, SwitchController> switchControllers;

  public UsiImpl() {
    super();
    switchControllers = new HashMap<>();
  }

  private SwitchController createController(SwitchInfo switchInfo) {
    SwitchController newController;
    switch (switchInfo.getModel()) {
      case ALLIED_TELESIS_X230: {
        newController = new AlliedTelesisX230(switchInfo.getIpAddr(), switchInfo.getUsername(),
            switchInfo.getPassword());
        break;
      }
      case CISCO_9300: {
        newController = new Cisco9300(switchInfo.getIpAddr(), switchInfo.getUsername(),
            switchInfo.getPassword());
        break;
      }
      case OVS_SWITCH: {
        newController = new OpenVSwitch();
        break;
      }
      default:
        throw new IllegalArgumentException("Unrecognized switch model " + switchInfo.getModel());
    }
    newController.start();
    return newController;
  }

  private SwitchController getSwitchController(SwitchInfo switchInfo) {
    String repr = String.join(",", switchInfo.getModel().toString(), switchInfo.getIpAddr(),
        switchInfo.getUsername(),
        switchInfo.getPassword());
    return switchControllers.computeIfAbsent(repr, key -> createController(switchInfo));
  }

  @Override
  public void getPower(SwitchInfo request, StreamObserver<PowerResponse> responseObserver) {
    SwitchController sc = getSwitchController(request);
    try {
      sc.getPower(request.getDevicePort(), data -> {
        responseObserver.onNext(data);
        responseObserver.onCompleted();
      });
    } catch (Exception e) {
      e.printStackTrace();
      responseObserver.onError(e);
    }
  }

  @Override
  public void getInterface(SwitchInfo request, StreamObserver<InterfaceResponse> responseObserver) {
    SwitchController sc = getSwitchController(request);
    try {
      sc.getInterface(request.getDevicePort(), data -> {
        responseObserver.onNext(data);
        responseObserver.onCompleted();
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
      sc.connect(request.getDevicePort(), data -> {
        responseObserver.onNext(data);
        responseObserver.onCompleted();
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
      sc.disconnect(request.getDevicePort(), data -> {
        responseObserver.onNext(data);
        responseObserver.onCompleted();
      });
    } catch (Exception e) {
      e.printStackTrace();
      responseObserver.onError(e);
    }
  }
}
