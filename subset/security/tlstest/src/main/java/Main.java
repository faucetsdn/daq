public class Main {

  public static void main(String[] args) throws Exception {

    if (args.length != 1) {
      throw new IllegalArgumentException("Expected target ipAddress/hostname as argument");
    }

    String ipAddress = args[0];

    Certs tlsTest = new Certs(ipAddress, 443);
    try {
      if (tlsTest.testTLSVersions()) {
        System.out.println("Certificate read successfully");
      } else {
        System.out.println("Certificate read failed");
      }
    } catch (Exception e) {
      System.err.println("Exception main:" + e.getMessage());
    }
  }
}
