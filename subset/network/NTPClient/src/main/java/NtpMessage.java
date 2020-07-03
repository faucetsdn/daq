import java.text.DecimalFormat;
import java.text.SimpleDateFormat;
import java.util.Date;

public class NtpMessage {
    public byte leapIndicator = 0;
    public byte version = 3;
    public byte mode = 0;
    public short stratum = 0;
    public byte pollInterval = 0;
    public byte precision = 0;
    public double rootDelay = 0;
    public double rootDispersion = 0;
    public byte[] referenceIdentifier = {0, 0, 0, 0};
    public double referenceTimestamp = 0;
    public double originateTimestamp = 0;
    public double receiveTimestamp = 0;
    public double transmitTimestamp = 0;

    /**
     * Constructs a new NtpMessage from an array of bytes.
     */
	public NtpMessage(byte[] array) {
        // See the packet format diagram in RFC 2030 for details
        leapIndicator = (byte)((array[0] >> 6) & 0x3);
        version = (byte)((array[0] >> 3) & 0x7);
        mode = (byte)(array[0] & 0x7);
        stratum = unsignedByteToShort(array[1]);
        pollInterval = array[2];
        precision = array[3];

        rootDelay = (array[4] * 256.0) +
                unsignedByteToShort(array[5]) +
                (unsignedByteToShort(array[6]) / 256.0) +
                (unsignedByteToShort(array[7]) / 65536.0);

        rootDispersion = (unsignedByteToShort(array[8]) * 256.0) +
                unsignedByteToShort(array[9]) +
                (unsignedByteToShort(array[10]) / 256.0) +
                (unsignedByteToShort(array[11]) / 65536.0);

        referenceIdentifier[0] = array[12];
        referenceIdentifier[1] = array[13];
        referenceIdentifier[2] = array[14];
        referenceIdentifier[3] = array[15];

        referenceTimestamp = decodeTimestamp(array, 16);
        originateTimestamp = decodeTimestamp(array, 24);
        receiveTimestamp = decodeTimestamp(array, 32);
        transmitTimestamp = decodeTimestamp(array, 40);
	}

    /**
     * Constructs a new NtpMessage in client -> server mode, and sets the
     * transmit timestamp to the current time.
     */
	public NtpMessage(double SECONDS_FROM_01_01_1900_TO_01_01_1970) {
        this.mode = 3;
        this.transmitTimestamp = (System.currentTimeMillis() / 1000.0) + SECONDS_FROM_01_01_1900_TO_01_01_1970;
	}

    /**
     * This method constructs the data bytes of a raw NTP packet.
     */
    public byte[] toByteArray() {
        // All bytes are automatically set to 0
        byte[] p = new byte[48];

        p[0] = (byte)(leapIndicator << 6 | version << 3 | mode);
        p[1] = (byte)stratum;
        p[2] = (byte)pollInterval;
        p[3] = (byte)precision;

        // root delay is a signed 16.16-bit FP, in Java an int is 32-bits
        int l = (int)(rootDelay * 65536.0);
        p[4] = (byte)((l >> 24) & 0xFF);
        p[5] = (byte)((l >> 16) & 0xFF);
        p[6] = (byte)((l >> 8) & 0xFF);
        p[7] = (byte)(l & 0xFF);

        // root dispersion is an unsigned 16.16-bit FP, in Java there are no
        // unsigned primitive types, so we use a long which is 64-bits
        long ul = (long)(rootDispersion * 65536.0);
        p[8] = (byte)((ul >> 24) & 0xFF);
        p[9] = (byte)((ul >> 16) & 0xFF);
        p[10] = (byte)((ul >> 8) & 0xFF);
        p[11] = (byte)(ul & 0xFF);

        p[12] = referenceIdentifier[0];
        p[13] = referenceIdentifier[1];
        p[14] = referenceIdentifier[2];
        p[15] = referenceIdentifier[3];

        encodeTimestamp(p, 16, referenceTimestamp);
        encodeTimestamp(p, 24, originateTimestamp);
        encodeTimestamp(p, 32, receiveTimestamp);
        encodeTimestamp(p, 40, transmitTimestamp);

        return p;
    }

    /**
     * Returns a string representation of a NtpMessage
     */
    public String toString() {
        String precisionStr =
                new DecimalFormat("0.#E0").format(Math.pow(2, precision));

        return "Leap indicator: " + leapIndicator + "\n" +
                "Version: " + version + "\n" +
                "Mode: " + mode + "\n" +
                "Stratum: " + stratum + "\n" +
                "Poll: " + pollInterval + "\n" +
                "Precision: " + precision + " (" + precisionStr + " seconds)\n" +
                "Root delay: " + new DecimalFormat("0.00").format(rootDelay * 1000) + " ms\n" +
                "Root dispersion: " + new DecimalFormat("0.00").format(rootDispersion * 1000) + " ms\n" +
                "Reference identifier: " + referenceIdentifierToString(referenceIdentifier, stratum, version) + "\n" +
                "Reference timestamp: " + timestampToString(referenceTimestamp) + "\n" +
                "Originate timestamp: " + timestampToString(originateTimestamp) + "\n" +
                "Receive timestamp:   " + timestampToString(receiveTimestamp) + "\n" +
                "Transmit timestamp:  " + timestampToString(transmitTimestamp);
    }

    /**
     * Converts an unsigned byte to a short.  By default, Java assumes that
     * a byte is signed.
     */
    public static short unsignedByteToShort(byte b) {
        if((b & 0x80) == 0x80) return (short)(128 + (b & 0x7f));
        else return (short)b;
    }

    /**
     * Will read 8 bytes of a message beginning at <code>pointer</code>
     * and return it as a double, according to the NTP 64-bit timestamp
     * format.
     */
    public static double decodeTimestamp(byte[] array, int pointer) {
        double r = 0.0;

        for(int i = 0; i < 8; i++)
        {
            r += unsignedByteToShort(array[pointer + i]) * Math.pow(2, (3 - i) * 8);
        }

        return r;
    }

    /**
     * Encodes a timestamp in the specified position in the message
     */
    public static void encodeTimestamp(byte[] array, int pointer, double timestamp) {
        // Converts a double into a 64-bit fixed point
        for(int i = 0; i < 8; i++) {
            // 2^24, 2^16, 2^8, .. 2^-32
            double base = Math.pow(2, (3 - i) * 8);
            // Capture byte value
            array[pointer + i] = (byte)(timestamp / base);
            // Subtract captured value from remaining total
            timestamp = timestamp - (double)(unsignedByteToShort(array[pointer + i]) * base);
        }
        array[7] = (byte)(Math.random() * 255.0);
    }

    /**
     * Returns a timestamp (number of seconds since 00:00 1-Jan-1900) as a
     * formatted date/time string.
     */
    public static String timestampToString(double timestamp) {
        if(timestamp == 0) return "0";
        double utc = timestamp - (2208988800.0);
        long ms = (long)(utc * 1000.0);
        String date = new SimpleDateFormat("dd-MMM-yyyy HH:mm:ss").format(new Date(ms));
        double fraction = timestamp - ((long)timestamp);
        String fractionSting = new DecimalFormat(".000000").format(fraction);
        return date + fractionSting;
    }

    /**
     * Returns a string representation of a reference identifier according
     * to the rules set out in RFC 2030.
     */
    public static String referenceIdentifierToString(byte[] ref, short stratum, byte version) {
        if(stratum == 0 || stratum == 1)
        {
            return new String(ref);
        }
        else if(version == 3)
        {
            return unsignedByteToShort(ref[0]) + "." +
                    unsignedByteToShort(ref[1]) + "." +
                    unsignedByteToShort(ref[2]) + "." +
                    unsignedByteToShort(ref[3]);
        }
        // In NTP Version 4 secondary servers, this is the low order 32 bits
        // of the latest transmit timestamp of the reference source.
        else if(version == 4)
        {
            return "" + ((unsignedByteToShort(ref[0]) / 256.0) +
                    (unsignedByteToShort(ref[1]) / 65536.0) +
                    (unsignedByteToShort(ref[2]) / 16777216.0) +
                    (unsignedByteToShort(ref[3]) / 4294967296.0));
        }
        return "";
    }
}
