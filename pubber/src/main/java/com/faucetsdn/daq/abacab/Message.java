package com.faucetsdn.daq.abacab;

import java.util.Date;
import java.util.HashMap;
import java.util.Map;

@SuppressWarnings("unused")
public class Message {

  public static class State extends AbacabBase {
    public SystemState system = new SystemState();
    public PointSetState pointset;
  }

  public static class Config extends AbacabBase {
    public SystemConfig system;
    public PointSetState pointset;
  }

  public static class PointSet extends AbacabBase {
    public Map<String, PointData> points = new HashMap<>();
  }

  public static class System extends AbacabBase {
    public Report log;
  }

  public static class PointSetState {
    public Map<String, PointState> points = new HashMap<>();
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

  public static class PointData {
    public Object present_value;
  }

  public static class PointState {
    public String units;
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
