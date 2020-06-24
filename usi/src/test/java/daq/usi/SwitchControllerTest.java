package daq.usi;

import static org.junit.jupiter.api.Assertions.*;


import daq.usi.SwitchController;
import java.util.Map;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class SwitchControllerTest {

  @BeforeEach
  void setUp() {
  }

  @AfterEach
  void tearDown() {
  }

  @Test
  void mapSimpleTableEmptyInput() {
    String raw = "";
    String[] colNames = {"a", "b"};
    String[] mapNames = {"a", "b"};
    Map<String, String> response = SwitchController.mapSimpleTable(raw, colNames, mapNames);
    for (String key: response.keySet()) {
      assertEquals(response.get(key), null);
    }
  }

  @Test
  void mapSimpleTableSampleInputAT() {
    String raw = "Interface   Admin    Pri  Oper     Power Device          Class Max       \n" +
        "port1.0.1   Enabled  Low  Powered   3337 n/a                 0 15400 [C]";
    String[] colNames = {"Interface", "Admin", "Pri", "Oper", "Power", "Device", "Class", "Max"};
    String[] mapNames = {"interface", "admin", "pri", "oper", "power", "device", "class", "max"};
    Map<String, String> expected = Map.of("interface", "port1.0.1", "admin", "Enabled", "pri",
        "Low", "oper", "Powered", "power", "3337", "device", "n/a", "class", "0", "max", "15400 [C]");
    Map<String, String> response = SwitchController.mapSimpleTable(raw, colNames, mapNames);
    for (String key: response.keySet()) {
      assertEquals(response.get(key), expected.get(key));
    }
  }

}