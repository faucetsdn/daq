/**
 * Simple function to transfer event data to firestore.
 *
 * State events come across on their own topic, but it would also be nice
 * to be able to process them using the same topic as regular messages.
 * The udmi_state function adds a subFolder attribute to the message and sends
 * along on the other topic. Logic later down the pipe can look for this
 * and handle appropriately. This has no impact on the device-side exchange,
 * purely the back-end processing (namely schema validator).
 */

const {PubSub} = require('@google-cloud/pubsub');
const pubsub = new PubSub();
const admin = require('firebase-admin');
admin.initializeApp();
var db = admin.firestore();

const settings = {
  timestampsInSnapshots: true
};
db.settings(settings)

const EXPIRY_MS = 1000 * 60 * 60 * 24;

function publishPubsubMessage(topicName, data, attributes) {
  const dataBuffer = Buffer.from(JSON.stringify(data));

  pubsub
    .topic(topicName)
    .publish(dataBuffer, attributes)
    .then(messageId => {
      console.info(`Message ${messageId} published.`);
    })
    .catch(err => {
      console.error('Publishing error:', err);
    });
}

function get_device_doc(registryId, deviceId) {
  const timestr = new Date().toJSON();
  const reg = db.collection('registries').doc(registryId);
  reg.set({'updated': timestr});
  const dev = reg.collection('devices').doc(deviceId);
  dev.set({'updated': timestr});
  return dev;
}

exports.udmi_firebase = event => {
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

exports.udmi_state = event => {
  const attributes = event.attributes;
  const dataBuffer = Buffer.from(event.data, 'base64');
  const payload = JSON.parse(dataBuffer.toString('utf8'));

  attributes.subFolder = 'state';

  publishPubsubMessage('target', payload, attributes);
};
