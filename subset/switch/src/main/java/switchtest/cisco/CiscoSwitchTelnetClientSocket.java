package switchtest.cisco;

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

public class CiscoSwitchTelnetClientSocket extends SwitchTelnetClientSocket {
  public CiscoSwitchTelnetClientSocket(
      String remoteIpAddress, int remotePort, SwitchInterrogator interrogator, boolean debug) {
    super(remoteIpAddress, remotePort, interrogator, debug);
  }

  /**
   * Continuous scan of data in the rxQueue and send to SwitchInterrogator for processing. If no
   * data can be read for 70 scans, send a new line to force something into the queue.
   */
  protected void gatherData() {
    int rxQueueCount = 0;

    int expectedLength = 1000;

    while (telnetClient.isConnected()) {
      try {
        if (rxQueue.isEmpty()) {
          Thread.sleep(100);
          rxQueueCount++;
          if (debug) {
            System.out.println("rxQueue.isEmpty:" + rxQueueCount);
            System.out.println("expectedLength:" + expectedLength);
          }
          if (rxQueueCount > 70) {
            rxQueueCount = 0;
            writeData("\n");
          }
        } else {
          String rxGathered = rxQueue.poll();
          interrogator.receiveData(rxGathered);
        }
      } catch (InterruptedException e) {
        System.err.println("InterruptedException gatherData:" + e.getMessage());
      }
    }
  }
}
