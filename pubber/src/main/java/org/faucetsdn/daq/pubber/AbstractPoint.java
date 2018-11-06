package org.faucetsdn.daq.pubber;

import com.faucetsdn.daq.abacab.Message.Point;

public interface AbstractPoint {

  String getName();

  Point getData();

  void updateData();

  Point getConfig();
}
