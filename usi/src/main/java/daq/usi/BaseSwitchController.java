package daq.usi;

import java.util.HashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;


public abstract class BaseSwitchController implements SwitchController {
  /**
   * Terminal Prompt ends with '#' when enabled, '>' when not enabled.
   */
  public static final String CONSOLE_PROMPT_ENDING_ENABLED = "#";
  public static final String CONSOLE_PROMPT_ENDING_LOGIN = ">";
  public static final int TELNET_PORT = 23;

  // Define Common Variables Required for All Switch Interrogators
  protected SwitchTelnetClientSocket telnetClientSocket;
  protected Thread telnetClientSocketThread;
  protected String remoteIpAddress;
  protected boolean debug;
  protected String username;
  protected String password;
  protected boolean userAuthorised = false;
  protected boolean userEnabled = false;
  protected String hostname = null;
  protected boolean commandPending = false;

  public BaseSwitchController(String remoteIpAddress, String username,
                              String password) {
    this(remoteIpAddress, username, password, false);
  }

  /**
   * Abstract Switch controller. Override this class for switch specific implementation
   *
   * @param remoteIpAddress switch ip address
   * @param username        switch username
   * @param password        switch password
   * @param debug           for verbose logging
   */
  public BaseSwitchController(
      String remoteIpAddress, String username, String password, boolean debug) {
    this.remoteIpAddress = remoteIpAddress;
    this.username = username;
    this.password = password;
    this.debug = debug;
    telnetClientSocket =
        new SwitchTelnetClientSocket(remoteIpAddress, TELNET_PORT, this, debug);
  }

  /**
   * Map a simple table containing a header and 1 row of data to a hashmap
   * This method will also attempt to correct for mis-aligned tabular data as well as empty
   * columns values.
   *
   * @param rawPacket Raw table response from a switch command
   * @param colNames  Array containing the names of the columns in the response
   * @param mapNames  Array containing names key names to map values to
   * @return A HashMap containing the values mapped to the key names provided in the mapNames array
   */
  protected static HashMap<String, String> mapSimpleTable(
      String rawPacket, String[] colNames, String[] mapNames) {
    HashMap<String, String> colMap = new HashMap<>();
    String[] lines = rawPacket.split("\n");
    int headerLine = 0;
    if (lines.length >= headerLine + 2) {
      String header = lines[headerLine].trim();
      String values = lines[headerLine + 1].trim();
      int lastSectionEnd = 0;
      for (int i = 0; i < colNames.length; i++) {
        int secStart = lastSectionEnd;
        int secEnd;
        if ((i + 1) >= colNames.length) {
          // Resolving last column
          secEnd = values.length();
        } else {
          // Tabular data is not always reported in perfectly alignment, we need to calculate the
          // correct values based off of the sections in between white spaces
          int nextHeaderStart = header.indexOf(colNames[i + 1]);
          if (Character.isWhitespace(values.charAt(lastSectionEnd))
              && lastSectionEnd < nextHeaderStart) {
            lastSectionEnd++;
          }
          int firstWhiteSpace =
              getFirstWhiteSpace(values.substring(lastSectionEnd)) + lastSectionEnd;
          // Wrong table header line
          if (firstWhiteSpace < 0) {
            headerLine++;
            break;
          }
          int lastWhiteSpace =
              getIndexOfNonWhitespaceAfterWhitespace(values.substring(firstWhiteSpace))
                  + firstWhiteSpace;
          // Account for empty values in a table.
          if (nextHeaderStart >= firstWhiteSpace && nextHeaderStart <= lastWhiteSpace) {
            secEnd = nextHeaderStart;
          } else {
            char beforeHead = values.charAt(nextHeaderStart - 1);
            if (Character.isWhitespace(beforeHead)) {
              secEnd = Math.max(lastWhiteSpace, nextHeaderStart);
            } else {
              secEnd = lastWhiteSpace;
            }
          }

        }
        lastSectionEnd = secEnd;
        // \u00A0 is non-breaking space which trim ignores.
        String rawString = values.substring(secStart, secEnd)
            .replace('\u00A0', ' ').trim();
        colMap.put(mapNames[i], rawString);
      }
    }
    return colMap;
  }

  private static int getFirstWhiteSpace(String string) {
    char[] characters = string.toCharArray();
    for (int i = 0; i < string.length(); i++) {
      if (Character.isWhitespace(characters[i])) {
        return i;
      }
    }
    return -1;
  }

  private static int getIndexOfNonWhitespaceAfterWhitespace(String string) {
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

  protected boolean containsPrompt(String consoleData) {
    // Prompts usually hostname# or hostname(config)#
    Pattern r = Pattern.compile(hostname + "\\s*(\\(.+\\))?" + CONSOLE_PROMPT_ENDING_ENABLED, 'g');
    Matcher m = r.matcher(consoleData);
    return m.find();
  }

  protected boolean promptReady(String consoleData) {
    // Prompts usually hostname# or hostname(config)#
    Pattern r = Pattern.compile(hostname + "\\s*(\\(.+\\))?" + CONSOLE_PROMPT_ENDING_ENABLED + "$");
    Matcher m = r.matcher(consoleData);
    return m.find();
  }

  /**
   * Receive the raw data packet from the telnet connection and process accordingly.
   *
   * @param consoleData Most recent data read from the telnet socket buffer
   */
  public void receiveData(String consoleData) {
    if (debug) {
      System.out.println(
          java.time.LocalTime.now() + " receivedData:\t" + consoleData);
    }
    if (consoleData != null) {
      try {
        consoleData = consoleData.trim();
        if (!userAuthorised) {
          handleLoginMessage(consoleData);
        } else if (!userEnabled) {
          handleEnableMessage(consoleData);
        } else {
          parseData(consoleData);
        }
      } catch (Exception e) {
        telnetClientSocket.disposeConnection();
        e.printStackTrace();
      }
    }
  }

  protected abstract void parseData(String consoleData) throws Exception;

  protected abstract void handleLoginMessage(String consoleData) throws Exception;

  protected abstract void handleEnableMessage(String consoleData) throws Exception;

  @Override
  public void start() {
    telnetClientSocketThread = new Thread(telnetClientSocket);
    telnetClientSocketThread.start();
  }
}
