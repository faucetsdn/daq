/**
 * Simple function to ingest test results event from DAQ.
 */

const functions = require('firebase-functions');
const admin = require('firebase-admin');
const { PubSub } = require(`@google-cloud/pubsub`);
const pubsub = new PubSub();

admin.initializeApp(functions.config().firebase);
const db = admin.firestore();

exports.daq_firestore = functions.pubsub.topic('daq_runner').onPublish((event) => {
  const message = event.json;
  const origin = event.attributes.origin;
  const siteName = event.attributes.site_name || 'unknown';
  const messageType = message.type;
  const payload = message.payload;

  if (messageType === 'runner_config') {
    return handleRunnerConfig(origin, payload);
  } else if (messageType === 'test_result') {
    return handleTestResult(origin, siteName, payload);
  } else if (messageType === 'heartbeat') {
    return handleHeartbeat(origin, payload);
  } else {
    throw `Unknown message type ${messageType} from ${origin}`
  }
});

function handleRunnerConfig(origin, message) {
  const now = Date.now();
  const timestamp = new Date(now).toJSON();
  console.log('updating runner config', timestamp, origin, message.timestamp);

  const originDoc = db.collection('origin').doc(origin);
  const runnerDoc = originDoc.collection('runner').doc('setup').collection('config').doc('latest');
  return runnerDoc.set({
    'updated': timestamp,
    'timestamp': message.timestamp,
    'config': message.config
  });
}

function handleTestResult(origin, siteName, message) {
  const now = Date.now();
  const timestamp = new Date(now).toJSON();

  const originDoc = db.collection('origin').doc(origin);
  const siteDoc = db.collection('site').doc(siteName);
  const portDoc = originDoc.collection('port').doc('port' + message.port);
  const deviceDoc = originDoc.collection('device').doc(message.device_id);
  return Promise.all([
    originDoc.set({ 'updated': timestamp }),
    siteDoc.set({ 'updated': timestamp }),
    portDoc.set({ 'updated': timestamp }),
    deviceDoc.set({ 'updated': timestamp })
  ]).then(() => {
    if (!message.name) {
      console.log('latest config', message.device_id, message.runid);
      const confDoc = deviceDoc.collection('config').doc('latest');

      return Promise.all([
        deviceDoc.set({ 'updated': timestamp }),
        confDoc.set(message)
      ]);
    }

    console.log('Test Result: ', timestamp, origin, siteName, message.port,
      message.runid, message.name, message.device_id, message.state);
    const runDoc = originDoc.collection('runid').doc(message.runid);
    const resultDoc = runDoc.collection('test').doc(message.name);
    const portRunDoc = portDoc.collection('runid').doc(message.runid);
    const deviceRunDoc = deviceDoc.collection('runid').doc(message.runid);
    return resultDoc.get().then((result) => {
      if (!result) {
        return true;
      }
      let data = result.data();
      if (!data || new Date(data.timestamp) < new Date(message.timestamp)) {
        return true;
      }
      return false;
    }).then((doUpdate) => {
      if(!doUpdate) {
        return;
      }
      return Promise.all([
        runDoc.set({ 'updated': timestamp }, { merge: true }),
        resultDoc.set(message),
        portRunDoc.set({ 'updated': timestamp }),
        deviceRunDoc.set({ 'updated': timestamp }),
      ]).then(() => {
        if (message.config) {
          console.log('updating config', message.port, message.runid, typeof (message.config), message.config);
          return Promise.all([
            runDoc.update({
              deviceId: message.device_id,
              siteName,
              port: message.port
            }),
            runDoc.collection('config').doc('latest').set(message)
          ]);
        }
      });
    });

  });
}

function handleHeartbeat(origin, message) {
  const timestamp = new Date().toJSON();
  const originDoc = db.collection('origin').doc(origin);
  console.log('heartbeat', timestamp, origin)
  originDoc.set({ 'updated': timestamp });
  const heartbeatDoc = originDoc.collection('runner').doc('heartbeat')
  return heartbeatDoc.set({
    'updated': timestamp,
    message
  });
}

function getDeviceDoc(registryId, deviceId) {
  const timestr = new Date().toTimeString();
  const reg = db.collection('registry').doc(registryId);
  const dev = reg.collection('device').doc(deviceId);
  return Promise.all([
    reg.set({ 'updated': timestr }),
    dev.set({ 'updated': timestr })
  ]).then(() => {
    return dev;
  });
}

exports.device_telemetry = functions.pubsub.topic('target').onPublish((event) => {
  const registryId = event.attributes.deviceRegistryId;
  const deviceId = event.attributes.deviceId;
  const base64 = event.data;
  const msgString = Buffer.from(base64, 'base64').toString();
  const msgObject = JSON.parse(msgString);

  getDeviceDoc(registryId, deviceId).then((deviceDoc) => {
    telemetryDoc = deviceDoc.collection('telemetry').doc('latest');
    return Promise.all(msgObject.data.map((data) => {
      telemetryDoc.set(data);
    }));
  }).then(() => {
    console.log(deviceId, msgObject);
  });
});

exports.device_state = functions.pubsub.topic('state').onPublish((event) => {
  const attributes = event.attributes;
  const registryId = attributes.deviceRegistryId;
  const deviceId = attributes.deviceId;
  const base64 = event.data;
  const msgString = Buffer.from(base64, 'base64').toString();
  const msgObject = JSON.parse(msgString);

  attributes.subFolder = 'state';
  console.log(`Processing state update for ${deviceId}`, msgObject);
  return publishPubsubMessage('target', msgObject, attributes).then(() => {
    return getDeviceDoc(registryId, deviceId);
  }).then((deviceDoc) => {
    deviceState = deviceDoc.collection('state').doc('latest');
    return deviceState.set(msgObject);
  });
});

function publishPubsubMessage(topicName, data, attributes) {
  const dataBuffer = Buffer.from(JSON.stringify(data));

  return pubsub
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
