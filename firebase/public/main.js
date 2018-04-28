document.addEventListener('DOMContentLoaded', function() {
  try {
    let app = firebase.app();
    document.getElementById('load').innerHTML = 'Firebase loaded';
  } catch (e) {
    console.error(e);
    document.getElementById('load').innerHTML = 'Error loading the Firebase SDK, check the console.';
  }

  var db = firebase.firestore();
  const settings = {
    timestampsInSnapshots: true
  };
  db.settings(settings);

  function watcher_add(ref, collection, handler) {
    ref.collection(collection).onSnapshot((snapshot) => {
      delay = 100;
      snapshot.docChanges.forEach((change) => {
        if (change.type == 'added') {
          setTimeout(() => handler(ref.collection(collection).doc(change.doc.id), change.doc.id), delay);
          delay = delay + 100;
        }
      });
    }, (e) => console.error(e));
  }

  function handle_result(origin, port, runid, test, result) {
    console.log(origin, port, runid, test, result);
  }

  watcher_add(db, "origin", (ref, origin_id) => {
    watcher_add(ref, "port", (ref, port_id) => {
      watcher_add(ref, "runid", (ref, runid_id) => {
        watcher_add(ref, "test", (ref, test_id) => {
          ref.get().then((result) => {
            handle_result(origin_id, port_id, runid_id, test_id, result.data());
          });
        });
      });
    });
  });
});
