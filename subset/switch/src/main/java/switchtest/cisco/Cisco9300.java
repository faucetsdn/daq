package switchtest.cisco;

/*
 * Licensed to the Google under one or more contributor license agreements.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import switchtest.SwitchInterrogator;

import java.util.HashMap;

public class Cisco9300 extends SwitchInterrogator {

  int commandIndex = 0;
  boolean commandPending = false;
  boolean promptReady = false;
  StringBuilder rxData = new StringBuilder();

  /** Cisco Terminal Prompt ends with # when enabled */
  String consolePromptEndingEnabled = "#";

  String consolePromptEndingLogin = ">";

  public Cisco9300(String remoteIpAddress, int interfacePort, boolean deviceConfigPoeEnabled) {
    super(remoteIpAddress, interfacePort, deviceConfigPoeEnabled);
    telnetClientSocket =
        new CiscoSwitchTelnetClientSocket(remoteIpAddress, remotePort, this, debug);
    // TODO: enabled the user to input their own username and password
    this.username = "admin";
    this.password = "password";
  }

  /** Generic Cisco Switch command to retrieve the Status of an interface. */
  private String showIfaceStatusCommand() {
    return "show interface gigabitethernet1/0/" + interfacePort + " status";
  }

  /**
   * Generic Cisco Switch command to retrieve the Power Status of an interface. Replace asterisk
   * with actual port number for complete message
   */
  private String showIfacePowerStatusCommand() {
    return "show power inline gigabitethernet1/0/" + interfacePort;
  }

  /**
   * Builds an array of currently supported commands to send to the Cisco Switch for the port
   * specified.
   *
   * @return String array of commands to be submitted to the switch
   */
  public String[] commands() {
    return new String[] {showIfaceStatusCommand(), showIfacePowerStatusCommand()};
  }

  /** Run all current tests in order and create and store the results */
  public void generateTestResults() {
    login_report += "\n";
    login_report += validateLinkTest();
    login_report += validateSpeedTests();
    login_report += validateDuplexTests();
    login_report += validatePowerTests();
  }

  public boolean handleCommandResponse(String consoleData) {
    if (consoleData == null) return false;
    if (consoleData.endsWith(getHostname() + consolePromptEndingEnabled)) {
      // Strip trailing command prompt
      String response =
          consoleData.substring(0, consoleData.length() - (getHostname() + "#").length());
      // Strip leading command that was sent
      response = response.substring(command[commandIndex].length());
      processCommandResponse(response);
      promptReady = true;
      commandPending = false;
      ++commandIndex;
      return true;
    }
    return false;
  }

  /**
   * Handles the process when using the enter command. Enable is a required step before commands can
   * be sent to the switch.
   *
   * @param consoleData Raw console data received the the telnet connection.
   * @return True if the data provided was understood and processed. False if the data is not an
   *     expected result or the enable process failed.
   */
  public boolean handleEnableMessage(String consoleData) throws Exception {
    if (consoleData == null) return false;
    if (consoleData.indexOf("Password:") >= 0) {
      telnetClientSocket.writeData(password + "\n");
      return true;
    } else if (consoleData.endsWith(consolePromptEndingEnabled)) {
      setUserEnabled(true);
      return true;
    } else if (consoleData.indexOf("% Bad passwords") >= 0) {
      telnetClientSocket.disposeConnection();
      throw new Exception("Could not Enable the User, Bad Password");
    }
    return false;
  }

  /**
   * Handles the process when logging into the switch.
   *
   * @param consoleData Raw console data received the the telnet connection.
   * @return True if the data provided was understood and processed. False if the data is not an
   *     expected result or if the login failed.
   */
  public boolean handleLoginMessage(String consoleData) throws Exception {
    if (consoleData == null) return false;
    if (consoleData.indexOf("Username:") >= 0) {
      telnetClientSocket.writeData(username + "\n");
      return true;
    } else if (consoleData.indexOf("Password:") >= 0) {
      telnetClientSocket.writeData(password + "\n");
      return true;
    } else if (consoleData.endsWith(consolePromptEndingLogin)) {
      setUserAuthorised(true);
      setHostname(consoleData.split(">")[0]);
      telnetClientSocket.writeData("enable\n");
      return true;
    } else if (consoleData.indexOf("% Login invalid") >= 0) {
      telnetClientSocket.disposeConnection();
      throw new Exception("Failked to Login, Login Invalid");
    } else if (consoleData.indexOf("% Bad passwords") >= 0) {
      telnetClientSocket.disposeConnection();
      throw new Exception("Failed to Login, Bad Password");
    }
    return false;
  }

  /**
   * If the message --More-- is present in the current data packet, this indicates the message is
   * incomplete. To complete the message, we need to tell the console to continue the response and
   * strip the --More-- entry from the data packet as it is not actually part of the response.
   *
   * @param consoleData Current unprocessed data packet
   */
  public void handleMore(String consoleData) {
    consoleData = consoleData.substring(0, consoleData.length() - "--More--".length());
    telnetClientSocket.writeData("\n");
    rxData.append(consoleData);
  }

  /**
   * Receive the raw data packet from the telnet connection and process accordingly.
   *
   * @param data Most recent data read from the telnet socket buffer
   */
  public void receiveData(String data) {
    if (debug) {
      System.out.println(
          java.time.LocalTime.now() + "receiveDataLen:" + data.length() + "receiveData:" + data);
    }
    if (data != null) {
      if (!data.isEmpty()) {
        if (data.indexOf("--More--") > 0) {
          handleMore(data);
          return;
        } else {
          rxData.append(data);
        }
      }
      try {
        if (parseData(rxData.toString())) {
          // If we have processed the current buffers data we will clear the buffer
          rxData = new StringBuilder();
        }
      } catch (Exception e) {
        telnetClientSocket.disposeConnection();
        e.printStackTrace();
      }
    }
  }

  /**
   * Handles current data in the buffer read from the telnet console InputStream and sends it to the
   * appropriate process.
   *
   * @param consoleData Current unhandled data in the buffered reader
   * @return true if the data was an expected value and appropriately processed and return false if
   *     the data is not-expected.
   */
  public boolean parseData(String consoleData) throws Exception {
    consoleData = consoleData.trim();
    if (!getUserAuthorised()) {
      return handleLoginMessage(consoleData);
    } else if (!getUserEnabled()) {
      return handleEnableMessage(consoleData);
    } else {
      // Logged in and enabled
      if (commandPending) { // Command has been sent and awaiting a response
        if (handleCommandResponse(consoleData)) {
          telnetClientSocket.writeData("\n");
          return true;
        }
      } else if (command.length > commandIndex) {
        if (consoleData.endsWith(getHostname() + consolePromptEndingEnabled)) {
          sendNextCommand();
          return true;
        }
      } else {
        generateTestResults();
        writeReport();
        telnetClientSocket.disposeConnection();
      }
    }
    return false;
  }

  public String validateLinkTest() {
    String testResults = "";
    if (interface_map.get("status").equals("connected")) {
      testResults += "RESULT pass connection.port_link\n";
    } else {
      testResults += "RESULT fail connection.port_link Link is down\n";
    }
    return testResults;
  }

  public String validateSpeedTests() {
    String testResults = "";
    if (interface_map.get("speed") != null) {
      String speed = interface_map.get("speed");
      if (speed.startsWith("a-")) { // Interface in Auto Speed
        speed = speed.replaceFirst("a-", "");
      }
      if (Integer.parseInt(speed) >= 10) {
        testResults += "RESULT pass connection.port_speed\n";
      } else {
        testResults += "RESULT fail connection.port_speed Speed is too slow\n";
      }
    } else {
      testResults += "RESULT fail connection.port_speed Cannot detect current speed\n";
    }
    return testResults;
  }

  public String validateDuplexTests() {
    String testResults = "";
    if (interface_map.get("duplex") != null) {
      String duplex = interface_map.get("duplex");
      if (duplex.startsWith("a-")) { // Interface in Auto Duplex
        duplex = duplex.replaceFirst("a-", "");
      }
      if (duplex.equals("full")) {
        testResults += "RESULT pass connection.port_duplex\n";
      } else {
        testResults += "RESULT fail connection.port_duplex Incorrect duplex mode set\n";
      }
    } else {
      testResults += "RESULT fail connection.port_duplex Cannot detect duplex mode\n";
    }
    return testResults;
  }

  public String validatePowerTests() {
    String testResults = "";
    double maxPower = 0;
    double currentPower = 0;
    boolean powerAuto = false;
    boolean poeDisabled = false;
    boolean poeOn = false;
    boolean poeOff = false;
    boolean poeFault = false;
    boolean poeDeny = false;
    try {
      // Generate test data from mapped results
      maxPower = Double.parseDouble(power_map.get("max"));
      currentPower = Double.parseDouble(power_map.get("power"));
      powerAuto = "auto".equals(power_map.get("admin"));
      poeDisabled = "off".equals(power_map.get("admin"));
      poeOn = "on".equals(power_map.get("oper"));
      poeOff = "off".equals(power_map.get("oper"));
      poeFault = "fault".equals(power_map.get("oper"));
      poeDeny = "power-deny".equals(power_map.get("oper"));
    } catch (Exception e) {
      // ToDo: Make these failures specific to the data resolve errors instead of all or nothing
      System.out.println("Power Tests Failed: " + e.getMessage());
      e.printStackTrace();
      testResults += "RESULT fail poe.power Could not detect any current being drawn\n";
      testResults += "RESULT fail poe.negotiation Could not detect any current being drawn\n";
      testResults += "RESULT fail poe.support Could not detect any current being drawn\n";
      return testResults;
    }

    if (!deviceConfigPoeEnabled) {
      testResults += "RESULT skip poe.power This test is disabled\n";
      testResults += "RESULT skip poe.negotiation This test is disabled\n";
      testResults += "RESULT skip poe.support This test is disabled\n";

    } else if (poeDisabled) {
      testResults += "RESULT skip poe.power The switch does not support PoE\n";
      testResults += "RESULT skip poe.negotiation The switch does not support PoE\n";
      testResults += "RESULT skip poe.support The switch does not support PoE\n";
    } else {

      // Determine PoE power test result
      if (maxPower >= currentPower && poeOn) {
        testResults += "RESULT pass poe.power\n";
      } else if (poeOff) {
        testResults += "RESULT fail poe.power No poE is applied\n";
      } else if (poeFault) {
        testResults +=
            "RESULT fail poe.power Device detection or a powered device is in a faulty state\n";
      } else if (poeDeny) {
        testResults +=
            "RESULT fail poe.power A powered device is detected, but no PoE is available, or the maximum wattage exceeds the detected powered-device maximum.\n";
      }

      // Determine PoE auto negotiation result
      if (powerAuto) {
        testResults += "RESULT pass poe.negotiation\n";
      } else {
        testResults += "RESULT fail poe.negotiation Incorrect privilege for negotiation\n";
      }

      // Determine PoE support result
      if (poeOn) {
        testResults += "RESULT pass poe.support\n";
      } else {
        testResults +=
            "RESULT fail poe.support The switch does not support PoE or it is disabled\n";
      }
    }

    return testResults;
  }

  private void processCommandResponse(String response) {
    response = response.trim();
    System.out.println("\nProcessing Command Response:\n" + response);
    switch (commandIndex) {
      case 0: // show interface status
        processInterfaceStatus(response);
        break;
      case 1: // show power status
        processPowerStatus(response);
    }
  }

  public HashMap<String, String> processInterfaceStatus(String response) {
    interface_map = mapSimpleTable(response, show_interface_expected, interface_expected);
    return interface_map;
  }

  public HashMap<String, String> processPowerStatus(String response) {
    // Pre-process raw data to be map ready
    response.replaceAll("-", "");
    String[] lines = response.split("\n");
    response = lines[0] + " \n" + lines[lines.length - 1];
    power_map = mapSimpleTable(response, show_power_expected, power_expected);
    return power_map;
  }

  /**
   * Map a simple table containing a header and 1 row of data to a hashmap
   *
   * <p>his method will also attempt ot correct for mis-aligned tabular data as well as empty
   * columns values.
   *
   * @param rawPacket Raw table response from a switch command
   * @param colNames Array containing the names of the columns in the response
   * @param mapNames Array containing names key names to map values to
   * @return A HashMap containing the values mapped to the key names provided in the mapNames array
   */
  public HashMap<String, String> mapSimpleTable(
      String rawPacket, String[] colNames, String[] mapNames) {
    HashMap<String, String> colMap = new HashMap();
    String[] lines = rawPacket.split("\n");
    if (lines.length > 0) {
      String header = lines[0].trim();
      String values = lines[1].trim();
      int lastSectionEnd = 0;
      for (int i = 0; i < colNames.length; ++i) {
        int secStart = lastSectionEnd;
        int secEnd;
        if ((i + 1) >= colNames.length) {
          // Resolving last column
          secEnd = values.length();
        } else {
          // Tabular data is not always reported in perfectly alignment, we need to calculate the
          // correct values based off of the sections in between white spaces
          int firstWhiteSpace =
              getFirstWhiteSpace(values.substring(lastSectionEnd)) + lastSectionEnd;
          int lastWhiteSpace =
              getIndexOfNonWhitespaceAfterWhitespace(values.substring(firstWhiteSpace))
                  + firstWhiteSpace;
          int nextHeaderStart = header.indexOf(colNames[i + 1]);
          secEnd = Math.min(lastWhiteSpace, nextHeaderStart);
        }
        lastSectionEnd = secEnd;
        String sectionRaw = values.substring(secStart, secEnd).trim();
        colMap.put(mapNames[i], sectionRaw);
      }
    }
    return colMap;
  }

  public static int getFirstWhiteSpace(String string) {
    char[] characters = string.toCharArray();
    for (int i = 0; i < string.length(); i++) {
      if (Character.isWhitespace(characters[i])) {
        return i;
      }
    }
    return -1;
  }

  public static int getIndexOfNonWhitespaceAfterWhitespace(String string) {
    char[] characters = string.toCharArray();
    boolean lastWhitespace = false;
    for (int i = 0; i < string.length(); i++) {
      if (Character.isWhitespace(characters[i])) {
        lastWhitespace = true;
      } else if (lastWhitespace) {
        return i;
      }
    }
    return -1;
  }

  public void sendNextCommand() {
    telnetClientSocket.writeData(command[commandIndex] + "\n");
    commandPending = true;
    promptReady = false;
  }

  public String[] interfaceExpected() {
    return new String[] {"interface", "name", "status", "vlan", "duplex", "speed", "type"};
  }

  public String[] powerExpected() {
    return new String[] {"dev_interface", "admin", "oper", "power", "device", "dev_class", "max"};
  }

  public String[] showInterfaceExpected() {
    return new String[] {"Port", "Name", "Status", "Vlan", "Duplex", "Speed", "Type"};
  }

  public String[] showPowerExpected() {
    return new String[] {"Interface", "Admin", "Oper", "Power", "Device", "Class", "Max"};
  }

  // Unused methods implemented for compiling only
  public String[] commandToggle() {
    return new String[] {};
  }

  public String[] expected() {
    return new String[] {};
  }

  public String[] loginExpected() {
    return new String[] {};
  }

  public String[] platformExpected() {
    return new String[] {};
  }

  public String[] showInterfacePortExpected() {
    return new String[] {};
  }

  public String[] showPlatformExpected() {
    return new String[] {};
  }

  public String[] showPlatformPortExpected() {
    return new String[] {};
  }

  public String[] stackExpected() {
    return new String[] {};
  }

  public String[] showStackExpected() {
    return new String[] {};
  }
}
