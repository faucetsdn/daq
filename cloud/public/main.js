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

  function handle_result(origin, port, runid, test, result) {
    console.log(origin, port, runid, test, result.updated);
  }

  db.collection("origin").get().then((origin_snapshot) => {
    origin_snapshot.forEach((origin_doc) => {
      console.log(`${origin_doc.id}`);
      origin_db = db.collection("origin").doc(origin_doc.id);
      origin_db.collection("port").get().then((port_snapshot) => {
        port_snapshot.forEach((port_doc) => {
          console.log(`${origin_doc.id} ${port_doc.id}`);
          port_db = origin_db.collection("port").doc(port_doc.id);
          port_db.collection("runid").get().then((runid_snapshot) => {
            runid_snapshot.forEach((runid_doc) => {
              console.log(`${origin_doc.id} ${port_doc.id} ${runid_doc.id}`);
              runid_db = port_db.collection("runid").doc(runid_doc.id);
              runid_db.collection("test").get().then((test_snapshot) => {
                test_snapshot.forEach((test_doc) => {
                  console.log(`${origin_doc.id} ${port_doc.id} ${runid_doc.id} ${test_doc.id}`);
                  test_db = runid_db.collection("test").doc(test_doc.id);
                  test_db.get().then((result) => {
                    if (result.data()) {
                      handle_result(origin_doc.id, port_doc.id, runid_doc.id, test_doc.id, result.data())
                    }
                  });
                });
              });
            });
          });
        });
      });
    });
  });
});
