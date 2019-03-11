package com.google.daq.mqtt.util;

import java.io.IOException;
import java.io.PrintStream;
import java.util.Map;
import java.util.TreeMap;
import java.util.function.BiConsumer;
import org.everit.json.schema.ValidationException;

public class ExceptionMap extends RuntimeException {

  private static final byte[] NEWLINE_BYTES = "\n".getBytes();

  final Map<String, Exception> exceptions = new TreeMap<>();

  public ExceptionMap(String description) {
    super(description);
  }

  private void forEach(BiConsumer<String, Exception> consumer) {
    exceptions.forEach(consumer);
  }

  public void throwIfNotEmpty() {
    if (!exceptions.isEmpty() || getCause() != null) {
      throw this;
    }
  }

  public void put(String key, Exception exception) {
    if (exceptions.put(key, exception) != null) {
      throw new IllegalArgumentException("Exception key already defined: " + key);
    }
  }

  public static ErrorTree format(Exception e, String indent) {
    return format(e, "", indent);
  }

  private static ErrorTree format(Throwable e, final String prefix, final String indent) {
    final ErrorTree errorTree = new ErrorTree();
    errorTree.prefix = prefix;
    errorTree.message = e.getMessage();
    final String newPrefix = prefix + indent;
    if (e instanceof ExceptionMap) {
      if (e.getCause() != null) {
        errorTree.cause = format(e.getCause(), newPrefix, indent);
      }
      ((ExceptionMap) e).forEach(
          (key, sub) -> errorTree.causes.put(key, format(sub, newPrefix, indent)));
    } else if (e instanceof ValidationException) {
      ((ValidationException) e).getCausingExceptions().forEach(
          sub -> errorTree.causes.put(sub.getMessage(), format(sub, newPrefix, indent)));
    } else if (e.getCause() != null) {
      errorTree.cause = format(e.getCause(), newPrefix, indent);
    }
    if (errorTree.causes.isEmpty()) {
      errorTree.causes = null;
    }
    return errorTree;
  }

  public static class ErrorTree {
    public String prefix;
    public String message;
    public ErrorTree cause;
    public Map<String, ErrorTree> causes = new TreeMap<>();

    public void write(PrintStream err) {
      try {
        if (message != null) {
          err.write(prefix.getBytes());
          err.write(message.getBytes());
          err.write(NEWLINE_BYTES);
        }
      } catch (IOException e) {
        throw new RuntimeException(e);
      }
      if (cause != null) {
        cause.write(err);
      }
      if (causes != null) {
        causes.forEach((key, value) -> value.write(err));
      }
    }
  }

}
