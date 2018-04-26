const functions = require('firebase-functions');
const admin = require('firebase-admin');

admin.initializeApp(functions.config().firebase);
var db = admin.firestore();
var docRef = db.collection('users').doc('alovelace');

exports.addMessage = functions.https.onRequest((req, res) => {
  const original = req.query.text;

  docRef.set({
    original: original
  }).then(() => {
    console.log('User insert finished');
    res.send('User insert finished');
    return null
  });
});
