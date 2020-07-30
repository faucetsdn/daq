package helper;

import com.google.common.collect.ArrayListMultimap;
import com.google.common.collect.Multimap;
import com.serotonin.bacnet4j.LocalDevice;
import com.serotonin.bacnet4j.RemoteDevice;
import com.serotonin.bacnet4j.exception.BACnetException;
import com.serotonin.bacnet4j.type.constructed.ObjectPropertyReference;
import com.serotonin.bacnet4j.type.constructed.SequenceOf;
import com.serotonin.bacnet4j.type.enumerated.ObjectType;
import com.serotonin.bacnet4j.type.enumerated.PropertyIdentifier;
import com.serotonin.bacnet4j.type.primitive.ObjectIdentifier;
import com.serotonin.bacnet4j.util.PropertyReferences;
import com.serotonin.bacnet4j.util.PropertyValues;
import com.serotonin.bacnet4j.util.RequestUtils;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class BacnetPoints {

  private Multimap<String, Map<String, String>> bacnetPointsMap = ArrayListMultimap.create();
  String propertyErrorMessage = "errorClass=Property, errorCode=Unknown property";

  public void get(LocalDevice localDevice) throws BACnetException {

    for (RemoteDevice remoteDevice : localDevice.getRemoteDevices()) {
      RequestUtils.getExtendedDeviceInformation(localDevice, remoteDevice);
      @SuppressWarnings("unchecked")
      List<ObjectIdentifier> allObjectsIdentifier =
              ((SequenceOf<ObjectIdentifier>)
                      RequestUtils.sendReadPropertyAllowNull(
                              localDevice,
                              remoteDevice,
                              remoteDevice.getObjectIdentifier(),
                              PropertyIdentifier.objectList))
                      .getValues();

      for (ObjectIdentifier objectIdentifier : allObjectsIdentifier) {
        try {
          PropertyReferences refs = new PropertyReferences();
          refs.add(objectIdentifier, PropertyIdentifier.all);
          PropertyValues propertyValues =
                  RequestUtils.readProperties(localDevice, remoteDevice, refs, null);

          for (ObjectPropertyReference objectPropertyReference : propertyValues) {
            if (!propertyValues
                    .getNoErrorCheck(objectPropertyReference)
                    .toString()
                    .equals(propertyErrorMessage)) {
              String bacnetObjectType = objectPropertyReference.getObjectIdentifier().toString();
              String bacnetObjectProperty =
                      objectPropertyReference.getPropertyIdentifier().toString();
              String bacnetPropertyValue =
                      propertyValues.getNoErrorCheck(objectPropertyReference).toString();
              Map<String, String> properties = new HashMap<>();
              properties.put(bacnetObjectProperty, bacnetPropertyValue);
            bacnetPointsMap.put(bacnetObjectType, properties);
            }
          }
        } catch (Exception e) {
          System.out.println("Error "+ objectIdentifier + " "  + e.getMessage() + "\n");

        }
      }
    }
  }

  public Multimap<String, Map<String, String>> getBacnetPointsMap() {
    return bacnetPointsMap;
  }
}
