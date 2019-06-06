public class Main {

  public static void main(String[] args) {
    if (args.length != 1) {
      throw new IllegalArgumentException("Usage: target_mac");
    }

    String macAddress = args[0];
    System.out.println("Main Started...");
    RetrieveList setupTest = new RetrieveList(macAddress);
    setupTest.startTest();
  }
}
