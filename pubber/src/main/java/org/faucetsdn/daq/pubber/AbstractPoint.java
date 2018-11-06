package org.faucetsdn.daq.pubber;

import com.faucetsdn.daq.abacab.Message.PointData;
import com.faucetsdn.daq.abacab.Message.PointState;

public interface AbstractPoint {

  String getName();

  PointData getData();

  void updateData();

  PointState getState();
}
