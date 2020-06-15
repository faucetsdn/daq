/**
 * Simple function to ingest test results event from DAQ.
 */

const functions = require('firebase-functions');
const admin = require('firebase-admin');
const { PubSub } = require(`@google-cloud/pubsub`);
const iot = require('@google-cloud/iot');
const pubsub = new PubSub();

admin.initializeApp(functions.config().firebase);
const db = admin.firestore();

const iotClient = new iot.v1.DeviceManagerClient({
  // optional auth parameters.
});

function deleteQueryBatch(originId, query, resolve, reject, deleted) {
  const origins = db.collection('origin');
  query.get()
    .then((snapshot) => {
      if (snapshot.size === 0) {
        return 0;
      }
      if (!deleted[originId]) {
        deleted[originId] = []
      }
      const batch = db.batch();
      snapshot.docs.forEach((doc) => {
        deleted[originId].push(doc.id);
        const runDoc = origins.doc(originId).collection('runid').doc(doc.id);
        batch.delete(runDoc);
        batch.delete(doc.ref);
      });

      return batch.commit().then(() => {
        return snapshot.size;
      });
    }).then((numDeleted) => {
      if (numDeleted === 0) {
        resolve();
        return;
      }
      process.nextTick(() => {
        deleteQueryBatch(originId, query, resolve, reject, deleted);
      });
    })
    .catch(reject);
}

exports.daq_cleanup_crontab = functions.runWith({ timeoutSeconds: 300 }).pubsub.schedule('0 2 * * *')
  .onRun((context) => {
    const origins = db.collection('origin');
    const deleted = {};
    const ports = {};
    return origins.get().then((snapshot) => {
      return Promise.all(snapshot.docs.map((origin) => {
        const expiration = origins.doc(origin.id).collection('expiration');
        return new Promise((resolve, reject) => {
          const query = expiration.where("expiration", "<=", new Date().toISOString()).limit(100);
          deleteQueryBatch(origin.id, query, resolve, reject, deleted);
        });
      }));
    }).then(() => {
      // get ports for each origin
      return Promise.all(Object.keys(deleted).map((originId) => {
        return origins.doc(originId).collection('port').get().then((snapshot) => {
          ports[originId] = snapshot.docs.map((doc) => doc.id);
        });
      }));
    }).then(() => {
      // delete run ids under port
      return Promise.all(Object.keys(ports).map((originId) => {
        return Promise.all(ports[originId].map((port) => {
          const runids = origins.doc(originId).collection("port").doc(port).collection("runid");
          return Promise.all(deleted[originId].map((runid) => {
            return runids.doc(runid).delete();
          }));
        }));
      }));
    });
  });

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

  const siteDoc = db.collection('site').doc(siteName);
  const originDoc = db.collection('origin').doc(origin);
  const portDoc = originDoc.collection('port').doc('port' + message.port);
  const deviceDoc = originDoc.collection('device').doc(message.device_id);

  const updates = [
    originDoc.set({ 'updated': timestamp }),
    siteDoc.set({ 'updated': timestamp }),
    portDoc.set({ 'updated': timestamp }),
    deviceDoc.set({ 'updated': timestamp })
  ];
  if (message.config && message.config.run_info
    && message.config.run_info.expiration) {
    const expirationDoc = originDoc.collection('expiration').doc(message.runid);
    updates.push(expirationDoc.set({
      expiration: message.config.run_info.expiration
    }));
  }
  return Promise.all(updates).then(() => {
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
    const lastDoc = originDoc.collection('last').doc(message.name);
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
      if (!doUpdate) {
        return;
      }
      return Promise.all([
        runDoc.set({ 'updated': timestamp,
                     'last_name': message.name
                   }, { merge: true }),
        resultDoc.set(message),
        lastDoc.set(message),
        portRunDoc.set({ 'updated': timestamp }),
        deviceRunDoc.set({ 'updated': timestamp }),
      ]).then(() => {
        if (message.config) {
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
  const heartbeatDoc = originDoc.collection('runner').doc('heartbeat');
  return Promise.all([
    originDoc.set({ 'updated': timestamp }),
    heartbeatDoc.get().then((result) => {
      const current = result.data();
      if (!current || !current.message || current.message.timestamp < message.timestamp)
        return heartbeatDoc.set({
          'updated': timestamp,
          message
        });
    })
  ]);
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

exports.device_target = functions.pubsub.topic('target').onPublish((event) => {
  const registryId = event.attributes.deviceRegistryId;
  const deviceId = event.attributes.deviceId;
  const subFolder = event.attributes.subFolder || 'unknown';
  const base64 = event.data;
  const msgString = Buffer.from(base64, 'base64').toString();
  const msgObject = JSON.parse(msgString);

  console.log(deviceId, subFolder, msgObject);

  device_doc = getDeviceDoc(registryId, deviceId).collection('events').doc(subFolder);

  msgObject.data.forEach((data) => device_doc.set(data))
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

  return pubsub
    .topic(topicName)
    .publish(dataBuffer, attributes)
    .then(messageId => {
      console.debug(`Message ${messageId} published to ${topicName}.`);
    })
    .catch(err => {
      console.error('publishing error:', err);
    });
}
