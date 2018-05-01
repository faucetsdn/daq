
columns = [ ]
rows = [ ]

function appendTestCell(parent, label) {
  const columnElement = document.createElement('td');
  columnElement.setAttribute('label', label);
  columnElement.classList.add('old');
  parent.appendChild(columnElement);
}

function ensureGridColumn(label) {
  if (columns.indexOf(label) < 0) {
    columns.push(label);
    for (row of rows) {
      const testRow = document.querySelector(`#testgrid table tr[label=${row}]`)
      appendTestCell(testRow, label);
    }
  }
  setGridValue('header', label, undefined, label);
}

function ensureGridRow(label) {
  if (rows.indexOf(label) < 0) {
    rows.push(label)
    const testTable = document.querySelector("#testgrid table")
    const rowElement = document.createElement('tr');
    testTable.appendChild(rowElement)
    rowElement.setAttribute('label', label)
    for (column of columns) {
      appendTestCell(rowElement, column);
    }
  }
  setGridValue(label, 'group', undefined, label);
}

function setGridValue(row, column, runid, value) {
  const selector = `#testgrid table tr[label=${row}] td[label=${column}]`;
  const targetElement = document.querySelector(selector)

  if (targetElement) {
    const previous = targetElement.getAttribute('runid');
    if (!previous || runid >= previous) {
      if (runid) {
        targetElement.setAttribute('runid', runid);
      }
      targetElement.innerHTML = value;
      targetElement.setAttribute('status', value);
    }
    const rowTime = document
          .querySelector(`#testgrid table tr[label=${row}]`).getAttribute('runid');
    updateTimeClass(targetElement, rowTime);
  } else {
    console.error('cant find', selector);
  }
  return targetElement;
}

function setRowState(row, runid) {
  const rowElement = document.querySelector(`#testgrid table tr[label=${row}]`);
  const previous = rowElement.getAttribute('runid');
  if (!previous || runid > previous) {
    rowElement.setAttribute('runid', runid);
    const allEntries = rowElement.querySelectorAll('td');
    allEntries.forEach((entry) => {
      updateTimeClass(entry, runid);
    });
  }
}

function updateTimeClass(entry, target) {
  const value = entry.getAttribute('runid');
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

function getQueryParam(field) {
  var reg = new RegExp( '[?&]' + field + '=([^&#]*)', 'i' );
  var string = reg.exec(window.location.href);
  return string ? string[1] : null;
}

function statusUpdate(message, e) {
  console.log(message);
  if (e) {
    console.error(e);
    message = message + ' ' + String(e)
  }
  document.getElementById('status').innerHTML = message;
}

function getResultStatus(result) {
  if (result.state) {
    return result.state;
  }
  if (result.exception) {
    return 'fail';
  }
  return Number(result.code) ? 'fail' : 'pass';
}

function handle_result(origin, port, runid, test, result) {
  ensureGridRow(port);
  ensureGridColumn(test);
  const status = getResultStatus(result);
  statusUpdate(`updating ${port} ${test} = ${result.runid} with ${status}`)
  setRowState(port, result.runid);
  setGridValue(port, test, result.runid, status);
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

function list_origins(db) {
  const link_group = document.getElementById('origins');
  db.collection('origin').get().then((snapshot) => {
    snapshot.forEach((origin) => {
      origin_id = origin.id;
      const origin_link = document.createElement('a');
      origin_link.setAttribute('href', '/?origin=' + origin_id);
      origin_link.innerHTML = origin_id;
      link_group.appendChild(origin_link);
      link_group.appendChild(document.createElement('p'));
    });
  }).catch((e) => statusUpdate('origin list error', e));
}

function setup_triggers() {
  var db = firebase.firestore();
  const settings = {
    timestampsInSnapshots: true
  };
  db.settings(settings);

  const origin_id = getQueryParam('origin');

  if (origin_id) {
    ensureGridRow('header');
    ensureGridColumn('group');
    trigger_origin(db, origin_id);
  } else {
    list_origins(db);
  }
}

function trigger_origin(db, origin_id) {
  const latest = (ref) => {
    return ref.orderBy('timestamp', 'desc').limit(3);
  }

  ref = db.collection('origin').doc(origin_id);
  watcher_add(ref, "port", undefined, (ref, port_id) => {
    watcher_add(ref, "runid", latest, (ref, runid_id) => {
      watcher_add(ref, "test", undefined, (ref, test_id) => {
        ref.onSnapshot((result) => {
          // TODO: Handle results going away.
          handle_result(origin_id, port_id, runid_id, test_id, result.data());
        });
      });
    });
  });
}

document.addEventListener('DOMContentLoaded', function() {
  try {
    let app = firebase.app();
    statusUpdate('System initialized.');
    setup_triggers();
  } catch (e) {
    statusUpdate('Loading error', e)
  }
});
