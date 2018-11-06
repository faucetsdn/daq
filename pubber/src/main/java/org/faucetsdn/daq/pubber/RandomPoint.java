package org.faucetsdn.daq.pubber;

import com.faucetsdn.daq.abacab.Message.Point;

public class RandomPoint implements AbstractPoint {

  private final String name;
  private final double min;
  private final double max;
  private final Point data = new Point();
  private final Point config = new Point();

  public RandomPoint(String name, double min, double max) {
    this.name = name;
    this.min = min;
    this.max = max;
    this.config.fault = max == min;
    updateData();
  }

  @Override
  public void updateData() {
    data.present_value = Math.round(Math.random() * (max - min) + min);
  }

  @Override
  public Point getConfig() {
    return config;
  }

  @Override
  public String getName() {
    return name;
  }

  @Override
  public Point getData() {
    return data;
  }
}
