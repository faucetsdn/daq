public class Main {

  public static void main(String[] args) throws Exception {

    if (args.length != 1) {
        throw new IllegalArgumentException("Expected target ipAddress/hostname as argument");
    }

    String ipAddress = args[0];

    Certs certificate = new Certs("https://" + ipAddress);

    try {
      if (certificate.getCertificate()) {
        System.out.println("Certificate read successfully");
      } else {
        System.out.println("Certificate read failed");
      }
    } catch (Exception e) {
      System.err.println("Exception main:" + e.getMessage());
    }
  }
}
