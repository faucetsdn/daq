/**
 * Simple function to transfer event data to firestore.
 */

const admin = require('firebase-admin');
admin.initializeApp();
var db = admin.firestore();

const settings = {
  timestampsInSnapshots: true
};
db.settings(settings)

const EXPIRY_MS = 1000 * 60 * 60 * 24;

function get_device_doc(registryId, deviceId) {
  const timestr = new Date().toJSON();
  const reg = db.collection('registry').doc(registryId);
  reg.set({'updated': timestr});
  const dev = reg.collection('device').doc(deviceId);
  dev.set({'updated': timestr});
  return dev;
}

exports.device_event = event => {
  const registryId = event.attributes.deviceRegistryId;
  const deviceId = event.attributes.deviceId;
  const subFolder = event.attributes.subFolder || 'unknown';
  const base64 = event.data;
  const msgString = Buffer.from(base64, 'base64').toString();
  const msgObject = JSON.parse(msgString);

  console.log(deviceId, subFolder, msgObject);

  const device_doc = get_device_doc(registryId, deviceId).collection('events').doc(subFolder);
  device_doc.set(msgObject);

  return null;
}

