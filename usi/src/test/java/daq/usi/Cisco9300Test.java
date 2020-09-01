package daq.usi;

import static org.junit.jupiter.api.Assertions.assertEquals;

import daq.usi.cisco.Cisco9300;
import grpc.InterfaceResponse;
import grpc.LinkStatus;
import grpc.POENegotiation;
import grpc.POEStatus;
import grpc.POESupport;
import grpc.PowerResponse;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class Cisco9300Test {

  private Cisco9300 at;

  @BeforeEach
  void setUp() {
    at = new Cisco9300(null, null, null);
    at.telnetClientSocket = new FakeSwitchTelnetClientSocket(null, 0, null, false);
  }

  @AfterEach
  void tearDown() {
  }

  private void fakeLogin() {
    at.userAuthorised = true;
    at.userEnabled = true;
    at.commandPending = false;
  }

  @Test
  void testEmptyPower() throws Exception {
    fakeLogin();
    at.getPower(1, new ResponseHandler<PowerResponse>() {
      @Override
      public void receiveData(PowerResponse data) throws Exception {
        assertEquals(data.getPoeSupport(), POESupport.State.UNKNOWN);
        assertEquals(data.getPoeNegotiation(), POENegotiation.State.UNKNOWN);
        assertEquals(data.getPoeStatus(), POEStatus.State.UNKNOWN);
        assertEquals(data.getCurrentPowerConsumption(), 0);
        assertEquals(data.getMaxPowerConsumption(), 0);
      }
    });
    at.receiveData("");
  }

  @Test
  void testSampleInterfaceResponse() throws Exception {
    final String output = "show interface gigabitethernet1/0/2 status\n\n\n"
        + "Port      Name               Status       Vlan       Duplex  Speed Type\n"
        + "Gi1/0/4                      connected    trunk      a-full  a-100 10/100/1000BaseTX\n"
        + "daq#\n";
    fakeLogin();
    at.getInterface(1, new ResponseHandler<InterfaceResponse>() {
      @Override
      public void receiveData(InterfaceResponse data) throws Exception {
        assertEquals(data.getDuplex(), "full");
        assertEquals(data.getLinkSpeed(), 100);
        assertEquals(data.getLinkStatus(), LinkStatus.State.UP);
      }
    });
    at.receiveData(output);
  }
}
