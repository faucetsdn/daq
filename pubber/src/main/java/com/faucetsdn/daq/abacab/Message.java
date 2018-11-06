package com.faucetsdn.daq.abacab;

import java.util.Date;
import java.util.HashMap;
import java.util.Map;

@SuppressWarnings("unused")
public class Message {

  public static class State extends AbacabBase {
    public SystemState system = new SystemState();
    public PointSetDesc pointset;
  }

  public static class Config extends AbacabBase {
    public SystemConfig system;
    public PointSetDesc pointset;
  }

  public static class PointSet extends AbacabBase {
    public PointMap points = new PointMap();
  }

  public static class System extends AbacabBase {
    public Report log;
  }

  public static class PointSetDesc {
    public PointMap points = new PointMap();
  }

  public static class SystemState {
    public String make_model;
    public Bundle firmware = new Bundle();
    public boolean operational;
    public Date last_config;
    public Map<String, Report> statuses = new HashMap<>();
  }

  public static class SystemConfig {
    public Integer report_interval_ms;
  }

  public static class PointMap extends HashMap<String, Point> {
  }

  public static class Point {
    // This value is only used for a device telemetry update.
    public Object present_value;

    // These values are only used for state/config.
    public Boolean fault;
  }

  public static class Bundle {
    public String version;
  }

  public static class AbacabBase {
    public Integer version = 1;
    public Date timestamp = new Date();
  }
}
