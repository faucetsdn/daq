package com.faucetsdn.daq.abacab;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

@SuppressWarnings("unused")
public class Message {
  public static class PointSet extends AbacabBase {
    public PointMap points = new PointMap();
  }

  public static class System extends AbacabBase {
    public Report log;
  }

  public static class State extends AbacabBase {
    public SystemState system = new SystemState();
    public PointSet pointset;
  }

  public static class SystemState {
    public String make_model;
    public String firmware_version;
    public boolean operational;
    public Date last_config;
    public Map<String, Report> status = new HashMap<>();
  }

  public static class Config extends AbacabBase {
    public SystemConfig system;
    public Object pointset;
  }

  public static class SystemConfig {
    public Integer report_interval_ms;
  }

  public static class Report {
    public String message;
    public String detail;
    public String category;
    public Integer level = 500;


    public Report(Exception e) {
      message = e.getMessage();
      ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
      e.printStackTrace(new PrintStream(outputStream));
      detail = outputStream.toString();
      category = e.getStackTrace()[0].getClassName();
      level = 800;
    }
  }

  public static class PointMap extends HashMap<String, Point> {
  }

  public static class Point {
    // This value is only used for a device telemetry update.
    public Object present_value;

    // These values are only used for state/config.
    public String units;
  }

  public static class AbacabBase {
    public Integer version = 1;
    public Date timestamp = new Date();
  }
}
