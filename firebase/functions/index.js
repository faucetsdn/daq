/**
 * Simple function to ingest test results event from DAQ.
 */

const functions = require('firebase-functions');
const admin = require('firebase-admin');
const {PubSub} = require(`@google-cloud/pubsub`);
const iot = require('@google-cloud/iot');
const pubsub = new PubSub();

const EXPIRY_MS = 1000 * 60 * 60 * 24;

admin.initializeApp(functions.config().firebase);
const db = admin.firestore();

const iotClient = new iot.v1.DeviceManagerClient({
  // optional auth parameters.
});

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
  const site_name = event.attributes.site_name || 'unknown';
  const message_type = message.type;
  const payload = message.payload;

  if (message_type === 'runner_config') {
    handle_runner_config(origin, payload);
  } else if (message_type === 'test_result') {
    handle_test_result(origin, site_name, payload);
  } else if (message_type === 'heartbeat') {
    handle_heartbeat(origin, payload);
  } else {
    throw `Unknown message type ${message_type} from ${origin}`
  }
  return null;
});

function handle_runner_config(origin, message) {
  const now = Date.now();
  const timestamp = new Date(now).toJSON();

  console.log('updating runner config', timestamp, origin, message.timestamp);

  const origin_doc = db.collection('origin').doc(origin);
  const runner_doc = origin_doc.collection('runner').doc('setup').collection('config').doc('latest');
  runner_doc.set({
    'updated': timestamp,
    'timestamp': message.timestamp,
    'config': message.config
  });
}

function handle_test_result(origin, site_name, message) {
  const now = Date.now();
  const timestamp = new Date(now).toJSON();

  console.log('test_result', timestamp, origin, site_name, message.port,
      message.runid, message.name, message.device_id);

  const origin_doc = db.collection('origin').doc(origin);
  origin_doc.set({'updated': timestamp});

  const site_doc = db.collection('sites').doc(site_name);
  site_doc.set({'updated': timestamp});

  handle_test_result_by_port(now, origin_doc, message);
  if (message.device_id) {
    handle_test_result_by_device(now, origin_doc, message);
    handle_test_result_by_device(now, site_doc, message);
  }
}

function handle_test_result_by_port(now, origin_doc, message) {
  const timestamp = new Date(now).toJSON();
  const expired = new Date(now - EXPIRY_MS).toJSON();
  const port_doc = origin_doc.collection('port').doc('port-' + message.port);

  port_doc.set({'updated': timestamp});
  const run_doc = port_doc.collection('runid').doc(message.runid);
  run_doc.set({'updated': timestamp});
  const result_doc = run_doc.collection('test').doc(message.name);
  result_doc.set(message);

  if (message.config) {
    console.log('updating config', port, message.runid, typeof(message.config), message.config);
    run_doc.collection('config').doc('latest').set(message);
  }

  port_doc.collection('runid').where('timestamp', '<', expired)
    .get().then(function(snapshot) {
      snapshot.forEach(function(old_doc) {
        deleteRun(port, port_doc, old_doc.id)
      });
    });
}

function handle_test_result_by_device(now, root_doc, message) {
  const timestamp = new Date(now).toJSON();
  const expired = new Date(now - EXPIRY_MS).toJSON();
  const device_doc = root_doc.collection('device').doc(message.device_id);
  device_doc.set({'updated': timestamp});

  if (!message.name) {
    console.log('updating config', message.device_id, message.runid);
    const conf_doc = device_doc.collection('config').doc('latest');
    conf_doc.set(message);
    return;
  }

  const run_doc = device_doc.collection('runid').doc(message.runid);
  run_doc.set({'updated': timestamp});
  const result_doc = run_doc.collection('test').doc(message.name);
  result_doc.set(message);

  if (message.config) {
    console.log('updating config', port, message.runid, typeof(message.config), message.config);
    run_doc.collection('config').doc('latest').set(message);
  }

  device_doc.collection('runid').where('timestamp', '<', expired)
    .get().then(function(snapshot) {
      snapshot.forEach(function(old_doc) {
        deleteRun(port, port_doc, old_doc.id)
      });
    });
}

function handle_heartbeat(origin, message) {
  const timestamp = new Date().toJSON();
  console.log('heartbeat', timestamp, origin)
  const origin_doc = db.collection('origin').doc(origin);
  origin_doc.set({'updated': timestamp});
  const port_doc = origin_doc.collection('runner').doc('heartbeat')
  port_doc.set({
    'updated': timestamp,
    'message': message
  });
}

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

exports.device_config = functions.pubsub.topic('target').onPublish((event) => {
  const attributes = event.attributes;
  const subFolder = attributes.subFolder;
  if (subFolder != 'config') {
    return null;
  }
  const projectId = attributes.projectId;
  const cloudRegion = attributes.cloudRegion;
  const registryId = attributes.deviceRegistryId;
  const deviceId = attributes.deviceId;
  const binaryData = event.data;
  const msgString = Buffer.from(binaryData, 'base64').toString();
  const msgObject = JSON.parse(msgString);
  const version = 0;

  console.log(projectId, cloudRegion, registryId, deviceId, msgString);

  const formattedName = iotClient.devicePath(
    projectId,
    cloudRegion,
    registryId,
    deviceId
  );

  console.log(formattedName, msgObject);

  const request = {
    name: formattedName,
    versionToUpdate: version,
    binaryData: binaryData,
  };

  return iotClient.modifyCloudToDeviceConfig(request).then(responses => {
    console.log('Success:', responses[0]);
  }).catch(err => {
    console.error('Could not update config:', deviceId, err);
  });
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
