Report generation error: 'device_info' is undefined
Failing data model:
{'modules': {'pass': {'enabled': False}, 'nmap': {'enabled': True}, 'macoui': {'enabled': True}, 'switch': {'enabled': False}, 'brute': {'enabled': True}, 'bacext': {'enabled': True}, 'tls': {'enabled': True}, 'udmi': {'enabled': True}}, 'process': {'approver': '*** Approver Name ***', 'operator': '*** Operator Name ***'}, 'report': {'results': ['pass', 'fail', 'skip'], 'expected': ['Required', 'recommended']}, 'tests': {'base.target.ping': {'category': 'connectivity', 'expected': 'Required'}, 'security.ports.nmap': {'category': 'security', 'expected': 'Recommended'}, 'network.brute': {'category': 'security', 'expected': 'Required'}}, 'run_info': {'run_id': '5d164013', 'mac_addr': '3c:5a:b4:1e:8f:0a', 'daq_version': '1.0.0', 'started': '2019-06-28T16:28:03.471Z'}, 'device_id': 'SNS-4', 'clean_mac': '3c5ab41e8f0a', 'start_time': datetime.datetime(2019, 6, 28, 16, 28, 3, tzinfo=<UTC>), 'end_time': datetime.datetime(2019, 6, 28, 16, 34, 5, tzinfo=<UTC>)}

## Report summary

|Expected|pass|fail|skip|
|---|---|---|---|
|Required|1|0|1|
|recommended|0|0|0|
|other|4|1|1|
|Recommended|0|1|0|

|Result|Test|Expected|Notes|
|---|---|---|---|
|skip|base.switch.ping|other||
|pass|base.target.ping|Required|target|
|fail|cloud.udmi.pointset|other|#: extraneous key [extraField] is not permitted|
|pass|connection.mac_oui|other||
|skip|network.brute|Required||
|pass|protocol.bacnet.version|other||
|fail|security.ports.nmap|Recommended||
|pass|security.tls.v3|other||
|pass|security.x509|other||


## Module ping

```
Baseline ping test report
%% 411 packets captured.
RESULT skip base.switch.ping
RESULT pass base.target.ping target %% 10.20.88.106
```

## Module nmap

```
Failing 443 open tcp https
RESULT fail security.ports.nmap
```

## Module brute

```
Target port 10000 not open.
RESULT skip network.brute
```

## Module macoui

```
Mac OUI Test
RESULT pass connection.mac_oui
```

## Module bacext

```
RESULT pass protocol.bacnet.version
```

## Module tls

```
Cipher:
TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
Certificate is active for current date.
RESULT pass security.tls.v3
RESULT pass security.x509

Certificate:
[
[
  Version: V1
  Subject: CN=127.0.0.1, OU=Software, O=ExcelRedstone, L=KingsX, ST=London, C=GB
  Signature Algorithm: SHA256withRSA, OID = 1.2.840.113549.1.1.11

  Key:  Sun RSA public key, 2048 bits
  modulus: 25872784015411084185589120859860270100270948657205752204249532917079107170341170558719213379933762881585949646574327365030055544118725875652840894288548247713757235926194680801686786700082315619499203157641091732515136485044369555717192265884611268680453488660653711963337787278259793759886896835452467506615747113224214858192617508781491418253768582530028912553047415859963966828650148036200604854419328809212615380972275346564330360867953655675399964314495209438096936895875653533316373690861766463815752298903019707818819416636640194741996634892957203916030903259922076303785298789406026627472062823823162104145643
  public exponent: 65537
  Validity: [From: Fri Jun 28 16:28:14 GMT 2019,
               To: Sat Jun 27 16:28:14 GMT 2020]
  Issuer: CN=127.0.0.1, OU=Software, O=ExcelRedstone, L=KingsX, ST=London, C=GB
  SerialNumber: [    7c475ea0 5de545d6 09643971 0e579868 578ac051]

]
  Algorithm: [SHA256withRSA]
  Signature:
0000: BE E1 03 92 80 A5 25 CB   5A AD F2 A7 00 F5 CC FD  ......%.Z.......
0010: 36 F3 21 80 B1 02 F1 F2   D1 C3 8E A9 0C 4D A4 4B  6.!..........M.K
0020: B8 57 EF 54 C2 AE AD 5E   81 B8 AD 92 F6 A5 5E 24  .W.T...^......^$
0030: 5C D9 07 B5 06 32 5F F8   05 C7 FE 71 68 E4 CB 6B  \....2_....qh..k
0040: 09 C5 84 7E A5 30 A0 2E   A1 5E 78 D9 B6 F8 EC 2E  .....0...^x.....
0050: 39 27 4F 7A 6F D4 6C D9   B6 54 B7 B4 25 F9 0D C3  9'Ozo.l..T..%...
0060: 61 86 DF DC F2 36 2A AE   FE 32 9C 31 5C 58 DD 7C  a....6*..2.1\X..
0070: 26 38 44 CB FD EF 4E 29   39 3C E5 7C A2 91 A9 40  &8D...N)9<.....@
0080: 02 E5 85 FD 43 6D 05 EE   2A 47 40 57 1D 43 F3 D2  ....Cm..*G@W.C..
0090: F7 36 4C CB B2 E9 0C D6   24 49 B3 29 94 71 F4 B7  .6L.....$I.).q..
00A0: F5 E7 A5 B1 4E 62 5E AE   3B A2 11 AE E9 4C 01 05  ....Nb^.;....L..
00B0: 22 32 18 F4 91 AF 09 66   EF 86 0B BF E9 70 11 D1  "2.....f.....p..
00C0: 9E CE E0 B2 87 BB 26 38   16 B5 5C B4 3A 9D 53 24  ......&8..\.:.S$
00D0: C1 18 D6 B2 F5 AB EA 0D   EE 8C 04 16 19 14 19 23  ...............#
00E0: D9 89 6F DF D5 DE 34 3E   F1 72 FA 1F 28 79 B6 D7  ..o...4>.r..(y..
00F0: FF E1 FC 32 B2 57 9A EB   25 D9 5B 3D 5E D9 1B CD  ...2.W..%.[=^...

]
```

## Module udmi

```
RESULT fail cloud.udmi.pointset #: extraneous key [extraField] is not permitted
```

## Report complete

