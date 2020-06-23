package daq.usi;

import io.grpc.Server;
import io.grpc.ServerBuilder;
import java.io.IOException;
import java.util.concurrent.TimeUnit;

public class UsiServer {
  private Server server;

  private void start() throws IOException {
    /* The port on which the server should run */
    int port = 5000;
    server = ServerBuilder.forPort(port)
        .addService(new UsiImpl())
        .build()
        .start();
    System.out.println("Server started, listening on " + port);
    Runtime.getRuntime().addShutdownHook(new Thread() {
      @Override
      public void run() {
        // Use stderr here since the logger may have been reset by its JVM shutdown hook.
        System.err.println("*** shutting down gRPC server since JVM is shutting down");
        try {
          UsiServer.this.stop();
        } catch (InterruptedException e) {
          e.printStackTrace(System.err);
        }
        System.err.println("*** server shut down");
      }
    });
  }

  private void stop() throws InterruptedException {
    if (server != null) {
      server.shutdown().awaitTermination(30, TimeUnit.SECONDS);
    }
  }

  /**
   * Await termination on the main thread since the grpc library uses daemon threads.
   */
  private void blockUntilShutdown() throws InterruptedException {
    if (server != null) {
      server.awaitTermination();
    }
  }

  /**
   * Main method.
   * @param args not used.
   * @throws Exception Maybe a refactor is needed to throw more specific exceptions.
   */
  public static void main(String[] args) throws Exception {
    final UsiServer server = new UsiServer();
    server.start();
    server.blockUntilShutdown();
  }
}
