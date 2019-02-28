/**
 * Simple function to ingest test results event from DAQ.
 */

const functions = require('firebase-functions');
const admin = require('firebase-admin');
const {PubSub} = require(`@google-cloud/pubsub`);
const pubsub = new PubSub();

const EXPIRY_MS = 1000 * 60 * 60 * 24;

admin.initializeApp(functions.config().firebase);
var db = admin.firestore();

function deleteRun(port, port_doc, runid) {
  const rundoc = port_doc.collection('runid').doc(runid);
  rundoc.collection('test').get().then(function(snapshot) {
    snapshot.forEach(function(run_test) {
      console.log('Deleting', port, runid, run_test.id);
      rundoc.collection('test').doc(run_test.id)
        .delete().catch((error) => {
          console.error('Error deleting', port, runid, run_test.id, error);
        });
    });
  });
  rundoc.delete().catch((error) => {
    console.error('Error deleting', port, runid, error);
  });
}

exports.daq_firestore = functions.pubsub.topic('daq_runner').onPublish((event) => {
  const message = event.json;
  const origin = event.attributes.origin;
  const port = 'port-' + message.port;
  const timestr = new Date().toTimeString();
  const timestamp = Date.now();
  const expired = timestamp - EXPIRY_MS;

  console.log('updating', timestamp, origin, port, message.runid, message.name);

  const origin_doc = db.collection('origin').doc(origin);
  origin_doc.set({'updated': timestr});
  const port_doc = origin_doc.collection('port').doc(port);
  if (message.runid) {
    port_doc.set({'updated': timestr});
    const run_doc = port_doc.collection('runid').doc(message.runid);
    run_doc.set({'updated': timestr, 'timestamp': timestamp});
    const test_doc = run_doc.collection('test').doc(message.name);
    test_doc.set(message);

    port_doc.collection('runid').where('timestamp', '<', expired)
      .get().then(function(snapshot) {
        snapshot.forEach(function(old_doc) {
          deleteRun(port, port_doc, old_doc.id)
        });
      });
  } else {
    port_doc.set({
      'updated': timestr,
      'timestamp': timestamp,
      'message': message
    });
  }

  return null;
});

function get_device_doc(registryId, deviceId) {
  const timestr = new Date().toTimeString();
  const reg = db.collection('registry').doc(registryId);
  reg.set({'updated': timestr});
  const dev = reg.collection('device').doc(deviceId);
  dev.set({'updated': timestr});
  return dev;
}

exports.device_telemetry = functions.pubsub.topic('target').onPublish((event) => {
  const registryId = event.attributes.deviceRegistryId;
  const deviceId = event.attributes.deviceId;
  const base64 = event.data;
  const msgString = Buffer.from(base64, 'base64').toString();
  const msgObject = JSON.parse(msgString);

  device_doc = get_device_doc(registryId, deviceId).collection('telemetry').doc('latest');

  console.log(deviceId, msgObject);
  msgObject.data.forEach((data) => {
    device_doc.set(data);
  });

  return null;
});

exports.device_state = functions.pubsub.topic('state').onPublish((event) => {
  const attributes = event.attributes;
  const registryId = attributes.deviceRegistryId;
  const deviceId = attributes.deviceId;
  const base64 = event.data;
  const msgString = Buffer.from(base64, 'base64').toString();
  const msgObject = JSON.parse(msgString);

  console.log(`Processing state update for ${deviceId}`, msgObject);

  attributes.subFolder = 'state';
  publishPubsubMessage('target', msgObject, attributes);

  device_doc = get_device_doc(registryId, deviceId).collection('state').doc('latest');
  device_doc.set(msgObject);

  return null;
});

function publishPubsubMessage(topicName, data, attributes) {
  const dataBuffer = Buffer.from(JSON.stringify(data));

  pubsub
    .topic(topicName)
    .publisher()
    .publish(dataBuffer, attributes)
    .then(messageId => {
      console.debug(`Message ${messageId} published to ${topicName}.`);
    })
    .catch(err => {
      console.error('publishing error:', err);
    });
}
