public class Main {

  public static void main(String[] args) throws Exception {
    String tlsReport = "";
    Report report = new Report();

    if (args.length != 2) {
      throw new IllegalArgumentException("Expected 2 args, only " + args.length + " detected.");
    }
    String ipAddress = args[0];
    String caFile = "None".equals(args[1])?null:args[1];
    System.out.println("Args:");
    System.out.println("IP Address: " + ipAddress);
    System.out.println("CA File: " + caFile);
    //Generate the Client/Server test objects
    Server tlsServer1_0 = new Server(ipAddress, 443,"1",caFile);
    Server tlsServer1_2 = new Server(ipAddress, 443,"1.2",caFile);
    Server tlsServer1_3 = new Server(ipAddress, 443,"1.3",caFile);
    Client client = new Client(ipAddress,new int[]{443,8883},new String[]{"1.2","1.3"});
    //Client client_1_3 = new Client(ipAddress,443,"1.3");
    //Run the tests
    tlsReport += validateServerTls(tlsServer1_0);
    tlsReport += validateServerTls(tlsServer1_2);
    tlsReport += validateServerTls(tlsServer1_3);
    tlsReport += validateClientTls(client);
    //tlsReport += validateClientTls(client_1_3);
    //Generate the results
    tlsReport += ResultGenerator.generateServerResults(tlsServer1_0);
    tlsReport += ResultGenerator.generateServerResults(tlsServer1_2);
    tlsReport += ResultGenerator.generateServerResults(tlsServer1_3);
    report.writeReport(tlsReport);
  }

  public static String validateServerTls(Server tlsTest) {
    String report = "";
    try {
      report += tlsTest.validate();
    }
    catch(Exception e){
      report +="Server TLS failed\n";
      report +=e.getMessage();
    }
    finally {
      return report;
    }
  }

  public static String validateClientTls(Client client){
    String report = "";
    try {
      report += client.validate();
    }
    catch(Exception e){
      report +="Client TLS failed\n";
      report +=e.getMessage();
    }
    finally {
      return report;
    }
  }
}
