package helper;

import com.serotonin.bacnet4j.LocalDevice;
import com.serotonin.bacnet4j.RemoteDevice;
import com.serotonin.bacnet4j.RemoteObject;
import com.serotonin.bacnet4j.event.DeviceEventListener;
import com.serotonin.bacnet4j.exception.BACnetServiceException;
import com.serotonin.bacnet4j.npdu.ip.IpNetwork;
import com.serotonin.bacnet4j.obj.BACnetObject;
import com.serotonin.bacnet4j.service.confirmed.ReinitializeDeviceRequest.ReinitializedStateOfDevice;
import com.serotonin.bacnet4j.transport.Transport;
import com.serotonin.bacnet4j.type.Encodable;
import com.serotonin.bacnet4j.type.constructed.Choice;
import com.serotonin.bacnet4j.type.constructed.DateTime;
import com.serotonin.bacnet4j.type.constructed.PropertyValue;
import com.serotonin.bacnet4j.type.constructed.SequenceOf;
import com.serotonin.bacnet4j.type.constructed.TimeStamp;
import com.serotonin.bacnet4j.type.enumerated.EventState;
import com.serotonin.bacnet4j.type.enumerated.EventType;
import com.serotonin.bacnet4j.type.enumerated.MessagePriority;
import com.serotonin.bacnet4j.type.enumerated.NotifyType;
import com.serotonin.bacnet4j.type.notificationParameters.NotificationParameters;
import com.serotonin.bacnet4j.type.primitive.Boolean;
import com.serotonin.bacnet4j.type.primitive.CharacterString;
import com.serotonin.bacnet4j.type.primitive.ObjectIdentifier;
import com.serotonin.bacnet4j.type.primitive.UnsignedInteger;

public class Connection {

  private LocalDevice localDevice;
  private IpNetwork network;
  private boolean terminate;

  private final int deviceId = (int) Math.floor(Math.random() * 1000.0);

  public Connection(String broadcastAddress, int port) throws BACnetServiceException, Exception {
    this(broadcastAddress, port, IpNetwork.DEFAULT_BIND_IP);
  }

  public Connection(String broadcastAddress, int port, String localAddress)
      throws BACnetServiceException, Exception {
    network = new IpNetwork(broadcastAddress, port, IpNetwork.DEFAULT_BIND_IP, 0, localAddress);
    System.out.println("Creating LoopDevice id " + deviceId);
    Transport transport = new Transport(network);
    transport.setTimeout(1000);
    localDevice = new LocalDevice(deviceId, transport);

    try {
      localDevice
          .getEventHandler()
          .addListener(
              new DeviceEventListener() {

                @Override
                public void listenerException(Throwable e) {
                  System.out.println("loopDevice listenerException");
                }

                @Override
                public void iAmReceived(RemoteDevice d) {
                  System.out.println("loopDevice iAmReceived");
                }

                @Override
                public boolean allowPropertyWrite(BACnetObject obj, PropertyValue pv) {
                  System.out.println("loopDevice allowPropertyWrite");
                  return true;
                }

                @Override
                public void propertyWritten(BACnetObject obj, PropertyValue pv) {
                  System.out.println("loopDevice propertyWritten");
                }

                @Override
                public void iHaveReceived(RemoteDevice d, RemoteObject o) {
                  System.out.println("loopDevice iHaveReceived");
                }

                @Override
                public void covNotificationReceived(
                    UnsignedInteger subscriberProcessIdentifier,
                    RemoteDevice initiatingDevice,
                    ObjectIdentifier monitoredObjectIdentifier,
                    UnsignedInteger timeRemaining,
                    SequenceOf<PropertyValue> listOfValues) {
                  System.out.println("loopDevice covNotificationReceived");
                }

                @Override
                public void eventNotificationReceived(
                    UnsignedInteger processIdentifier,
                    RemoteDevice initiatingDevice,
                    ObjectIdentifier eventObjectIdentifier,
                    TimeStamp timeStamp,
                    UnsignedInteger notificationClass,
                    UnsignedInteger priority,
                    EventType eventType,
                    CharacterString messageText,
                    NotifyType notifyType,
                    Boolean ackRequired,
                    EventState fromState,
                    EventState toState,
                    NotificationParameters eventValues) {
                  System.out.println("loopDevice eventNotificationReceived");
                }

                @Override
                public void textMessageReceived(
                    RemoteDevice textMessageSourceDevice,
                    Choice messageClass,
                    MessagePriority messagePriority,
                    CharacterString message) {
                  System.out.println("loopDevice textMessageReceived");
                }

                @Override
                public void privateTransferReceived(
                    UnsignedInteger vendorId,
                    UnsignedInteger serviceNumber,
                    Encodable serviceParameters) {
                  System.out.println("loopDevice privateTransferReceived");
                }

                @Override
                public void reinitializeDevice(
                    ReinitializedStateOfDevice reinitializedStateOfDevice) {
                  System.out.println("loopDevice reinitializeDevice");
                }

                @Override
                public void synchronizeTime(DateTime dateTime, boolean utc) {
                  System.out.println("loopDevice synchronizeTime");
                }
              });
      localDevice.initialize();
    } catch (RuntimeException e) {
      System.out.println("Error: " + e.getMessage());
      localDevice.terminate();
      localDevice = null;
      throw e;
    }
  }

  /** @return the terminate */
  public boolean isTerminate() {
    return terminate;
  }

  /** @param terminate the terminate to set */
  public void doTerminate() {
    terminate = true;
    localDevice.terminate();
    synchronized (this) {
      notifyAll();
    }
  }

  /** @return the localDevice */
  public LocalDevice getLocalDevice() {
    return localDevice;
  }
}
