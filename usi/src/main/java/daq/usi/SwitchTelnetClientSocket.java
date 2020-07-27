package daq.usi;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;
import java.util.Queue;
import org.apache.commons.net.telnet.EchoOptionHandler;
import org.apache.commons.net.telnet.InvalidTelnetOptionException;
import org.apache.commons.net.telnet.SuppressGAOptionHandler;
import org.apache.commons.net.telnet.TelnetClient;
import org.apache.commons.net.telnet.TelnetNotificationHandler;
import org.apache.commons.net.telnet.TerminalTypeOptionHandler;

public class SwitchTelnetClientSocket implements TelnetNotificationHandler, Runnable {
  public static String MORE_INDICATOR = "--More--";

  protected static final int SLEEP_MS = 100;
  // Rx empty space timeout before sending \n
  protected static final int MAX_EMPTY_WAIT_COUNT = 70;

  protected TelnetClient telnetClient;
  protected BaseSwitchController interrogator;

  protected String remoteIpAddress = "";
  protected int remotePort = 23;

  protected InputStream inputStream;
  protected OutputStream outputStream;

  protected Queue<String> rxQueue = new LinkedList<>();

  protected Thread readerThread;
  protected Thread gatherThread;

  protected boolean debug;

  /**
   * Telnet Client.
   * @param remoteIpAddress switch ip address
   * @param remotePort      telent port
   * @param interrogator    switch specific switch controller
   * @param debug For more verbose output.
   */
  public SwitchTelnetClientSocket(
      String remoteIpAddress, int remotePort, BaseSwitchController interrogator, boolean debug) {
    this.remoteIpAddress = remoteIpAddress;
    this.remotePort = remotePort;
    this.interrogator = interrogator;
    this.debug = debug;
    telnetClient = new TelnetClient();
    addOptionHandlers();
  }

  protected void connectTelnetSocket() {
    int attempts = 0;

    while (!telnetClient.isConnected() && attempts < 10) {
      try {
        telnetClient.connect(remoteIpAddress, remotePort);
      } catch (IOException e) {
        System.err.println("Exception while connecting:" + e.getMessage());
      }

      attempts++;

      try {
        Thread.sleep(SLEEP_MS);
      } catch (InterruptedException e) {
        System.err.println("Exception while connecting:" + e.getMessage());
      }
    }
  }

  @Override
  public void run() {
    connectTelnetSocket();

    Runnable readDataRunnable =
        () -> {
          readData();
        };
    readerThread = new Thread(readDataRunnable);

    readerThread.start();

    Runnable gatherDataRunnable =
        () -> {
          gatherData();
        };
    gatherThread = new Thread(gatherDataRunnable);

    gatherThread.start();

    outputStream = telnetClient.getOutputStream();
  }

  protected void gatherData() {
    StringBuilder rxData = new StringBuilder();

    int rxQueueCount = 0;

    while (telnetClient.isConnected()) {
      try {
        if (rxQueue.isEmpty()) {
          Thread.sleep(SLEEP_MS);
          rxQueueCount++;
          if (!interrogator.commandPending && rxQueueCount > MAX_EMPTY_WAIT_COUNT) {
            if (debug) {
              System.out.println("rxQueue Empty. Sending new line.");
            }
            rxQueueCount = 0;
            writeData("\n");
          }
          continue;
        }
        rxQueueCount = 0;
        while (rxQueue.peek().trim() == "") {
          rxQueue.poll();
        }
        String rxTemp = rxQueue.poll();
        if (rxTemp.indexOf(MORE_INDICATOR) > 0) {
          writeData("\n");
          if (debug) {
            System.out.println("more position:" + rxTemp.indexOf(MORE_INDICATOR));
            System.out.println("Data: " + rxTemp);
          }
          rxTemp = rxTemp.replace(MORE_INDICATOR, "");
          rxData.append(rxTemp);
        } else if ((interrogator.userAuthorised && interrogator.userEnabled)
            && !interrogator.promptReady((rxData.toString() + rxTemp).trim())) {
          rxData.append(rxTemp);
          if (debug) {
            System.out.println("Waiting for more data till prompt ready: ");
            System.out.println(rxData.toString().trim());
          }
        } else {
          rxQueueCount = 0;
          rxData.append(rxTemp);
          String rxGathered = rxData.toString().trim();
          rxData = new StringBuilder();
          interrogator.receiveData(rxGathered);
        }
      } catch (InterruptedException e) {
        System.err.println("InterruptedException gatherData:" + e.getMessage());
      }
    }
  }

  /**
   * * Callback method called when TelnetClient receives an option negotiation command.
   *
   * @param negotiationCode - type of negotiation command received (RECEIVED_DO, RECEIVED_DONT,
   *                         RECEIVED_WILL, RECEIVED_WONT, RECEIVED_COMMAND)
   * @param optionCode      - code of the option negotiated *
   */
  public void receivedNegotiation(int negotiationCode, int optionCode) {
    String command = null;
    switch (negotiationCode) {
      case TelnetNotificationHandler.RECEIVED_DO:
        command = "DO";
        break;
      case TelnetNotificationHandler.RECEIVED_DONT:
        command = "DONT";
        break;
      case TelnetNotificationHandler.RECEIVED_WILL:
        command = "WILL";
        break;
      case TelnetNotificationHandler.RECEIVED_WONT:
        command = "WONT";
        break;
      case TelnetNotificationHandler.RECEIVED_COMMAND:
        command = "COMMAND";
        break;
      default:
        command = Integer.toString(negotiationCode); // Should not happen
        break;
    }
    System.out.println("Received " + command + " for option code " + optionCode);
  }

  private void addOptionHandlers() {
    TerminalTypeOptionHandler terminalTypeOptionHandler =
        new TerminalTypeOptionHandler("VT100", false, false, true, false);

    EchoOptionHandler echoOptionHandler = new EchoOptionHandler(false, false, false, false);

    SuppressGAOptionHandler suppressGaOptionHandler =
        new SuppressGAOptionHandler(true, true, true, true);

    try {
      telnetClient.addOptionHandler(terminalTypeOptionHandler);
      telnetClient.addOptionHandler(echoOptionHandler);
      telnetClient.addOptionHandler(suppressGaOptionHandler);
    } catch (InvalidTelnetOptionException e) {
      System.err.println(
          "Error registering option handlers InvalidTelnetOptionException: " + e.getMessage());
    } catch (IOException e) {
      System.err.println("Error registering option handlers IOException: " + e.getMessage());
    }
  }

  private String normalizeLineEnding(byte[] bytes, char endChar) {
    List<Byte> bytesBuffer = new ArrayList<Byte>();

    int countBreak = 0;
    int countEsc = 0;

    for (int i = 0; i < bytes.length; i++) {
      if (bytes[i] != 0) {
        switch (bytes[i]) {
          case 8:
            // backspace \x08
            break;
          case 10:
            // newLineFeed \x0A
            countBreak++;
            bytesBuffer.add((byte) endChar);
            break;
          case 13:
            // carriageReturn \x0D
            countBreak++;
            bytesBuffer.add((byte) endChar);
            break;
          case 27:
            // escape \x1B
            countEsc = 2;
            break;
          case 33:
            // character:!
            break;
          default:
            if (countEsc == 0) {
              if (countBreak > 1) {
                int size = bytesBuffer.size();
                for (int x = 0; x < countBreak - 1; x++) {
                  bytesBuffer.remove(size - 1 - x);
                }
                countBreak = 0;
              }
              bytesBuffer.add(bytes[i]);
            } else {
              countEsc--;
            }
            break;
        }
      }
    }

    String bytesString = "";

    for (Byte byteBuffer : bytesBuffer) {
      bytesString = bytesString + (char) (byte) byteBuffer;
    }

    return bytesString;
  }

  protected void readData() {
    int bytesRead = 0;

    inputStream = telnetClient.getInputStream();

    while (telnetClient.isConnected()) {
      try {
        byte[] buffer = new byte[1024];

        bytesRead = inputStream.read(buffer);
        if (bytesRead > 0) {
          String rawData = normalizeLineEnding(buffer, '\n');
          rxQueue.add(rawData);
          // Useful for debugging
          // rxQueue.add(new String(buffer, 0, bytesRead, StandardCharsets.UTF_8));
        } else {
          try {
            Thread.sleep(SLEEP_MS);
          } catch (InterruptedException e) {
            System.err.println("InterruptedException readData:" + e.getMessage());
          }
        }
      } catch (IOException e) {
        System.err.println("Exception while reading socket:" + e.getMessage());
      }
    }
  }

  public void writeData(String data) {
    writeOutputStream(data);
  }

  private void writeOutputStream(String data) {
    try {
      outputStream.write(data.getBytes());
      outputStream.flush();
    } catch (IOException e) {
      System.err.println("Exception while writing socket:" + e.getMessage());
    }
  }

  /**
   * Closes telnet connection.
   */
  public void disposeConnection() {
    try {
      telnetClient.disconnect();
    } catch (IOException e) {
      System.err.println("Exception while disposeConnection:" + e.getMessage());
    }
  }
}
