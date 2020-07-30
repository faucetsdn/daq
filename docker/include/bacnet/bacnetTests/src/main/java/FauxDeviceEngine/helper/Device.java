package FauxDeviceEngine.helper;

import com.serotonin.bacnet4j.LocalDevice;
import com.serotonin.bacnet4j.exception.BACnetServiceException;
import com.serotonin.bacnet4j.obj.BACnetObject;
import com.serotonin.bacnet4j.type.Encodable;
import com.serotonin.bacnet4j.type.enumerated.PropertyIdentifier;

import java.util.Map;

public class Device {
    public void addProperty(BACnetObject bacnetObjectType, PropertyIdentifier propertyIdentifier, Encodable encodable) {
        try {
            bacnetObjectType.setProperty(propertyIdentifier, encodable);
        } catch (BACnetServiceException e) {
            System.err.println("Error adding bacnet property: " + e.getMessage() + propertyIdentifier.toString());
        }
    }

    public void addObjectType(LocalDevice localDevice, BACnetObject bacnetObject, Map<String, String> map) {
        try {
            localDevice.addObject(bacnetObject);
        } catch (BACnetServiceException e) {
            System.err.println("Error adding bacnet object: " + e.getMessage() + " " + map.toString());
        }
    }

    public boolean[] castToArrayBoolean(String string_of_booleans) {
        String[] booleans_arr = string_of_booleans.split(" ");
        boolean[] array = new boolean[booleans_arr.length];
        for (int i = 0; i < booleans_arr.length; i++) {
            array[i] = Boolean.parseBoolean(booleans_arr[i]);
        }
        return array;
    }
}
