package com.faucetsdn.daq.abacab;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.util.Date;

public class Report {
  public String message;
  public String detail;
  public String category;
  public Integer level = 500;
  public Date timestamp = new Date();



  public Report(Exception e) {
    message = e.toString();
    ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
    e.printStackTrace(new PrintStream(outputStream));
    detail = outputStream.toString();
    category = e.getStackTrace()[0].getClassName();
    level = 800;
  }
}
