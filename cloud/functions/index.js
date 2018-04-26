const functions = require('firebase-functions');
const admin = require('firebase-admin');

admin.initializeApp(functions.config().firebase);
var db = admin.firestore();

exports.daq_firestore = functions.pubsub.topic('daq_runner').onPublish((event) => {
  const message = event.json;
  const origin = event.attributes.origin;
  const port = 'port-' + message.port;
  const test = message.name;
  db.collection('origin').doc(origin).collection('port').doc(port).collection('test').doc(test).set(message);
  return null;
});
