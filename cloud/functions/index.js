const functions = require('firebase-functions');
const admin = require('firebase-admin');

admin.initializeApp(functions.config().firebase);
var db = admin.firestore();

exports.daq_firestore = functions.pubsub.topic('daq_runner').onPublish((event) => {
  const message = event.json;
  const origin = event.attributes.origin;
  const port = 'port-' + message.port;
  const timestr = new Date().toTimeString();
  message.updated = timestr;

  const origin_doc = db.collection('origin').doc(origin);
  origin_doc.set({'updated': timestr});
  const port_doc = origin_doc.collection('port').doc(port);
  port_doc.set({'updated': timestr});
  const run_doc = port_doc.collection('runid').doc(message.runid);
  run_doc.set({'updated': timestr});
  const test_doc = run_doc.collection('test').doc(message.name);
  test_doc.set(message);
  
  return null;
});
