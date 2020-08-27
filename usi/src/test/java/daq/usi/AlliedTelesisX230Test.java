package daq.usi;

import static org.junit.jupiter.api.Assertions.assertEquals;

import daq.usi.allied.AlliedTelesisX230;
import grpc.POENegotiation;
import grpc.POEStatus;
import grpc.POESupport;
import grpc.PowerResponse;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class AlliedTelesisX230Test {

  private AlliedTelesisX230 at;

  @BeforeEach
  void setUp() {
    at = new AlliedTelesisX230(null, null, null);
    at.telnetClientSocket = new FakeSwitchTelnetClientSocket(null, 0, null, false);
  }

  @AfterEach
  void tearDown() {
  }

  @Test
  void testEmptyPower() throws Exception {
    at.userAuthorised = true;
    at.userEnabled = true;
    at.commandPending = false;
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
}
