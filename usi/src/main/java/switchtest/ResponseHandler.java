package switchtest;

public interface ResponseHandler<T> {
    void receiveData(T data) throws Exception;
}
