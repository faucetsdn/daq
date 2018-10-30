package com.google.iot.bos.datafmt;

import java.util.Date;
import java.util.Map;
import java.util.TreeMap;

public class AbacabMessage {
  public static class PointSet extends AbacabBase {
    public Map<String, Point> points = new TreeMap<>();
  }

  public static class LogEntry extends AbacabBase {
    public Report log;
  }

  public static class State extends AbacabBase {
    public SystemState system;
    public Report status;
  }

  public static class SystemState {
    public String make_model;
    public String firmware_version;
    public boolean operational;
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
  }

  public static class Point {
    public Object present_value;
  }

  public static class AbacabBase {
    public Integer version = 1;
    public Date timestamp = new Date();
  }
}
