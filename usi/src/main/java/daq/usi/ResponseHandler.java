package daq.usi;

public interface ResponseHandler<T> {
  void receiveData(T data) throws Exception;
}
