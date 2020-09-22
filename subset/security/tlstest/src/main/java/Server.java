import org.bouncycastle.jce.provider.JDKKeyPairGenerator;
import org.bouncycastle.openssl.PEMWriter;

import java.io.*;
import java.net.InetSocketAddress;
import java.security.KeyManagementException;
import java.security.NoSuchAlgorithmException;
import java.security.PublicKey;
import java.security.cert.*;
import java.security.interfaces.DSAPublicKey;
import java.security.interfaces.ECPublicKey;
import java.security.interfaces.RSAPublicKey;
import javax.crypto.Cipher;
import javax.net.ssl.*;

public class Server {
  private final String ipAddress;
  private final int port;
  private final String tlsVersion;
  private final String caFile;
  private static final int CONNECT_TIMEOUT_MS = 10000;

  private CertificateStatus serverCertStatus = CertificateStatus.CERTIFICATE_INVALID;
  private KeyLengthStatus serverKeyLengthStatus = KeyLengthStatus.PUBLIC_KEY_INVALID_LENGTH;
  private CertificateSignatureStatus sigStatus = CertificateSignatureStatus.CERTIFICATE_SELF_SIGNED;
  private CipherStatus cipherStatus = CipherStatus.INVALID;

  private String certificateReport = "";
  boolean skip = false;

  public Server(String ipAddress, int port,String tlsVersion,String caFile) {
    this.ipAddress = ipAddress;
    this.port = port;
    this.tlsVersion = tlsVersion;
    this.caFile = caFile;
  }

  public String validate(){
    try {
      appendReport("Gathering TLS " + tlsVersion + " Server Information....");
      testTlsVersion();
    }
    catch(Exception e){
      System.out.println("Unexpected Error");
      e.printStackTrace();
    }
    finally {
      appendReport("TLS " + tlsVersion + " Server Information Complete.\n\n");
      return certificateReport;
    }
  }

  public TestResult getServerResult(){
    if(skip){
      return TestResult.SKIP;
    }
    else if((serverKeyLengthStatus == KeyLengthStatus.PUBLIC_KEY_RSA_VALID_LENGTH
            || serverKeyLengthStatus == KeyLengthStatus.PUBLIC_KEY_EC_VALID_LENGTH)
            && (cipherStatus == CipherStatus.VALID || cipherStatus == CipherStatus.SKIPPED)){
      return TestResult.PASS;
    }
    else{
      return TestResult.FAIL;
    }
  }

  public TestResult getCertificateResult(){
    if(skip){
      return TestResult.SKIP;
    }
    else if(serverCertStatus == CertificateStatus.CERTIFICATE_VALID &&
            sigStatus == CertificateSignatureStatus.CERTIFICATE_CA_SIGNED){
      return TestResult.PASS;
    }
    else{
      return TestResult.FAIL;
    }
  }

  public CipherStatus getCipherStatus(){
    return cipherStatus;
  }

  public CertificateStatus getServerCertStatus(){
    return serverCertStatus;
  }

  public KeyLengthStatus getServerKeyLengthStatus(){
    return serverKeyLengthStatus;
  }

  public CertificateSignatureStatus getSigStatus(){
    return sigStatus;
  }

  public String getTlsVersion(){
    return tlsVersion;
  }

  /**Append the message to the report object and add a new line before
   * the message
   *
   * @param message String message to append
   */
  public void appendReport(String message){
    certificateReport += "\n"+message;
  }

  private void testTlsVersion() throws Exception {
    SSLSocket socket;
    try {
      // Attempt to open an SSL Socket at the TLS version specified
      socket = makeSSLSocket(ipAddress, port, "TLSv" + tlsVersion);
    } catch (Exception e) {
      appendReport("TLS " + tlsVersion + "Server Implementation Skipping Test, could not open connection");
      System.out.println("TLSv" + tlsVersion + " Failed: " + e.getMessage());
      e.printStackTrace();
      skip = true;
      return;
    }

    // Validate Server Certificates While using specified TLS version
    try {
      Certificate[] certificates = getServerCertificates(socket);
      serverKeyLengthStatus = validateKeyLength(certificates);
      serverCertStatus = validateCertificates(certificates);
      sigStatus = validateSignature(certificates);
      cipherStatus = validateCipher(certificates);

    } catch (SSLHandshakeException e) {
      System.out.println("SSLHandshakeException: Unable to complete handshake:" + e.getMessage());
      e.printStackTrace();
      skip = true;
    } catch (Exception e) {
      System.out.println("Certificate Validation Failed: " + e.getMessage());
      e.printStackTrace();
    }
  }

  /**
   * Validate the Cipher while using specified TLS Version.
   *
   * Skip - TLS 1.3 or RSA Public Key have no cipher requirement
   * Pass - If EC Public Key ECDH and ECDSA are supported in cipher
   * Fail - If EC Public Key and ECDH and ECDSA are not supported in cipher
   * @param certificates Array of all certificates provided with no cipher
   *                     restrictions on the connection
   * @return
   */
  private CipherStatus validateCipher(Certificate[] certificates ) {
    try {
      appendReport("\nValidating Cipher...");
      if(tlsVersion.equals("1.3")){
        appendReport("No Cipher check required for TLS 1.3");
        return CipherStatus.SKIPPED;
      }
      for(int i = 0;i<certificates.length;++i){
        PublicKey key = certificates[i].getPublicKey();
        if(key instanceof ECPublicKey){
          String cipher = getPreferredCipher();
          if(cipher!=null){
            boolean ecdh = cipher.toUpperCase().contains("ECDH");
            if (ecdh) {
              appendReport("Cipher Suite ECDH present.");
            } else {
              appendReport("FAIL: Cipher Suite ECDH NOT present.");
            }
            boolean ecdhsa = cipher.toUpperCase().contains("ECDSA");
            if (ecdhsa) {
              appendReport("Cipher Suite ECDSA present.");
            } else {
              appendReport("FAIL: Cipher Suite ECDSA NOT present.");
            }
            appendReport("Cipher Validated.");
            return ecdh&&ecdhsa?CipherStatus.VALID:CipherStatus.INVALID;
          }
        }
      }
      return CipherStatus.SKIPPED;//No ECPublic Key detected, skip
    } catch (Exception e) {
      appendReport("Cipher Validation Failed: " + e.getMessage());
      System.out.println("Cipher Validation Failed: " + e.getMessage());
      e.printStackTrace();
      return CipherStatus.INVALID;
    }
  }

  private String getPreferredCipher(){
    String cipher = null;
    try{
    SSLSocket socket = makeSSLSocket(ipAddress, port, "TLSv" + tlsVersion);
    //socket.setEnabledCipherSuites(getSupportedCiphers());
    cipher = getSessionCipher(socket);
    appendReport("Cipher:" + cipher);
    return cipher;
    }
    catch(Exception e){
      appendReport("Failed to resolve cipher: " + e.getMessage());
      e.printStackTrace();
    }
    return cipher;
  }

  private KeyLengthStatus validateKeyLength(Certificate[] certificates) {
    appendReport("Checking Public Key Length...");
    KeyLengthStatus keyLengthStatus = KeyLengthStatus.PUBLIC_KEY_INVALID_LENGTH;
    if(getTlsVersion().equals("1") || getTlsVersion().equals("1.2")){
      keyLengthStatus = validateKeyLengthRSAorEC(certificates);
    }
    else if(getTlsVersion().equals("1.3")){
      keyLengthStatus = validateKeyLengtTLS1_3(certificates);
    }
    else{
      appendReport("Public key validation failed for unsupported TLS version: " + tlsVersion);
    }
    appendReport(ResultGenerator.getKeyLengthStatusMessage(keyLengthStatus));
    appendReport("Public Key Length Checked.");
    return keyLengthStatus;
  }

  private KeyLengthStatus validateKeyLengtTLS1_3(Certificate[] certificates){
    KeyLengthStatus keyLengthStatus = KeyLengthStatus.PUBLIC_KEY_INVALID_LENGTH;
    for (Certificate certificate : certificates) {
      if (certificate instanceof X509Certificate) {
        int minKeySize = -1;
        int keyLength = 0;
        X509Certificate x509Certificate = (X509Certificate) certificate;
        // Check the public key bit length is at least 2048
        PublicKey key = x509Certificate.getPublicKey();
        appendReport("Validating Public Key\n " + key);
        if (key instanceof RSAPublicKey) {
          minKeySize = 2048;
          keyLength = ((RSAPublicKey) key).getModulus().bitLength();
          appendReport("RSA Key Length: " + keyLength);
        }
        else if(key instanceof ECPublicKey){
          minKeySize = 224;
          keyLength = ((ECPublicKey)key).getParams().getOrder().bitLength();
          appendReport("EC Key Length: " + keyLength);
        }
        else{
          appendReport("Public Key not supported: " + key);
        }
        if (keyLength >= minKeySize && minKeySize>0) {
          if(key instanceof RSAPublicKey){
            keyLengthStatus = KeyLengthStatus.PUBLIC_KEY_RSA_VALID_LENGTH;
          }
          else if(key instanceof ECPublicKey){
            keyLengthStatus = KeyLengthStatus.PUBLIC_KEY_EC_VALID_LENGTH;
          }
        }
      }
    }
    return keyLengthStatus;
  }


  private KeyLengthStatus validateKeyLengthRSAorEC(Certificate[] certificates){
    KeyLengthStatus keyLengthStatus = KeyLengthStatus.PUBLIC_KEY_INVALID_LENGTH;
    for (Certificate certificate : certificates) {
      if (certificate instanceof X509Certificate) {
        int minKeySize = -1;
        int keyLength = 0;
        X509Certificate x509Certificate = (X509Certificate) certificate;
        // Check the public key bit length is at least 2048
        PublicKey key = x509Certificate.getPublicKey();
        appendReport("Validating Public Key\n " + key);
        if (key instanceof RSAPublicKey) {
          minKeySize = 2048;
          keyLength = ((RSAPublicKey) key).getModulus().bitLength();
          appendReport("RSA Key Length: " + keyLength);
        }
        else if(key instanceof ECPublicKey){
          minKeySize = 224;
          keyLength = ((ECPublicKey)key).getParams().getOrder().bitLength();
          appendReport("EC Key Length: " + keyLength);
        }
        else{
          appendReport("Public Key not supported: " + key);
        }
        if (keyLength >= minKeySize && minKeySize > 0) {
          if (key instanceof RSAPublicKey) {
            keyLengthStatus = KeyLengthStatus.PUBLIC_KEY_RSA_VALID_LENGTH;
          } else if (key instanceof ECPublicKey) {
            keyLengthStatus = KeyLengthStatus.PUBLIC_KEY_EC_VALID_LENGTH;
          }
        }
      }
    }
    return keyLengthStatus;
  }

  private CertificateStatus validateCertificates(Certificate[] certificates) {
    appendReport("Checking Certificate...");
    for (Certificate certificate : certificates) {

      if (certificate instanceof X509Certificate) {
        try {
          appendReport("Certificate:\n" + certificate);
          // Check the expiration date
          X509Certificate x509Certificate = (X509Certificate) certificate;
          x509Certificate.checkValidity();
          appendReport("Certificate is active for current date.\n\n");
          return CertificateStatus.CERTIFICATE_VALID;
        } catch (CertificateExpiredException cee) {
          appendReport("Certificate is expired.");
          return CertificateStatus.CERTIFICATE_EXPIRED;
        } catch (CertificateNotYetValidException e) {
          appendReport("Certificate not yet valid.");
          return CertificateStatus.CERTIFICATE_NOT_YET_VALID;
        }
      } else {
        appendReport("Unsupported certificate type.");
        return CertificateStatus.CERTIFICATE_TYPE_UNSUPPORTED;
      }
    }
    appendReport("Certificate Checked.");
    return CertificateStatus.CERTIFICATE_INVALID;
  }

  private  String combineCerts(Certificate[] certificates){
    String certChain = "";
    for (Certificate certificate : certificates) {
      if (certificate instanceof X509Certificate) {
        try {
          X509Certificate  x509Certificate = (X509Certificate) certificate;
          String pem = convertToBase64PEMString(x509Certificate);
          certChain+=pem;
        } catch (Exception e) {
          e.printStackTrace();
        }
      }
    }
    return certChain ;
  }

  private CertificateSignatureStatus validateSignature(Certificate[] certificates) {
    appendReport("Checking Certificate Signature...");
    System.out.println("CA File: " + caFile);
    appendReport("Certificates found: " + certificates.length);
    try {
      File certFile = writePemFile(certificates, tlsVersion + "_cert.pem");
      File caFile = resolveCAFile();
      System.out.println("CA file resolved");
      if(caFile!=null){
        System.out.println("CA File exists: " + caFile.exists());
        String[] cmd = new String[]{"openssl","verify","-CAfile",caFile.getAbsolutePath(),certFile.getAbsolutePath()};
        String procResp = runCommand(cmd,true).trim();
        appendReport("Certificate Validation\n" + procResp);
        System.out.println("CA Validation Response: " + procResp);
        if(procResp.equals(certFile.getAbsolutePath()+": OK")){
          System.out.println("Certificate Signature Validated");
          appendReport("Certificate Signature Validated");
          return CertificateSignatureStatus.CERTIFICATE_CA_SIGNED;
        }
        else{
          System.out.println("Certificate Signature Validation Failed");
          appendReport("Certificate Signature Validation Failed");
        }
      }
      else{
        System.out.println("CA File not  resolved");
        appendReport("CA File not Resolved:");
      }
    }
    catch(Exception e){
      System.out.println("Certificate Signature Validation Error: " + e.getMessage());
      e.printStackTrace();
    }
    appendReport("Certificate Signature Checked.");
    return CertificateSignatureStatus.CERTIFICATE_SELF_SIGNED;
  }

  /**
   * Write a Pem File to the temp directory
   *
   * @param x509Cert X.509 Certificate to write in PEM encoding
   * @param fileName Name of the file to be written to the tmp directory
   * @throws Exception
   */
  private File writePemFile(Certificate x509Cert,String fileName) throws Exception{
    File tmp = new File("tmp").exists()?new File("tmp"):new File("/root/tmp");
    //File tmp = new File("tmp");
    if(!tmp.exists()){
      tmp.mkdirs();
    }
    File f = new File("tmp/"+fileName);
    System.out.println("Writing PEM to " + f.getAbsolutePath());
    String pem = convertToBase64PEMString(x509Cert);
    FileWriter fw = new FileWriter(f.getAbsolutePath());
    fw.write(pem);
    fw.close();
    System.out.println("PEM File Written");
    return f;
  }

  /**
   * Combine all certificates and write a PEM File to the temp directory
   * @param certificates Array of X.509 Certificates  to combine and write in PEM encoding
   * @param fileName Name of the file to be written to the tmp directory
   * @throws Exception
   * @return
   */
  private File writePemFile(Certificate[] certificates,String fileName) throws Exception{
    //Tmp directory location is different based on context so we'll check where we're at
    File tmp= new File("tmp/").exists()?new File("tmp/"):new File("/root/tmp/");
    if(!tmp.exists()){
      tmp.mkdirs();
    }
    File f = new File("tmp/"+fileName);
    System.out.println("Writing PEM to " + f.getAbsolutePath());
    String pem = combineCerts(certificates);
    FileWriter fw = new FileWriter(f.getAbsolutePath());
    fw.write(pem);
    fw.close();
    System.out.println("PEM File Written");
    return f;
  }

  private File resolveCAFile(){
    System.out.println("Resolving CA File...");
    File caFile = resolveCAFromFile();
    if(caFile!=null){
      if(caFile.exists()){
        return caFile;
      }
    }
    return null;
  }

  /**
   * Read the CA file from the device folder(/config/device)
   * @return
   */
  private File resolveCAFromFile(){
    System.out.println("Resolving CA from File: " + caFile);
    File f = null;
    if(caFile!=null){
      f = new File("/config/device/"+caFile);
    }
    return f;
  }

  /**
   * Converts a {@link X509Certificate} instance into a Base-64 encoded string (PEM format).
   *
   * @param x509Cert A X509 Certificate instance
   * @return PEM formatted String
   * @throws CertificateEncodingException
   */
  public String convertToBase64PEMString(Certificate x509Cert) throws IOException {
    StringWriter sw = new StringWriter();
    try (PEMWriter pw = new PEMWriter(sw)) {
      pw.writeObject(x509Cert);
    }
    return sw.toString();
  }

  /**
   * Creates a trust manager to accept all certificates. This is required since we need this test to
   * be able to connect to any device and can't know anything about the certificates before hand.
   *
   * @return A valid TrustManager which accepts all valid X509Certificates
   */
  private TrustManager[] trustAllManager() {
    // Create a trust manager that does not validate certificate chains
    return new TrustManager[] {
      new X509TrustManager() {
        public java.security.cert.X509Certificate[] getAcceptedIssuers() {
          return null;
        }

        public void checkClientTrusted(X509Certificate[] certs, String authType) {}

        public void checkServerTrusted(X509Certificate[] certs, String authType) {}
      }
    };
  }

  /**
   * Attemps to complete the SSL handshake and retrieve the Server Certificates. Server certificates
   * in this context refers to the device being tested.
   *
   * @param socket The SSLSocket which connects to the device for testing
   * @throws Exception
   */
  private Certificate[] getServerCertificates(SSLSocket socket) throws IOException {
    socket.startHandshake();
    return socket.getSession().getPeerCertificates();
  }

  /**
   * Attemps to complete the SSL handshake and retrieve the Cipher Used.
   *
   * @param socket The SSLSocket which connects to the device for testing
   * @throws Exception
   */
  private String getSessionCipher(SSLSocket socket) throws IOException {
    socket.startHandshake();
    return socket.getSession().getCipherSuite();
  }

  /**
   * @param host This is the host IP address of the device being tested
   * @param port This is teh Port of the SSL connection for the device being tested.
   * @param protocol The SSL protocol to be tested.
   * @return SSLSocket which supports only the SSL protocol defined.
   * @throws Exception
   */
  private SSLSocket makeSSLSocket(String host, int port, String protocol)
      throws NoSuchAlgorithmException, KeyManagementException, IOException {
    SSLSocketFactory factory = makeSSLFactory(trustAllManager(), protocol);
    SSLSocket socket = (SSLSocket)factory.createSocket();
    socket.connect(new InetSocketAddress(host, port), CONNECT_TIMEOUT_MS);
    socket.setEnabledProtocols(new String[] {protocol});
    return socket;
  }

  /**
   * Create an SSLSocketFactory with the defined trust manager and protocol
   *
   * @param trustManager TrustManager to be used in the SSLContext
   * @param protocol The SSL protocol to be used in the SSLContext
   * @return An initialized SSLSocketFactory with SSLContext defined by input parameters
   * @throws Exception
   */
  private SSLSocketFactory makeSSLFactory(TrustManager[] trustManager, String protocol)
      throws NoSuchAlgorithmException, KeyManagementException {
    // Install the all-trusting trust manager
    SSLContext sslContext = SSLContext.getInstance(protocol);
    sslContext.init(null, trustManager, new java.security.SecureRandom());
    return sslContext.getSocketFactory();
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

  private static String[] getSupportedCiphers(){
    return
    new String[]{
            "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
            "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
            "TLS_ECDH_ECDSA_WITH_AES_256_GCM_SHA384",
            "TLS_ECDH_ECDSA_WITH_AES_128_GCM_SHA256",
            "TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA384",
            "TLS_ECDH_ECDSA_WITH_AES_256_CBC_SHA384",
            "TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA",
            "TLS_ECDH_ECDSA_WITH_AES_256_CBC_SHA",
            "TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA256",
            "TLS_ECDH_ECDSA_WITH_AES_128_CBC_SHA256",
            "TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA",
            "TLS_ECDH_ECDSA_WITH_AES_128_CBC_SHA"
    };
  }
}


