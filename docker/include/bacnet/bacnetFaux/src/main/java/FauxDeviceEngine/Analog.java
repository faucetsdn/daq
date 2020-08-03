package FauxDeviceEngine;

import FauxDeviceEngine.helper.Device;
import com.serotonin.bacnet4j.LocalDevice;
import com.serotonin.bacnet4j.exception.BACnetServiceException;
import com.serotonin.bacnet4j.obj.BACnetObject;
import com.serotonin.bacnet4j.type.Encodable;
import com.serotonin.bacnet4j.type.constructed.*;
import com.serotonin.bacnet4j.type.enumerated.*;
import com.serotonin.bacnet4j.type.primitive.CharacterString;
import com.serotonin.bacnet4j.type.primitive.Real;
import com.serotonin.bacnet4j.type.primitive.UnsignedInteger;

import java.util.Map;

public class Analog {

    private float presentValue = 0.0f;
    private String objectName = "";
    private String deviceType = "";
    private float deadband = 0.0f;
    private boolean outOfService = false;
    private float resolution = 0.0f;
    private boolean[] eventEnable = new boolean[3];
    private int eventState = 0;
    private int objectType = 0;
    private int timeDelayNormal = 0;
    private float lowLimit = 0;
    private boolean[] limitEnable = new boolean[2];
    private float covIncrement = 0.0f;
    private boolean[] statusFlags = new boolean[4];
    private int updateInterval = 0;
    private boolean[] ackedTransitions = new boolean[3];
    private float highLimit = 0;
    private int notifyType = 0;
    private boolean eventDetectionEnable = false;
    private float minPresValue = 0.0f;
    private float maxPresValue = 0.0f;
    private int reliability = 0;
    private SequenceOf<EventTransitionBits> eventTransitionBits = new SequenceOf<EventTransitionBits>();
    private int notificationClass = 0;
    private String description = "";
    private boolean eventAlgorithmInhibit = false;
    private int units = 0;
    private String profileName = "";
    private float relinquishDefault = 0.0f;
    private boolean priorityArray = false;
    Device device = new Device();

    public Analog(LocalDevice localDevice, BACnetObject bacnetObjectType, Map<String, String>bacnetObjectMap) {
        for(Map.Entry<String, String> map : bacnetObjectMap.entrySet()) {
            String propertyName = map.getKey();
            String propertyValue = map.getValue();
            addObjectProperty(bacnetObjectType, propertyName, propertyValue);
        }
        device.addObjectType(localDevice, bacnetObjectType, bacnetObjectMap);
    }

    private void addObjectProperty(BACnetObject bacnetObjectType, String objectProperty, String propertyValue) {
        Encodable encodable;
        switch (objectProperty) {
            case "Present_Value":
                presentValue = Float.parseFloat(propertyValue);
                encodable = new Real(presentValue);
                device.addProperty(bacnetObjectType, PropertyIdentifier.presentValue, encodable);
                break;
            case "Object_Name":
                objectName = propertyValue;
                encodable = new CharacterString(objectName);
                device.addProperty(bacnetObjectType, PropertyIdentifier.objectName, encodable);
                break;
            case "Device_Type":
                deviceType = propertyValue;
                encodable = new CharacterString(deviceType);
                device.addProperty(bacnetObjectType, PropertyIdentifier.deviceType, encodable);
                break;
            case "Deadband":
                deadband = Float.parseFloat(propertyValue);
                encodable = new Real(deadband);
                device.addProperty(bacnetObjectType, PropertyIdentifier.deadband, encodable);
                break;
            case "Out_Of_Service":
                outOfService = Boolean.valueOf(propertyValue);
                encodable = new com.serotonin.bacnet4j.type.primitive.Boolean(outOfService);
                device.addProperty(bacnetObjectType, PropertyIdentifier.outOfService, encodable);
                break;
            case "Resolution" :
                resolution = Float.parseFloat(propertyValue);
                encodable = new Real(resolution);
                device.addProperty(bacnetObjectType, PropertyIdentifier.resolution, encodable);
                break;
            case "Event_Enable":
                eventEnable = device.castToArrayBoolean(propertyValue);
                encodable = new EventTransitionBits(eventEnable[0], eventEnable[1], eventEnable[2]);
                device.addProperty(bacnetObjectType, PropertyIdentifier.eventEnable, encodable);
                break;
            case "Event_State":
                eventState = Integer.parseInt(propertyValue);
                encodable = new EventState(eventState);
                device.addProperty(bacnetObjectType, PropertyIdentifier.eventState, encodable);
                break;
            case "Object_Type":
                objectType = Integer.parseInt(propertyValue);
                encodable = new ObjectType(objectType);
                device.addProperty(bacnetObjectType, PropertyIdentifier.objectType, encodable);
                break;
            case "Time_Delay_Normal":
                timeDelayNormal = Integer.parseInt(propertyValue);
                encodable = new UnsignedInteger(timeDelayNormal);
                device.addProperty(bacnetObjectType, PropertyIdentifier.timeDelayNormal, encodable);
                break;
            case "Low_Limit":
                lowLimit = Float.parseFloat(propertyValue);
                encodable = new Real(lowLimit);
                device.addProperty(bacnetObjectType, PropertyIdentifier.lowLimit, encodable);
                break;
            case "Limit_Enable":
                limitEnable = device.castToArrayBoolean(propertyValue);
                encodable = new LimitEnable(limitEnable[0], limitEnable[1]);
                device.addProperty(bacnetObjectType, PropertyIdentifier.limitEnable, encodable);
                break;
            case "Cov_Increment":
                covIncrement = Float.parseFloat(propertyValue);
                encodable = new Real(covIncrement);
                device.addProperty(bacnetObjectType, PropertyIdentifier.covIncrement, encodable);
                break;
            case "Status_Flags":
                statusFlags = device.castToArrayBoolean(propertyValue);
                encodable = new StatusFlags(statusFlags[0], statusFlags[1], statusFlags[2], statusFlags[3]);
                device.addProperty(bacnetObjectType, PropertyIdentifier.statusFlags, encodable);
                break;
            case "Update_Interval":
                updateInterval = Integer.parseInt(propertyValue);
                encodable = new UnsignedInteger(updateInterval);
                device.addProperty(bacnetObjectType, PropertyIdentifier.updateInterval, encodable);
                break;
            case "Acked_Transitions":
                ackedTransitions = device.castToArrayBoolean(propertyValue);
                encodable = new EventTransitionBits(ackedTransitions[0], ackedTransitions[1], ackedTransitions[2]);
                device.addProperty(bacnetObjectType, PropertyIdentifier.ackedTransitions, encodable);
                break;
            case "High_Limit":
                highLimit = Float.parseFloat(propertyValue);
                encodable = new Real(highLimit);
                device.addProperty(bacnetObjectType, PropertyIdentifier.highLimit, encodable);
                break;
            case "Notify_Type":
                notifyType = Integer.parseInt(propertyValue);
                encodable = new NotifyType(notifyType);
                device.addProperty(bacnetObjectType, PropertyIdentifier.notifyType, encodable);
                break;
            case "Event_Detection_Enable":
                eventDetectionEnable = Boolean.parseBoolean(propertyValue);
                encodable = new com.serotonin.bacnet4j.type.primitive.Boolean(eventDetectionEnable);
                device.addProperty(bacnetObjectType, PropertyIdentifier.eventDetectionEnable, encodable);
                break;
            case "Max_Pres_Value":
                maxPresValue = Float.parseFloat(propertyValue);
                encodable = new Real(maxPresValue);
                device.addProperty(bacnetObjectType, PropertyIdentifier.maxPresValue, encodable);
                break;
            case "Min_Pres_Value":
                minPresValue = Float.parseFloat(propertyValue);
                encodable = new Real(minPresValue);
                device.addProperty(bacnetObjectType, PropertyIdentifier.minPresValue, encodable);
                break;
            case "Reliability":
                reliability = Integer.parseInt(propertyValue);
                encodable = new Reliability(reliability);
                device.addProperty(bacnetObjectType, PropertyIdentifier.reliability, encodable);
                break;
            case "Event_Message_Texts":
                if(Boolean.parseBoolean(propertyValue)) {
                    eventTransitionBits = new SequenceOf<EventTransitionBits>();
                    encodable = eventTransitionBits;
                    device.addProperty(bacnetObjectType, PropertyIdentifier.eventMessageTexts, encodable);
                }
                break;
            case "Notification_Class":
                notificationClass = Integer.parseInt(propertyValue);
                encodable = new UnsignedInteger(notificationClass);
                device.addProperty(bacnetObjectType, PropertyIdentifier.notificationClass, encodable);
                break;
            case "Description":
                description = propertyValue;
                encodable = new CharacterString(description);
                device.addProperty(bacnetObjectType, PropertyIdentifier.description, encodable);
                break;
            case "Event_Algorithm_Inhibit":
                eventAlgorithmInhibit = Boolean.parseBoolean(propertyValue);
                encodable = new com.serotonin.bacnet4j.type.primitive.Boolean(eventAlgorithmInhibit);
                device.addProperty(bacnetObjectType, PropertyIdentifier.eventAlgorithmInhibit, encodable);
                break;
            case "Units":
                units = Integer.parseInt(propertyValue);
                encodable = new EngineeringUnits(units);
                device.addProperty(bacnetObjectType, PropertyIdentifier.units, encodable);
                break;
            case "Profile_Name":
                profileName = propertyValue;
                encodable = new CharacterString(profileName);
                device.addProperty(bacnetObjectType, PropertyIdentifier.profileName, encodable);
                break;
            case "Relinquish_Default":
                relinquishDefault = Float.parseFloat(propertyValue);
                encodable = new Real(relinquishDefault);
                device.addProperty(bacnetObjectType, PropertyIdentifier.relinquishDefault, encodable);
                break;
            case "Priority_Array":
                priorityArray = Boolean.parseBoolean(propertyValue);
                if(priorityArray) {
                    encodable = new PriorityArray();
                    device.addProperty(bacnetObjectType, PropertyIdentifier.priorityArray, encodable);
                }
                break;

                default:
                throw new IllegalArgumentException(objectProperty + " not found.");
        }
    }
}
