package switchtest.allied;

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

import switchtest.SwitchInterrogator;
import switchtest.SwitchTelnetClientSocket;

public class AlliedSwitchTelnetClientSocket extends SwitchTelnetClientSocket {
  public AlliedSwitchTelnetClientSocket(
      String remoteIpAddress, int remotePort, SwitchInterrogator interrogator, boolean debug) {
    super(remoteIpAddress, remotePort, interrogator, debug);
  }

  protected void gatherData() {
    StringBuilder rxData = new StringBuilder();
    String rxGathered = "";

    boolean parseFlag = false;

    int count = 0;
    int flush = 0;
    int rxQueueCount = 0;
    int rxTempCount = 0;
    int expectedLength = 1000;
    int requestFlag = 0;

    while (telnetClient.isConnected()) {
      try {

        if (rxQueue.isEmpty()) {
          Thread.sleep(100);
          rxQueueCount++;
          if (debug) {
            System.out.println("rxQueue.isEmpty:" + rxQueueCount);
            System.out.println("expectedLength:" + expectedLength);
            System.out.println("requestFlag:" + requestFlag);
          }
          if (rxQueueCount > 70) {
            rxQueueCount = 0;
            writeData("\n");
          }
        } else {
          rxQueueCount = 0;
          String rxTemp = rxQueue.poll();
          if (rxTemp.equals("")) {
            Thread.sleep(100);
            rxTempCount++;
            if (debug) {
              System.out.println("rxTemp.equals:" + rxTempCount);
            }
          } else if (rxTemp.indexOf("--More--") > 0) {
            Thread.sleep(20);
            writeData("\n");

            if (debug) {
              System.out.println("more position:" + rxTemp.indexOf("--More--"));
              System.out.println("rxTemp.length" + rxTemp.length() + "rxTemp pre:" + rxTemp);
              // Useful for debugging
              // char[] tempChar = rxTemp.toCharArray();
              // for(char temp:tempChar) {
              //        System.out.println("tempChar:"+(byte)temp);
              // }
            }

            rxTemp = rxTemp.substring(0, rxTemp.length() - 9);

            if (debug) {
              System.out.println("rxTemp.length" + rxTemp.length() + "rxTemp post:" + rxTemp);
            }

            rxData.append(rxTemp);
          } else {
            rxQueueCount = 0;
            rxTempCount = 0;
            rxData.append(rxTemp);
            rxGathered = rxData.toString();
            System.out.println(
                java.time.LocalTime.now()
                    + "rxDataLen:"
                    + rxGathered.length()
                    + "rxData:"
                    + rxGathered);

            int position = -1;

            int charLength = 1;
            int beginPosition = 0;
            System.out.println("count is:" + count);

            String[] loginExpected = interrogator.login_expected;
            int[] loginExpectedLength = {5, 5, 40};

            String hostname = interrogator.getHostname();
            requestFlag = ((AlliedTelesisX230) interrogator).getRequestFlag() - 1;

            boolean[] requestFlagIndexOf = {false, false, false, true, false};
            String[] requestFlagExpected = {hostname, hostname, hostname, "end", hostname};
            int[] requestFlagExpectedLength = {600, 600, 50, 1000, 290};
            int[] requestFlagCharLength = {
              hostname.length() + 1, hostname.length() + 1, hostname.length() + 1, 3, -1
            };
            int[] requestFlagFlush = {0, 0, 0, 15, 0};

            // login & enable process
            if (count < 3) {
              position = rxGathered.indexOf(loginExpected[count]);
              if (position >= 0) {
                expectedLength = loginExpectedLength[count];
                if (count == 2) {
                  interrogator.setUserAuthorised(true);
                }
                count++;
              }
            } else if ((count % 2) != 0) {
              position = rxGathered.indexOf(interrogator.getHostname());
              if (position >= 0) {
                interrogator.setUserEnabled(true);
                expectedLength = 2;
                charLength = interrogator.getHostname().length() + 1;
                flush = 0;
                beginPosition = 0;
                count++;
              }
            } else {
              position =
                  findPosition(
                      rxGathered,
                      requestFlagExpected[requestFlag],
                      requestFlagIndexOf[requestFlag]);
              if (position >= 0) {
                expectedLength = requestFlagExpectedLength[requestFlag];
                charLength = requestFlagCharLength[requestFlag];
                flush = requestFlagFlush[requestFlag];
                if (rxGathered.length() >= expectedLength) {
                  beginPosition = 4;
                  count++;
                }
              }
            }
            System.out.println("Position: " + position);
            System.out.println("RxGathered: " + rxGathered.length());
            System.out.println("Expected Length: " + expectedLength);
            System.out.println("rxGathered: " + rxGathered);

            if (position >= 0 && rxGathered.length() >= expectedLength) {
              rxGathered = rxGathered.substring(beginPosition, position + charLength);
              System.out.println(
                  java.time.LocalTime.now()
                      + "rxGatheredLen:"
                      + rxGathered.length()
                      + "rxGathered:"
                      + rxGathered);
              rxData.delete(0, position + charLength + flush);

              interrogator.receiveData(rxGathered);
            }
          }
        }
      } catch (InterruptedException e) {
        System.err.println("InterruptedException gatherData:" + e.getMessage());
      }
    }
  }

  protected int findPosition(String rxGathered, String value, boolean indexOf) {
    int position = -1;
    if (indexOf) {
      position = rxGathered.indexOf(value);
    } else {
      position = rxGathered.lastIndexOf(value);
    }
    return position;
  }
}
