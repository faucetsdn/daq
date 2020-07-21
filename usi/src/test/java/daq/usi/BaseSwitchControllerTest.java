package daq.usi;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import java.util.Map;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class BaseSwitchControllerTest {

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
    Map<String, String> response = BaseSwitchController.mapSimpleTable(raw, colNames, mapNames);
    for (String key : response.keySet()) {
      assertNull(response.get(key));
    }
  }

  @Test
  void mapSimpleTableSampleInputAT() {
    String raw = "Interface   Admin    Pri  Oper     Power Device          Class Max       \n"
        + "port1.0.1   Enabled  Low  Powered   3337 n/a                 0 15400 [C]";
    String[] colNames = {"Interface", "Admin", "Pri", "Oper", "Power", "Device", "Class", "Max"};
    String[] mapNames = {"interface", "admin", "pri", "oper", "power", "device", "class", "max"};
    Map<String, String> expected = Map.of("interface", "port1.0.1", "admin", "Enabled", "pri",
        "Low", "oper", "Powered", "power", "3337", "device", "n/a",
        "class", "0", "max", "15400 [C]");
    Map<String, String> response = BaseSwitchController.mapSimpleTable(raw, colNames, mapNames);
    for (String key : response.keySet()) {
      assertEquals(expected.get(key), response.get(key));
    }
  }

  @Test
  void mapSimpleTableSampleInputCisco9300() {
    String raw = "Port         Name               Status       Vlan       Duplex  Speed Type\n"
        + "Gi1/0/1                         connected    routed     a-full  a-100 10/100/1000BaseTX";
    String[] colNames =  {"Port", "Name", "Status", "Vlan", "Duplex", "Speed", "Type"};
    String[] mapNames =       {"interface", "name", "status", "vlan", "duplex", "speed", "type"};
    Map<String, String> expected = Map.of("interface", "Gi1/0/1", "name", "", "status",
        "connected", "vlan", "routed", "duplex", "a-full", "speed", "a-100",
        "type", "10/100/1000BaseTX");
    Map<String, String> response = BaseSwitchController.mapSimpleTable(raw, colNames, mapNames);
    for (String key : response.keySet()) {
      assertEquals(expected.get(key), response.get(key));
    }
  }
}