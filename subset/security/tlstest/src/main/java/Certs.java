import java.io.IOException;
import java.net.*;
import java.security.*;
import java.security.cert.CertificateExpiredException;
import java.security.cert.CertificateNotYetValidException;
import java.security.cert.X509Certificate;
import javax.net.ssl.HostnameVerifier;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSession;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;

public class Certs {

  String ipAddress = "127.0.0.1";
  String certificateReport = "";
  String summaryNote = "";

  Report report = new Report();

  public Certs(String ipAddress) {
    this.ipAddress = ipAddress;
  }

  public boolean getCertificate() {
    try {
      disableSslVerification();

      URL url;

      url = new URL(ipAddress);
      HttpsURLConnection httpsURLConnection;
      httpsURLConnection = (HttpsURLConnection) url.openConnection();
      httpsURLConnection.connect();
      Principal peername = httpsURLConnection.getPeerPrincipal();
      String cipher = httpsURLConnection.getCipherSuite();
      java.security.cert.Certificate[] certificates = httpsURLConnection.getServerCertificates();
      certificateReport += "Cipher:\n" + cipher + "\n";
      for (java.security.cert.Certificate certificate : certificates) {

        if (certificate instanceof X509Certificate) {
          try {
            ((X509Certificate) certificate).checkValidity();
            summaryNote = "Certificate is active for current date.";
            certificateReport += summaryNote + "\n";
            passTlsV3(true);
            passX509(true);
          } catch (CertificateExpiredException cee) {
            summaryNote = "Certificate is expired.";
            certificateReport += summaryNote + "\n";
            passTlsV3(false);
            passX509(false);
            return false;
          } catch (CertificateNotYetValidException e) {
            summaryNote = "Certificate not yet valid.";
            certificateReport += summaryNote + "\n";
            passTlsV3(false);
            passX509(false);
            return false;
          }

          certificateReport += "\n";

          certificateReport += "Certificate:\n" + certificate + "\n";

        } else {
          summaryNote = "Unknown certificate type";
          certificateReport += summaryNote + "\n";
          passTlsV3(false);
          passX509(false);
          System.err.println("Unknown certificate type: " + certificate);
          return false;
        }
      }
      return true;
    } catch (MalformedURLException e) {
      summaryNote = "MalformedURLException unable to connect to server.";
      certificateReport += summaryNote + "\n";
      System.err.println("getCertificate MalformedURLException:" + e.getMessage());
      skipTlsX509();
      return false;
    } catch (IOException e) {
      summaryNote = "IOException unable to connect to server";
      certificateReport += summaryNote + "\n";
      System.err.println("getCertificate IOException:" + e.getMessage());
      skipTlsX509();
      return false;
    } finally {
      report.writeReport(certificateReport);
    }
  }

  private void passTlsV3(boolean status){
    if(status){
      certificateReport += String.format("RESULT pass security.tls.v3 %s\n", summaryNote);
    } else {
      certificateReport += String.format("RESULT fail security.tls.v3 %s\n", summaryNote);
    }
  }

  private void passX509(boolean status){
    if(status){
      certificateReport += String.format("RESULT pass security.x509 %s\n", summaryNote);
    } else {
      certificateReport += String.format("RESULT fail security.x509 %s\n", summaryNote); 
    }
  }

  private void skipTlsX509(){
    certificateReport += String.format("RESULT skip security.tls.v3 %s\n", summaryNote);
    certificateReport += String.format("RESULT skip security.x509 %s\n", summaryNote);
  }

  private static void disableSslVerification() {
    try {
      // Create a trust manager that does not validate certificate chains
      TrustManager[] trustAllCerts =
          new TrustManager[] {
            new X509TrustManager() {
              public java.security.cert.X509Certificate[] getAcceptedIssuers() {
                return null;
              }

              public void checkClientTrusted(X509Certificate[] certs, String authType) {}

              public void checkServerTrusted(X509Certificate[] certs, String authType) {}
            }
          };

      // Install the all-trusting trust manager
      SSLContext sslContext = SSLContext.getInstance("SSL");
      sslContext.init(null, trustAllCerts, new java.security.SecureRandom());
      HttpsURLConnection.setDefaultSSLSocketFactory(sslContext.getSocketFactory());

      // Create all-trusting host name verifier
      HostnameVerifier allHostsValid =
          new HostnameVerifier() {
            public boolean verify(String hostname, SSLSession session) {
              return true;
            }
          };

      // Install the all-trusting host verifier
      HttpsURLConnection.setDefaultHostnameVerifier(allHostsValid);
    } catch (NoSuchAlgorithmException e) {
      System.err.println("disableSslVerification NoSuchAlgorithmException:" + e.getMessage());
    } catch (KeyManagementException e) {
      System.err.println("disableSslVerification KeyManagementException:" + e.getMessage());
    }
  }
}