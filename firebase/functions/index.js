const functions = require('firebase-functions');
const admin = require('firebase-admin');

const expiry_ms = 1000 * 60 * 60 * 24;

admin.initializeApp(functions.config().firebase);
var db = admin.firestore();

exports.daq_firestore = functions.pubsub.topic('daq_runner').onPublish((event) => {
  const message = event.json;
  const origin = event.attributes.origin;
  const port = 'port-' + message.port;
  const timestr = new Date().toTimeString();
  const timestamp = Date.now();
  const expired = timestamp - expiry_ms;

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
          const del_doc = port_doc.collection('runid').doc(old_doc.id);
          del_doc.delete().catch((error) => {
            console.error('Error deleting doc ', old_doc.id, error);
          });
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
