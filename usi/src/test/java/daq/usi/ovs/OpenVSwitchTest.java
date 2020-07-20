package daq.usi.ovs;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.io.FileNotFoundException;
import java.io.IOException;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class OpenVSwitchTest {
  OpenVSwitch ovs;

  @BeforeEach
  void setUp() {
    ovs = new OpenVSwitch();
  }

  @AfterEach
  void tearDown() {
  }

  @Test
  void getInterfaceByPort() throws IOException {
    assertEquals(ovs.getInterfaceByPort(1), "faux");
    assertEquals(ovs.getInterfaceByPort(2), "faux-2");
    assertEquals(ovs.getInterfaceByPort(7), "sec-eth7");
  }

}