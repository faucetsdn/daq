package helper;

import com.google.common.collect.ArrayListMultimap;
import com.google.common.collect.Multimap;

import java.util.*;
import java.util.regex.Pattern;

public class PicsValidator {
  String read = "R";
  String write = "W";
  String optional = "O";
  String Supported = "TRUE";
  String formatProperty = "%-35s%-35s%-15s%-25s";

  Multimap<String, String> result = ArrayListMultimap.create();

  boolean testPassed = false;
  private int count = 0;

  public void validate(String bacnetObjectType, String bacnetObjectProperty, String conformanceCode,
                       String supported, Multimap bacnetPointsMap, boolean verboseOutput) {

    Set<String> mapKeySet = bacnetPointsMap.keySet();
    ArrayList<String> keys = getMapKeys(mapKeySet, bacnetObjectType);

    if (keys.size() == 0 && (conformanceCode.contains(read) || conformanceCode.equals(write))
            && !bacnetObjectProperty.equals("Property List")) {
      writeToAppendix(formatProperty, bacnetObjectType, bacnetObjectProperty, conformanceCode,
              "FAILED", verboseOutput);
      setResult(false);
    } else if (keys.size() == 0 && conformanceCode.contains(optional)
            && !bacnetObjectProperty.equals("Property List")) {
      writeToAppendix(formatProperty, bacnetObjectType, bacnetObjectProperty, conformanceCode,
              "PASSED/WARNING", verboseOutput);
      setResult(true);
    } else if (keys.size() == 0 && bacnetObjectProperty.equals("Property List")) {
      writeToAppendix(formatProperty, bacnetObjectType, bacnetObjectProperty, conformanceCode,
              "PASSED", verboseOutput);
      setResult(true);
    }

    for (String key : keys) {
      String properties = bacnetPointsMap.get(key).toString();
      boolean bacnetObjectPropertyIsFound =
          Pattern.compile(Pattern.quote(bacnetObjectProperty), Pattern.CASE_INSENSITIVE)
              .matcher(properties).find();
      if (!bacnetObjectPropertyIsFound
          && (conformanceCode.contains(read) || conformanceCode.equals(write)) && supported.equals(Supported)
          && !bacnetObjectProperty.equals("Property List")) {
        writeToAppendix(formatProperty, bacnetObjectType, bacnetObjectProperty, conformanceCode,
                "FAILED", verboseOutput);
        setResult(false);
      } else if (!bacnetObjectPropertyIsFound && conformanceCode.contains(optional)
          && supported.equals(Supported) && !bacnetObjectProperty.equals("Property List")) {
        writeToAppendix(formatProperty, bacnetObjectType, bacnetObjectProperty, conformanceCode,
                "PASSED/WARNING", verboseOutput);
        setResult(true);
      } else if (bacnetObjectPropertyIsFound && supported.equals(Supported)
          && !bacnetObjectProperty.equals("Property List")) {
        writeToAppendix(formatProperty, bacnetObjectType, bacnetObjectProperty, conformanceCode,
                "PASSED", verboseOutput);
        setResult(true);
      }
    }
  }

  private void writeToAppendix(String formatProperty, String key, String bacnetObjectProperty, String conformanceCode,
                               String lineresult, boolean verboseOutput) {
    if (!verboseOutput & (lineresult.contains("FAILED") | lineresult.contains("PASSED/WARNING"))) {
      String appendix = String.format(formatProperty, key, bacnetObjectProperty,
              conformanceCode, lineresult);
      this.result.put(key, appendix);
    } else if (verboseOutput) {
      String appendix = String.format(formatProperty, key, bacnetObjectProperty,
              conformanceCode, lineresult);
      this.result.put(key, appendix);
    }
  }

  private ArrayList<String> getMapKeys(Set<String> mapKeySet, String bacnetObjectType) {
    ArrayList<String> keys = new ArrayList<>();
    for (String key : mapKeySet) {
      if (key.contains(bacnetObjectType)) {
        keys.add(key);
      }
    }
    return keys;
  }

  private void setResult(boolean propertyValidated) {
    if(count == 0) {
      this.testPassed = propertyValidated;
    } else {
      if(!this.testPassed) {
        return;
      } else { this.testPassed = propertyValidated; }
    }
    count++;
  }

  public Multimap<String, String> getResultMap() {
    return this.result;
  }

  public boolean getResult() {
    return this.testPassed;
  }
}
