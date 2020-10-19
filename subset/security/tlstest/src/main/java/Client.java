import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonParser;

import java.io.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;

public class Client {
    private final String clientIpAddress;
    private final int[] ports;
    private final String[] tlsVersion;
    private String captureFile = "/scans/test_tls.pcap";
    private String clientReport = "";
    private int totalScans = 0;
    private int maxScans = 10;

    public Client(String clientIpAddress, int[] ports,String[] tlsVersion) {
        this.clientIpAddress = clientIpAddress;
        this.ports = ports;
        this.tlsVersion = tlsVersion;
    }

    /**
     * Scan the provided capture file and validate it's results.
     * @param captureFile Capture file to scan and validate
     * @return True indicates file contained expected traffic and could be validated.  False indicates no
     * traffic could be detected to validate.
     */
    private boolean validateCaptureFile(String captureFile,String tlsVersion){
        System.out.println("Scanning Capture File: " + captureFile);
        this.captureFile = captureFile;
        //Check all servers that have been contacted by the DUT to see
        //if they have completed a SSL/TLS handshake
        List<String> serverList = getServers(tlsVersion);
        if(serverList.size()>0){
            boolean handshakeComplete = serverList.stream().anyMatch(serverIp -> isHandshakeCompleted(serverIp,tlsVersion));
            boolean cipherValid = checkClientCiphers();
            passClient(handshakeComplete, cipherValid,tlsVersion);
            return true;
        }
        else{
            System.out.println("No client initiated TLS communication detected in capture file: " + captureFile);
            return false;
        }
    }

    /**
     * Validate all versions of TLS requested for client side communications.
     * Scan the capture file a maximum of 10 times between all versions
     * which equates to 5 minutes total wait time.  Any longer can cause
     * a module timeout.
     * @return
     */
    public String validate(){
        System.out.println("Validating Client TLS Versions...");
        for(int i = 0;i<tlsVersion.length;++i){
            System.out.println("Checking Client TLS Version: " + tlsVersion[i]);
            String tlsVersionReport = validate(tlsVersion[i]);
            clientReport += tlsVersionReport;
        }
        return clientReport;
    }

    public String validate(String tlsVersion) {
        String tlsVersionReport = "";
        try {
            tlsVersionReport += "\nGathering TLS Client " + clientIpAddress +" Information....";
            System.out.println("Validating Client TLS: " + clientIpAddress);
            //Make sure our capture file is available before even attempting this test
            File f = new File(captureFile);
            if(f.exists()) {
                System.out.println("Capture File Available: " + captureFile);
                //Scan file over a max of 5 minutes to check for valid traffic
                boolean validated = false;
                while(totalScans<maxScans && !validated){
                    ++totalScans;
                    System.out.println("Capture File Scan Attempt: " + totalScans);
                    Thread.sleep(30000);//Pause 30 seconds between scans
                    validated = validateCaptureFile(captureFile,tlsVersion);
                }
                if(!validated) {
                    skipClient("No client initiated TLS communication detected",tlsVersion);
                }
            }
            else{
                skipClient("Capture file required for TLS validation not present: " + captureFile,tlsVersion);
            }
        }
        catch(Exception e){
            e.printStackTrace();
        }
        finally{
            tlsVersionReport += "\nTLS Client Information Complete.";
            return tlsVersionReport;
        }
    }

    private boolean checkClientCiphers(){
        if(tlsVersion.equals("1.3")){
            System.out.println("No Cipher check required for TLS 1.3");
            return true;
        }
        List<String> ciphers = getClientCiphers();
        boolean ecdh = isCipherSupported(ciphers,"ECDH");
        boolean ecdsa = isCipherSupported(ciphers,"ECDSA");
        if(ecdh) {
            System.out.println("ECDH Client Cipher Detected: " + ecdh);
        }
        if(ecdh) {
            System.out.println("ECDSA Client Cipher Detected: " + ecdsa);
        }
        return ecdh && ecdsa;
    }

    /**
     * Inspect the capture file for all hello messages from the client device (DUT)
     * @return List<String> List of all client Hello packets resolved
     */
    private List<String> getClientCiphers(){
        String[] command = new String[]{"tshark", "-r", captureFile,"-Vx",
                "-Y", "ssl.handshake.ciphersuites and ip.src=="+clientIpAddress+""};
        String procRes = runCommand(command,true);
        String[] lines = procRes.split("\n");
        System.out.println("Cipher Resp Size: " + lines.length);
        List<String> cipherList = new ArrayList<String>();
        Arrays.stream(lines).forEach(line->{
            if(line.contains("Cipher Suite:")){
                line = line.trim();
                if(!cipherList.contains(line)){
                    System.out.println("Unique Cipher: " + line);
                    cipherList.add(line);
                }
            }
        });
        return cipherList;
    }

    /**
     * Resolve all the servers that the DUT has reached out to over SSL/TLS
     * @return List of IP addresses of all the servers resolved
     */
    private List<String> getServers(String tlsVersion){
        JsonArray clientHelloPackets = getClientHelloPackets(tlsVersion);
        System.out.println("Client Hello Messages Resolved: " + clientHelloPackets.size());
        List<String> serverList = new ArrayList();
        for (int i = 0; i < clientHelloPackets.size(); ++i) {
            String serverIp = clientHelloPackets.get(i).getAsJsonObject()
                    .getAsJsonObject("_source")
                    .getAsJsonObject("layers")
                    .getAsJsonObject("ip")
                    .getAsJsonPrimitive("ip.dst").getAsString();
            if (!serverList.contains(serverIp) && !serverIp.equals(clientIpAddress)) {
                serverList.add(serverIp);
                System.out.println("Unique Server IP Detected: " + serverIp);
            }
        }
        return serverList;
    }

    /**
     * Inspect the capture file for all hello messages from the client device (DUT)
     * on specified port.
     * 0x0303 -> TLS 1.2
     * 0x0304 -> TLS 1.3
     * @return JsonArray of all client Hello packets resolved
     */
    private JsonArray getClientHelloPackets(String tlsVersion){
        List<String> commands = new LinkedList<String>();
        commands.add("tshark");
        commands.add("-r");
        commands.add(captureFile);
        commands.add("-T");
        commands.add("json");
        commands.add("ssl.handshake.type==1");
        commands.add("and");
        commands.add("ip.src=="+clientIpAddress);
        commands.add("and");
        commands.add(getPortsFilter());
        commands.add("and");
        if(tlsVersion == "1.2"){
            commands.add("ssl.handshake.version==0x0303");
        }
        else{
            commands.add("tls.handshake.extensions.supported_version==0x0304");
        }
        String procRes = runCommand(commands.toArray(new String[0]),false);
        //The process can potentially get run as root so account for
        //possible nuisance warning messages that mess up the json packet
        procRes = procRes.substring(procRes.indexOf('['));
        JsonElement e = JsonParser.parseString(procRes);
        return e.getAsJsonArray();
    }

    private String getPortsFilter(){
        StringBuilder sb  = new StringBuilder();
        sb.append("(");
        for(int i = 0;i<ports.length;++i){
            sb.append(i>0?" or ":"");
            sb.append("tcp.port=="+ports[i]);
        }
        sb.append(")");
        return sb.toString();
    }

    /**
     * Inspect the capture file for completed client/server SSL/TLS handshakes
     * ssl.handshake.type==14 -> ServerHelloDone indicating handshake has completed for TLS 1.2
     * ssl.handshake.type==2 -> ServerHello indicating handshake has completed for TLS 1.3
     *
     * @param serverIp IP address for the server side of the connection
     * @return True when a completed handshake can be detected for the server and client
     */
    private boolean isHandshakeCompleted(String serverIp,String tlsVersion){
        System.out.println("Checking handshake completion for: " + serverIp+"->"+clientIpAddress);
        String[] command;
        if(tlsVersion.equals("1.2")){
            command = handshakeCompleteMessageTls1_2(serverIp);
        }
        else{
            command = handshakeCompleteMessageTls1_3(serverIp);
        }
        boolean completed = runCommand(command,false).length()>0;
        if(completed){
            System.out.println("Handshake Completed for: " + serverIp + "->" + clientIpAddress);
        }
        else{
            System.out.println("Handshake not completed for: " + serverIp + "->" + clientIpAddress);
        }
        return completed;
    }

    /**
     * Create the wireshark filter needed to find completed TLS 1.2 handshakes
     *
     * ssl.handshake.type==14 -> ServerHelloDone indicating handshake has completed for TLS 1.2
     * @param serverIp IP address for the server side of the connection
     * @return
     */
    private String[] handshakeCompleteMessageTls1_2(String serverIp){
        return new String[]{"tshark",
                "-r",
                captureFile,
                "ssl.handshake.type==14",
                "and",
                "ip.src=="+serverIp,
                " and ",
                "ip.dst=="+clientIpAddress,
                "and",
                getPortsFilter()
        };
    }

    /**
     * Create the wireshark filter needed to find completed TLS 1.3 handshakes
     *
     * ssl.handshake.type==2 -> ServerHello indicating handshake has completed for TLS 1.3
     * @param serverIp IP address for the server side of the connection
     * @return
     */
    private String[] handshakeCompleteMessageTls1_3(String serverIp){
        return new String[]{"tshark",
                "-r",
                captureFile,
                "ssl.handshake.type==2",
                "and",
                "ip.src=="+serverIp,
                " and ",
                "ip.dst=="+clientIpAddress,
                "and",
                getPortsFilter()
        };
    }

    private boolean isCipherSupported(List<String> cipherList, String cipher ){
        return cipherList.stream().anyMatch(s -> s.contains(cipher));
    }

    private void passClient(boolean handshake,boolean cipherValid,String tlsVersion) {
        if (handshake && cipherValid) {
            clientReport +=
                    "\nRESULT pass security.tls.v"
                            +  tlsVersion.replace(".","_")
                            + "_client"
                            + " Client/Server completed handshake and ECDH/ECDSA supported ciphers.";
        } else {
            clientReport +=
                    "\nRESULT fail security.tls.v"
                            +  tlsVersion.replace(".","_")
                            + "_client";
            clientReport+=handshake?"":" No completed SSL/TLS handshake detected.";
            clientReport+=cipherValid?"":" Cipher could not be validated.";
        }
    }

    private void skipClient(String skipMessage,String tlsVersion) {
        clientReport +=
                "\nRESULT skip security.tls.v"
                        +  tlsVersion.replace(".","_")
                        + "_client "
                        + skipMessage;
    }

    private static String runCommand(String[] command, boolean useRawData){
        ProcessBuilder processBuilder = new ProcessBuilder();
        processBuilder.command(command);
        try {
            processBuilder.redirectErrorStream(true);
            Process process = processBuilder.start();

            BufferedReader reader =
                    new BufferedReader(new InputStreamReader(process.getInputStream()));
            StringBuffer sb = new StringBuffer();
            String line;
            while ((line = reader.readLine()) != null) {
                if(useRawData){
                    if(sb.length()>0){
                        sb.append("\n");
                    }
                    sb.append(line);
                }
                else{
                    sb.append(line.trim());
                }
            }
            process.waitFor();
            String result = sb.toString();
            return result;
        } catch (IOException e) {
            e.printStackTrace();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        return "";
    }
}
