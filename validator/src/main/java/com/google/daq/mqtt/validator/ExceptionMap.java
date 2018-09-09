package com.google.daq.mqtt.validator;

import java.io.IOException;
import java.io.OutputStream;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.Callable;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.BiConsumer;
import org.everit.json.schema.ValidationException;

class ExceptionMap extends RuntimeException {

  private static final byte[] NEWLINE_BYTES = "\n".getBytes();

  final Map<String, Exception> exceptions = new ConcurrentHashMap<>();

  ExceptionMap(String description) {
    super(description);
  }

  private void forEach(BiConsumer<String, Exception> consumer) {
    exceptions.forEach(consumer);
  }

  void throwIfNotEmpty() {
    if (!exceptions.isEmpty() || getCause() != null) {
      throw this;
    }
  }

  void put(String key, Exception exception) {
    if (exceptions.put(key, exception) != null) {
      throw new IllegalArgumentException("Exception key already defined: " + key);
    }
  }

  static ErrorTree format(Exception e, String indent, OutputStream outputStream) {
    return format(e, "", indent, outputStream);
  }

  private static ErrorTree format(Throwable e, final String prefix,
      final String indent, OutputStream outputStream) {
    final ErrorTree errorTree = new ErrorTree();
    try {
      errorTree.message = e.getMessage();
      if (outputStream != null) {
        outputStream.write(prefix.getBytes());
        outputStream.write(errorTree.message.getBytes());
        outputStream.write(NEWLINE_BYTES);
      }
    } catch (IOException ioe) {
      throw new RuntimeException(ioe);
    }
    final String newPrefix = prefix + indent;
    if (e instanceof ExceptionMap) {
      if (e.getCause() != null) {
        errorTree.cause = format(e.getCause(), newPrefix, indent, outputStream);
      }
      ((ExceptionMap) e).forEach(
          (key, sub) -> errorTree.causes.put(key, format(sub, newPrefix, indent, outputStream)));
    } else if (e instanceof ValidationException) {
      ((ValidationException) e).getCausingExceptions().forEach(
          sub -> errorTree.causes.put(sub.getMessage(), simplify(format(sub, newPrefix, indent, outputStream))));
    } else if (e.getCause() != null) {
      errorTree.cause = format(e.getCause(), newPrefix, indent, outputStream);
    }
    if (errorTree.causes.isEmpty()) {
      errorTree.causes = null;
    }
    return errorTree;
  }

  /**
   * Handle special prune case when this is inserted to the map, and the 'message' field ends
   * up being redundant with the entry key.
   */
  private static ErrorTree simplify(ErrorTree format) {
    if ((format.causes == null || format.causes.size() == 0)
        && format.cause == null) {
      return new ErrorTree();
    }
    return format;
  }

  static class ErrorTree {
    public String message;
    public ErrorTree cause;
    public Map<String, ErrorTree> causes = new TreeMap<>();
  }

}
