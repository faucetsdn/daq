package switchtest;

/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

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

public abstract class SwitchTelnetClientSocket implements TelnetNotificationHandler, Runnable {
  protected TelnetClient telnetClient = null;
  protected SwitchInterrogator interrogator;

  protected String remoteIpAddress = "";
  protected int remotePort = 23;

  protected InputStream inputStream;
  protected OutputStream outputStream;

  protected Queue<String> rxQueue = new LinkedList<>();

  protected Thread readerThread;
  protected Thread gatherThread;

  protected boolean debug = false;

  public SwitchTelnetClientSocket(
      String remoteIpAddress, int remotePort, SwitchInterrogator interrogator, boolean debug) {
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
        Thread.sleep(100);
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

  protected abstract void gatherData();

  /**
   * * Callback method called when TelnetClient receives an option negotiation command.
   *
   * @param negotiation_code - type of negotiation command received (RECEIVED_DO, RECEIVED_DONT,
   *     RECEIVED_WILL, RECEIVED_WONT, RECEIVED_COMMAND)
   * @param option_code - code of the option negotiated *
   */
  public void receivedNegotiation(int negotiation_code, int option_code) {
    String command = null;
    switch (negotiation_code) {
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
        command = Integer.toString(negotiation_code); // Should not happen
        break;
    }
    System.out.println("Received " + command + " for option code " + option_code);
  }

  private void addOptionHandlers() {
    TerminalTypeOptionHandler terminalTypeOptionHandler =
        new TerminalTypeOptionHandler("VT100", false, false, true, false);

    EchoOptionHandler echoOptionHandler = new EchoOptionHandler(false, false, false, false);

    SuppressGAOptionHandler suppressGAOptionHandler =
        new SuppressGAOptionHandler(true, true, true, true);

    try {
      telnetClient.addOptionHandler(terminalTypeOptionHandler);
      telnetClient.addOptionHandler(echoOptionHandler);
      telnetClient.addOptionHandler(suppressGAOptionHandler);
    } catch (InvalidTelnetOptionException e) {
      System.err.println(
          "Error registering option handlers InvalidTelnetOptionException: " + e.getMessage());
    } catch (IOException e) {
      System.err.println("Error registering option handlers IOException: " + e.getMessage());
    }
  }

  private String normalizeLineEnding(byte[] bytes, char endChar) {
    String data = new String(bytes);

    List<Byte> bytesBuffer = new ArrayList<Byte>();

    int countBreak = 0;
    int countESC = 0;

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
            countESC = 2;
            break;
          case 33:
            // character:!
            break;
          default:
            if (countESC == 0) {
              if (countBreak > 1) {
                int size = bytesBuffer.size();
                for (int x = 0; x < countBreak - 1; x++) {
                  bytesBuffer.remove(size - 1 - x);
                }
                countBreak = 0;
              }
              bytesBuffer.add(bytes[i]);
            } else {
              countESC--;
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
            Thread.sleep(100);
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
    Runnable runnable =
        () -> {
          writeOutputStream(data);
        };
    Thread writeThread = new Thread(runnable);
    writeThread.start();
  }

  private void writeOutputStream(String data) {
    try {
      outputStream.write(data.getBytes());
      // Useful for debugging
      // outputStream.write(data.getBytes(StandardCharsets.UTF_8));
      outputStream.flush();
    } catch (IOException e) {
      System.err.println("Exception while writing socket:" + e.getMessage());
    }
  }

  public void disposeConnection() {
    try {
      telnetClient.disconnect();
    } catch (IOException e) {
      System.err.println("Exception while disposeConnection:" + e.getMessage());
    }
  }
}
