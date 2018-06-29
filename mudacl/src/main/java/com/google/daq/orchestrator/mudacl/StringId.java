package com.google.daq.orchestrator.mudacl;

public class StringId {

  private final String id;

  StringId(String id) {
    if (id == null) {
      throw new IllegalArgumentException("ID can not be null");
    }
    this.id = id;
  }

  public String toString() {
    return id;
  }

  @Override
  public int hashCode() {
    return id.hashCode();
  }

  @Override
  public boolean equals(Object other) {
    return other.getClass().isAssignableFrom(getClass())
        && other instanceof StringId
        && id.equals(((StringId) other).id);
  }
}
