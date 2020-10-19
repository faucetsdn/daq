import java.util.Arrays;

public class ResultGenerator {

    public static String generateServerResults(Server tlsServer){
        String report = "";
        if(tlsServer.getServerResult() == TestResult.PASS
                && tlsServer.getCertificateResult() == TestResult.PASS){
            report = generatePassResults(tlsServer);
        }
        else if(tlsServer.getServerResult() == TestResult.SKIP
                || tlsServer.getCertificateResult() ==TestResult.SKIP){
            report = generateServerSkipResult(tlsServer);
        }
        else{
            report = generateFailResults(tlsServer);
        }

        return report;
    }

    private static String generatePassResults(Server server){
        String report = "";
        report +=
                "\nRESULT pass security.tls.v"
                        + server.getTlsVersion().replace(".","_")
                        + "_server "
                        + getKeyLengthStatusMessage(server.getServerKeyLengthStatus()) + " "
                        + getCertStatusMessage(server.getServerCertStatus()) + " "
                        + getSignatureMessage(server.getSigStatus()) + " "
                        + getCipherStatusMessage(server.getCipherStatus());
        return report;
    }

    private static String generateFailResults(Server server){
        String report = "";
        report +=
                "\nRESULT fail security.tls.v"
                        + server.getTlsVersion().replace(".","_")
                        + "_server";
        if(server.getServerKeyLengthStatus() == KeyLengthStatus.PUBLIC_KEY_INVALID_LENGTH){
            report+=" " + getKeyLengthStatusMessage(server.getServerKeyLengthStatus());
        }
        if(server.getServerCertStatus() != CertificateStatus.CERTIFICATE_VALID){
            report+=" " + getCertStatusMessage(server.getServerCertStatus());
        }
        if(server.getSigStatus() != CertificateSignatureStatus.CERTIFICATE_CA_SIGNED){
            report+=" " + getSignatureMessage(server.getSigStatus());
        }
        if(server.getCipherStatus() == CipherStatus.VALID){
            report+=" " + getCipherStatusMessage(server.getCipherStatus());
        }
        return report;
    }

    private static String generateServerSkipResult(Server server) {
        String report =
                "\nRESULT skip security.tls.v"
                + server.getTlsVersion().replace(".","_")
                + "_server"
                + " IOException unable to connect to server.";
        return report;
    }

    public static String getKeyLengthStatusMessage(KeyLengthStatus status){
        String message ="";
        switch (status) {
            case PUBLIC_KEY_RSA_VALID_LENGTH:
                message = "Certificate public key length is >= 2048.";
                break;
            case PUBLIC_KEY_EC_VALID_LENGTH:
                message = "Certificate public key length is >= 224.";
                break;
            case PUBLIC_KEY_INVALID_LENGTH:
            default:
                message = "Certificate public key length too short.";
        }
        return message;
    }

    public static String getCipherStatusMessage(CipherStatus status){
        String message ="";
        switch (status) {
            case VALID:
                message = "Cipher Valid.";
                break;
            case INVALID:
                message = "Cipher Invalid.";
                break;
            case SKIPPED:
            default:
                message = "Cipher check not required.";
        }
        return message;
    }

    public static String getSignatureMessage(CertificateSignatureStatus status){
        String message ="";
        switch (status) {
            case CERTIFICATE_CA_SIGNED:
                message = "Certificate has been signed by a CA.";
                break;
            case CERTIFICATE_SELF_SIGNED:
            default:
                message = "Certificate has not been signed by a CA.";
        }
        return message;
    }

    public static String getCertStatusMessage(CertificateStatus status) {
        String message ="";
        switch (status) {
            case CERTIFICATE_VALID:
                message = "Certificate active for current date.";
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
            case CERTIFICATE_INVALID:
            default:
                message = "Certificate could not be validated.";
        }
        return message;
    }

    public static String combineTlsVersions(String[] tlsVersions){
        StringBuilder sb = new StringBuilder();
        Arrays.stream(tlsVersions).forEach(tls ->{
            sb.append(sb.length()>0?",":"");
            sb.append(tls);
        });
        return sb.toString();
    }
}


