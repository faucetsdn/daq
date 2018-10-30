package com.google.iot.bos;

import com.google.iot.bos.datafmt.AbacabMessage.Point;
import java.util.Objects;

class FauxSensor {
  private final double period;
  private final double phase;
  private final double mean;
  private final double swing;

  FauxSensor(double period, double phase, double mean, double swing) {
    this.period = period;
    this.phase = phase;
    this.mean = mean;
    this.swing = swing;
  }

  Point getReading(String deviceId) {
    Point point = new Point();
    long now = System.currentTimeMillis() + Objects.hashCode(deviceId);
    double value = Math.sin((double) now * period * 0.0001 + phase);
    point.present_value = Math.floor(value * swing * 100.0) / 100.0 + mean;
    return point;
  }
}
