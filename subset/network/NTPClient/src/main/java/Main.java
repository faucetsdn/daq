import java.io.IOException;
import java.net.*;
import java.text.DecimalFormat;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;


public class Main {
    static final double SECONDS_FROM_01_01_1900_TO_01_01_1970 = 2208988800.0;
    static String serverName = "time.google.com";
    static int PORT = 123;
    static int timerPeriod = 10;

    public static void main(String[] args) {
        if (args.length < 2) {
            throw new IllegalArgumentException("Usage: server_name port timerPeriod");
        }
        serverName = args[0];
        PORT = Integer.parseInt(args[1]);
        timerPeriod = Integer.parseInt(args[2]);

        Runnable senderRunnable = new Runnable() {
            @Override
            public void run() {
                try {
                    sendRequest();
                } catch (IOException e) {
                    System.out.println(e.getMessage());
                }
            }
        };
        ScheduledExecutorService executor = Executors.newScheduledThreadPool(1);
        executor.scheduleAtFixedRate(senderRunnable, 0, timerPeriod, TimeUnit.SECONDS);
    }

    private static void sendRequest() throws IOException {
        // Send request
        DatagramSocket socket = new DatagramSocket();
        InetAddress address = InetAddress.getByName(serverName);
        byte[] buf = new NtpMessage(SECONDS_FROM_01_01_1900_TO_01_01_1970).toByteArray();
        DatagramPacket packet =
                new DatagramPacket(buf, buf.length, address, PORT);

        // Set the transmit timestamp *just* before sending the packet
        NtpMessage.encodeTimestamp(packet.getData(), 40,
                (System.currentTimeMillis() / 1000.0) + SECONDS_FROM_01_01_1900_TO_01_01_1970);
        sendPacket(socket, packet, buf);
    }

    private static void sendPacket(DatagramSocket socket, DatagramPacket packet, byte[] buf) throws IOException {
        socket.send(packet);

        // Get response
        System.out.println("NTP request sent, waiting for response...\n");
        packet = new DatagramPacket(buf, buf.length);
        socket.receive(packet);

        // Immediately record the incoming timestamp
        double destinationTimestamp =
                (System.currentTimeMillis() / 1000.0) + SECONDS_FROM_01_01_1900_TO_01_01_1970;

        // Process response
        NtpMessage msg = new NtpMessage(packet.getData());
        double roundTripDelay = (destinationTimestamp-msg.originateTimestamp) -
                (msg.transmitTimestamp-msg.receiveTimestamp);
        double localClockOffset =
                ((msg.receiveTimestamp - msg.originateTimestamp) +
                        (msg.transmitTimestamp - destinationTimestamp)) / 2;

        // Display response
        System.out.println("NTP server: " + serverName);
        System.out.println(msg.toString());
        System.out.println("Dest. timestamp:     " +
                NtpMessage.timestampToString(destinationTimestamp));
        System.out.println("Round-trip delay: " +
                new DecimalFormat("0.00").format(roundTripDelay * 1000) + " ms");
        System.out.println("Local clock offset: " +
                new DecimalFormat("0.00").format(localClockOffset * 1000) + " ms");
    }
}
