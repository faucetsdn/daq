package helper;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

import com.google.common.collect.ArrayListMultimap;
import com.google.common.collect.Multimap;

public class Csv {

  private PicsValidator picsValidator = new PicsValidator();
  private String csvFile = null;
  private String line = "";
  private String csvSplitBy = ",";
  private Multimap<String, Object> picsMap = ArrayListMultimap.create();
  private String[] csvColumnTitle = {
    "Bacnet_Object_Type", "Bacnet_Object_Property", "Conformance_Code", "Supported"
  };
  private boolean passedTest = false;
  private String appendixText = "";

  public Csv(String csvFile) {
    this.csvFile = csvFile;
  }

  public void readAndValidate(Multimap<String, Map<String, String>> bacnetPointsMap, boolean verboseOutput) {
    try (BufferedReader br = new BufferedReader(new FileReader(csvFile))) {
      while ((line = br.readLine()) != null) {
        String[] value = line.split(csvSplitBy);
        final String objectType = value[0];
        final String objectProperty = value[1];
        final String conformanceCode = value[3];
        final String supported = value[4];
        if (!objectType.equals(csvColumnTitle[0])
            && !objectProperty.equals(csvColumnTitle[1])
            && !conformanceCode.equals(csvColumnTitle[2])
            && !supported.equals(csvColumnTitle[3])) {
          saveValuesToMap(value);
          validateLine(value[0], value[1], value[3], value[4], bacnetPointsMap, verboseOutput);
        }
      }
      setTestResult(picsValidator.getResult());
    } catch (IOException e) {
      String errorMessage = "CSV file error: " + e.getMessage();
      System.err.println(errorMessage);
      setTestResult(false);
      setTestAppendices(errorMessage);
    }
  }

  private void validateLine(
      String bacnetObjectType,
      String bacnetObjectProperty,
      String conformanceCode,
      String supported,
      Multimap bacnetPointsMap,
      boolean verboseOutput) {
    try {
      picsValidator.validate(
          formatValue(bacnetObjectType),
          formatValue(bacnetObjectProperty),
          conformanceCode,
          supported,
          bacnetPointsMap, verboseOutput);
    } catch (Exception e) {
      System.err.println(
          "Error validating property: "
              + e.getMessage()
              + " "
              + bacnetObjectType
              + " "
              + bacnetObjectProperty);
    }
  }

  public boolean getTestResult() {
    return this.passedTest;
  }

  private void setTestResult(boolean result) {
    this.passedTest = result;
  }

  public String getTestAppendices() {
    Multimap<String, String> appendicesMap = picsValidator.getResultMap();

    for (Map.Entry appendix : appendicesMap.entries()) {
      appendixText += String.format("%s %s \n", appendix.getKey(), appendix.getValue());
    }
    return appendixText + "\n";
  }

  private void setTestAppendices(String appendix) {
    this.appendixText = appendix;
  }

  private void saveValuesToMap(String[] values) {
    String bacnetObjectType = formatValue(values[0]);
    String bacnetObjectProperty = values[1];
    String conformanceCode = values[3];
    String supported = values[4];
    Map<String, String[]> bacnetObjectPropertyMap = new HashMap<>();
    String[] properties = {conformanceCode, supported};
    bacnetObjectPropertyMap.put(bacnetObjectProperty, properties);
    picsMap.put(bacnetObjectType, bacnetObjectPropertyMap);
  }

  private String formatValue(String value) {
    if (value.isEmpty() || value.trim().length() == 0) {
      return "";
    }
    String[] bacnetObjectTypes = {
      "Analog_Input, Analog_Output",
      "Analog_Value",
      "Binary_Input",
      "Binary_Output",
      "Binary_Value",
      "Calendar",
      "Device",
      "Event_Enrollment",
      "File",
      "Loop",
      "Multi-state_Input",
      "Multi-state_Value",
      "Program",
      "Notification",
      "Schedule",
      "Trend_Log"
    };

    value = value.replace("Bacnet_", "")
            .replace("Analogue", "Analog")
            .replace("_", " ");

    for (int count = 0; count < bacnetObjectTypes.length; count++) {
      String bacnetObjectType = bacnetObjectTypes[count];
      if (bacnetObjectType.contains(value)) {
        bacnetObjectType = bacnetObjectType.replaceAll("_", " ");
        return bacnetObjectType;
      }
    }
    return value;
  }
}
