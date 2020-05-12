import java.io.IOException;
import java.security.KeyManagementException;
import java.security.NoSuchAlgorithmException;
import java.security.PublicKey;
import java.security.cert.Certificate;
import java.security.cert.CertificateExpiredException;
import java.security.cert.CertificateNotYetValidException;
import java.security.cert.X509Certificate;
import java.security.interfaces.DSAPublicKey;
import java.security.interfaces.RSAPublicKey;
import javax.net.ssl.*;

public class Certs {

  public static String ipAddress;
  public static int port;

  public Certs(String ipAddress, int port) {
    this.ipAddress = ipAddress;
    this.port = port;
  }

  String certificateReport = "";
  Report report = new Report();

  public boolean testTLSVersions() throws Exception {
    try {
      boolean tlsV10 = testTlsVersion("1");
      boolean tlsV12 = testTlsVersion("1.2");
      boolean tlsV13 = testTlsVersion("1.3");
      return tlsV10 || tlsV12 || tlsV13;
    } finally {
      report.writeReport(certificateReport);
    }
  }

  private boolean testTlsVersion(String tlsVersion) throws Exception {
    SSLSocket socket;
    try {
      // Attempt to open an SSL Socket at the TLS version specified
      socket = makeSSLSocket(ipAddress, port, "TLSv" + tlsVersion);
    } catch (IOException e) {
      System.out.println("TLSv" + tlsVersion + " Failed: " + e.getMessage());
      e.printStackTrace();
      skipTls(tlsVersion);
      skipTlsX509(tlsVersion);
      return false;
    }

    // Validate Server Certificates While using specified TLS version
    CertificateStatus certStatus = CertificateStatus.CERTIFICATE_INVALID;
    try {
      Certificate[] certificates = getServerCertificates(socket);
      certStatus = validateCertificates(certificates);
    } catch (SSLHandshakeException e) {
      System.out.println("SSLHandshakeException: Unable to complete handshake:" + e.getMessage());
      e.printStackTrace();
    } catch (Exception e) {
      System.out.println("Certificate Validation Failed: " + e.getMessage());
      e.printStackTrace();
    }

    validateCipher(socket);
    passTls(certStatus, tlsVersion);
    passX509(certStatus, tlsVersion);
    return certStatus == CertificateStatus.CERTIFICATE_VALID;
  }

  /**
   * Validate the Cipher while using specified TLS Version
   *
   * @param socket SSLSocket to use to retrieve the cipher
   * @return
   */
  private boolean validateCipher(SSLSocket socket) {
    try {
      String cipher = getSessionCipher(socket);
      certificateReport += "Cipher:" + cipher + "\n";
      boolean ecdh = cipher.toUpperCase().contains("ECDH");
      if (ecdh) {
        certificateReport += "Cipher Suite ECDH present.\n";
      } else {
        certificateReport += "WARNING: Cipher Suite ECDH NOT present.\n";
      }
      boolean ecdhsa = cipher.toUpperCase().contains("ECDSA");
      if (ecdhsa) {
        certificateReport += "Cipher Suite ECDSA present.\n";
      } else {
        certificateReport += "WARNING: Cipher Suite ECDSA NOT present.\n";
      }
      return ecdh && ecdhsa;
    } catch (Exception e) {
      System.out.println("Cipher Validation Failed: " + e.getMessage());
      e.printStackTrace();
      return false;
    }
  }

  private CertificateStatus validateCertificates(Certificate[] certificates) {
    for (Certificate certificate : certificates) {

      if (certificate instanceof X509Certificate) {
        try {
          certificateReport += "Certificate:\n" + certificate + "\n";
          // Check the expiration date
          X509Certificate x509Certificate = (X509Certificate) certificate;
          x509Certificate.checkValidity();
          certificateReport += "Certificate is active for current date.\n\n";
          // Check the public key bit length is at least 2048
          PublicKey key = x509Certificate.getPublicKey();
          int keyLength = 0;
          if (key instanceof RSAPublicKey) {
            keyLength = ((RSAPublicKey) key).getModulus().bitLength();
          } else if (key instanceof DSAPublicKey) {
            keyLength = ((DSAPublicKey) key).getParams().getP().bitLength();
          }
          if (keyLength >= 2048) {
            certificateReport += "Certificate has valid public key length: " + keyLength + "\n\n";
            return CertificateStatus.CERTIFICATE_VALID;
          }
          return CertificateStatus.PUBLIC_KEY_INVALID_LENGTH;
        } catch (CertificateExpiredException cee) {
          certificateReport += "Certificate is expired.\n";
          return CertificateStatus.CERTIFICATE_EXPIRED;
        } catch (CertificateNotYetValidException e) {
          certificateReport += "Certificate not yet valid.\n";
          return CertificateStatus.CERTIFICATE_NOT_YET_VALID;
        }
      } else {
        certificateReport += "Unsupported certificate type.\n";
        return CertificateStatus.CERTIFICATE_TYPE_UNSUPPORTED;
      }
    }
    return CertificateStatus.CERTIFICATE_INVALID;
  }

  private void passX509(CertificateStatus status, String tlsVersion) {

    if (status == CertificateStatus.CERTIFICATE_VALID) {
      certificateReport +=
          "RESULT pass security.tls.v"
              + tlsVersion.replace(".", "_")
              + ".x509 "
              + getCertStatusMessage(status)
              + "\n";
    } else {
      certificateReport +=
          "RESULT fail security.tls.v"
              + tlsVersion.replace(".", "_")
              + ".x509 "
              + getCertStatusMessage(status)
              + "\n";
    }

    //    if (status) {
    //      certificateReport += "RESULT pass security.tls.v" + tlsVersion.replace(".", "_") +
    // ".x509\n";
    //    } else {
    //      certificateReport += "RESULT fail security.tls.v" + tlsVersion.replace(".", "_") +
    // ".x509\n";
    //    }
  }

  private void passTls(CertificateStatus status, String tlsVersion) {
    if (status == CertificateStatus.CERTIFICATE_VALID) {
      certificateReport +=
          "RESULT pass security.tls.v"
              + tlsVersion.replace(".", "_")
              + " "
              + getCertStatusMessage(status)
              + "\n";
    } else {
      certificateReport +=
          "RESULT fail security.tls.v"
              + tlsVersion.replace(".", "_")
              + " "
              + getCertStatusMessage(status)
              + "\n";
    }
    //
    //    if (status) {
    //      certificateReport += "RESULT pass security.tls.v" + tlsVersion.replace(".", "_") + "\n";
    //    } else {
    //      certificateReport += "RESULT fail security.tls.v" + tlsVersion.replace(".", "_") + "\n";
    //    }
  }

  private String getCertStatusMessage(CertificateStatus status) {
    String message = "";
    switch (status) {
      case CERTIFICATE_VALID:
        message = "Certificate active for current date and public key length > 2048.";
        break;
      case CERTIFICATE_NOT_YET_VALID:
        message = "Certificate not yet active for current date.";
        break;
      case CERTIFICATE_EXPIRED:
        message = "Certificate is expired.";
        break;
      case CERTIFICATE_TYPE_UNSUPPORTED:
        message = "Certificate type is NOT in supported x509 format.";
        break;
      case PUBLIC_KEY_INVALID_LENGTH:
        message = "Certificate public key length is < 2048.";
        break;
      case CERTIFICATE_INVALID:
      default:
        message = "Certificate could not be validated.";
    }
    return message;
  }

  private void skipTls(String tlsVersion) {
    certificateReport +=
        "RESULT skip security.tls.v"
            + tlsVersion.replace(".", "_")
            + " IOException unable to connect to server \n";
  }

  private void skipTlsX509(String tlsVersion) {
    certificateReport +=
        "RESULT skip security.tls.v"
            + tlsVersion.replace(".", "_")
            + ".x509 IOException unable to connect to server\n";
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

    SSLSocket socket = (SSLSocket) factory.createSocket(host, port);
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
}
