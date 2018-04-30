columns = [ ]
rows = [ ]

timestamp = { }

function ensureGridColumn(label) {
  if (columns.indexOf(label) < 0) {
    console.log('adding table column', label);
    columns.push(label);
    for (row of rows) {
      const testRow = document.querySelector(`#testgrid table tr[label=${row}]`)
      const columnElement = document.createElement('td');
      testRow.appendChild(columnElement);
      columnElement.setAttribute('label', label);
    }
  }
  setGridValue('header', label, undefined, label);
}

function ensureGridRow(label) {
  if (rows.indexOf(label) < 0) {
    console.log('adding table row', label);
    rows.push(label)
    const testTable = document.querySelector("#testgrid table")
    const rowElement = document.createElement('tr');
    testTable.appendChild(rowElement)
    rowElement.setAttribute('label', label)
    for (column of columns) {
      const columnElement = document.createElement('td');
      rowElement.appendChild(columnElement);
      columnElement.setAttribute('label', column);
    }
  }
  setGridValue(label, 'group', undefined, label);
}

function setGridValue(row, column, timestamp, value) {
  const selector = `#testgrid table tr[label=${row}] td[label=${column}]`;
  const targetElement = document.querySelector(selector)

  if (targetElement) {
    const previous = targetElement.getAttribute('time');
    if (!previous || timestamp > previous) {
      if (timestamp) {
        targetElement.setAttribute('time', timestamp);
      }
      targetElement.innerHTML = value;
    }
    const rowTime = document
          .querySelector(`#testgrid table tr[label=${row}]`).getAttribute('time');
    updateTimeClass(targetElement, rowTime);
  } else {
    console.log('cant find', selector);
  }
  return targetElement;
}

function setRowState(row, timestamp) {
  const rowElement = document.querySelector(`#testgrid table tr[label=${row}]`);
  const previous = rowElement.getAttribute('time');
  if (!previous || timestamp > previous) {
    rowElement.setAttribute('time', timestamp);
    const allEntries = rowElement.querySelectorAll('td');
    allEntries.forEach((entry) => {
      updateTimeClass(entry, timestamp);
    });
  }
}

function updateTimeClass(entry, target) {
  const value = entry.getAttribute('time');
  if (value) {
    if (value >= target) {
      entry.classList.remove('old');
      entry.classList.add('current');
    } else {
      entry.classList.add('old');
      entry.classList.remove('current');
    }
  }
}

function handle_result(origin, port, runid, test, result) {
  ensureGridRow(port);
  console.log(`updating ${port} ${test} = ${result.runid} with ${result.code}`);
  ensureGridColumn(test);
  status = Number(result.code) ? 'fail' : 'pass';
  setRowState(port, result.runid);
  target = setGridValue(port, test, result.runid, status);
  if (target) {
    target.classList.remove(['fail', 'pass'])
    target.classList.add(status);
  }
}

function watcher_add(ref, collection, limit, handler) {
  const base = ref.collection(collection)
  const target = limit ? limit(base) : base;
  target.onSnapshot((snapshot) => {
    delay = 100;
    snapshot.docChanges.forEach((change) => {
      if (change.type == 'added') {
        setTimeout(() => handler(ref.collection(collection).doc(change.doc.id), change.doc.id), delay);
        delay = delay + 100;
      }
    });
  }, (e) => console.error(e));
}

function setup_triggers() {
  var db = firebase.firestore();
  const settings = {
    timestampsInSnapshots: true
  };
  db.settings(settings);

  const latest = (ref) => {
    return ref.orderBy('timestamp', 'desc').limit(3);
  }
  
  watcher_add(db, "origin", undefined, (ref, origin_id) => {
    watcher_add(ref, "port", undefined, (ref, port_id) => {
      watcher_add(ref, "runid", latest, (ref, runid_id) => {
        watcher_add(ref, "test", undefined, (ref, test_id) => {
          ref.get().then((result) => {
            handle_result(origin_id, port_id, runid_id, test_id, result.data());
          });
        });
      });
    });
  });
}

document.addEventListener('DOMContentLoaded', function() {
  try {
    let app = firebase.app();
    document.getElementById('load').innerHTML = 'Firebase loaded';
    ensureGridRow('header');
    ensureGridColumn('group');
    setup_triggers();
  } catch (e) {
    console.error(e);
    document.getElementById('load').innerHTML = 'Error loading the Firebase SDK, check the console.';
  }
});
