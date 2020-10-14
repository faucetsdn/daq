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
  private final boolean debug;

  /**
   * UsiImpl.
   *
   * @param debug           for verbose output
   */
  public UsiImpl(boolean debug) {
    super();
    switchControllers = new HashMap<>();
    this.debug = debug;
  }

  private SwitchController createController(SwitchInfo switchInfo) {
    SwitchController newController;
    switch (switchInfo.getModel()) {
      case ALLIED_TELESIS_X230: {
        newController = new AlliedTelesisX230(switchInfo.getIpAddr(), switchInfo.getUsername(),
            switchInfo.getPassword(), debug);
        break;
      }
      case CISCO_9300: {
        newController = new Cisco9300(switchInfo.getIpAddr(), switchInfo.getUsername(),
            switchInfo.getPassword(), debug);
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
    System.out.println("Received request in getPower");
    SwitchController sc = getSwitchController(request);
    try {
      sc.getPower(request.getDevicePort(), data -> {
        System.out.println("Sent response in getPower");
        if (debug) {
          System.out.println(data);
        }
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
    System.out.println("Received request in getInterface");
    SwitchController sc = getSwitchController(request);
    try {
      sc.getInterface(request.getDevicePort(), data -> {
        System.out.println("Sent response in getInterface");
        if (debug) {
          System.out.println(data);
        }
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
    System.out.println("Received request in connect");
    SwitchController sc = getSwitchController(request);
    try {
      sc.connect(request.getDevicePort(), data -> {
        System.out.println("Sent response in connect");
        if (debug) {
          System.out.println(data);
        }
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
    System.out.println("Received request in disconnect");
    SwitchController sc = getSwitchController(request);
    try {
      sc.disconnect(request.getDevicePort(), data -> {
        System.out.println("Sent response in disconnect");
        if (debug) {
          System.out.println(data);
        }
        responseObserver.onNext(data);
        responseObserver.onCompleted();
      });
    } catch (Exception e) {
      e.printStackTrace();
      responseObserver.onError(e);
    }
  }
}
