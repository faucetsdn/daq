/**
 * Simple file to handle test results events from DAQ.
 * Uses firebase for data management, and renders straight to HTML.
 */

const PORT_ROW_COUNT = 25;
const ROW_TIMEOUT_SEC = 500;

const display_columns = [ ];
const display_rows = [ ];
const row_timestamps = {};

const data_state = {};

let last_result_time_sec = 0;

const origin_id = getQueryParam('origin');
const port_id = getQueryParam('port');
const registry_id = getQueryParam('registry');
const device_id = getQueryParam('device');
const run_id = getQueryParam('runid');

var db;

document.addEventListener('DOMContentLoaded', () => {
  db = firebase.firestore();
  const settings = {
  };
  db.settings(settings);
});

function appendTestCell(row, column) {
  const columnElement = document.createElement('td');
  columnElement.setAttribute('label', column);
  columnElement.setAttribute('row', row);
  columnElement.classList.add('old');
  const parent = document.querySelector(`#testgrid table tr[label="${row}"]`)
  parent.appendChild(columnElement);
}

function ensureGridColumn(label, content) {
  if (display_columns.indexOf(label) < 0) {
    display_columns.push(label);
    for (row of display_rows) {
      appendTestCell(row, label);
    }
  }
  setGridValue('header', label, undefined, content || label);
}

function ensureColumns(columns) {
  for (column of columns) {
    ensureGridColumn(column);
  }
  ensureGridColumn('info');
  ensureGridColumn('timer');
  ensureGridColumn('report');
}

function ensureGridRow(label, content, max_rows) {
  let added = false;
  if (display_rows.indexOf(label) < 0) {
    display_rows.push(label)
    const testTable = document.querySelector("#testgrid table")
    const tableRows = testTable.querySelectorAll('tr');
    const existingRows = (tableRows && Array.from(tableRows).slice(1)) || [];

    const rowElement = document.createElement('tr');

    if (max_rows) {
      for (row of existingRows) {
        if (label > row.getAttribute('label')) {
          testTable.insertBefore(rowElement, row);
          added = true;
          break;
        }
      }
    }

    if (!added) {
      testTable.appendChild(rowElement)
      added = true;
    }

    rowElement.setAttribute('label', label)
    for (column of display_columns) {
      appendTestCell(label, column);
    }

    if (max_rows && existingRows) {
      const extraRows = existingRows.slice(max_rows - 1);
      for (row of extraRows) {
        row.remove();
      }
    }
  }
  setGridValue(label, 'row', undefined, content || label);
  return added;
}

function setGridValue(row, column, runid, value) {
  const selector = `#testgrid table tr[label="${row}"] td[label="${column}"]`;
  const targetElement = document.querySelector(selector);

  if (targetElement) {
    const previous = targetElement.getAttribute('runid');
    if (!previous || runid >= previous) {
      if (runid) {
        targetElement.setAttribute('runid', runid);
      }
      if (value) {
        targetElement.innerHTML = value;
        targetElement.setAttribute('status', value);
      }
    }
    const rowElement = document.querySelector(`#testgrid table tr[label="${row}"]`);
    const rowTime = rowElement.getAttribute('runid');
    const rowPrev = rowElement.getAttribute('prev');
    updateTimeClass(targetElement, rowTime, rowPrev);
  } else {
    console.error('Could not find', selector);
  }
  return targetElement;
}

function setRowClass(row, timeout) {
  const rowElement = document.querySelector(`#testgrid table tr[label="${row}"]`);
  rowElement.classList.toggle('timeout', timeout);
}

function setRowState(row, new_runid) {
  const rowElement = document.querySelector(`#testgrid table tr[label="${row}"]`);
  let runid = rowElement.getAttribute('runid') || 0;
  let prev = rowElement.getAttribute('prev') || 0;
  console.log('rowstate', row, 'mudgee', new_runid, runid, prev);
  if (runid === new_runid) {
    return;
  } else if (!runid || new_runid > runid) {
    rowElement.setAttribute('prev', runid);
    rowElement.setAttribute('runid', new_runid);
    prev = runid
    runid = new_runid
  } else if (!prev || new_runid > prev) {
    rowElement.setAttribute('prev', new_runid);
    prev = new_runid
  } else {
    return;
  }
  const allEntries = rowElement.querySelectorAll('td');
  allEntries.forEach((entry) => {
    updateTimeClass(entry, runid, prev);
  });
}

function updateTimeClass(entry, target, prev) {
  const value = entry.getAttribute('runid');
  const row = entry.getAttribute('row');
  const column = entry.getAttribute('label');
  console.log('update', row, column, value, target, prev);
  if (value === target) {
    entry.classList.add('current');
    entry.classList.remove('old', 'gone');
  } else if (value === prev) {
    entry.classList.add('old');
    entry.classList.remove('current', 'gone');
  } else {
    entry.classList.add('gone');
    entry.classList.remove('current', 'old');
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
  console.log(result)
  if (result.exception) {
    return 'serr';
  }
  if (result.state) {
    return result.state;
  }
  if (Number(result.code)) {
    return 'merr';
  }
  return '????';
}

function handleOriginResult(origin, port, runid, test, result) {
  if (result.timestamp > last_result_time_sec) {
    last_result_time_sec = result.timestamp;
  }
  if (!row_timestamps[port] || row_timestamps[port] < result.timestamp) {
    row_timestamps[port] = result.timestamp;
  }
  const href =`?origin=${origin}&port=${port}`;
  ensureGridRow(port, `<a href="${href}">${port}</a>`);
  ensureGridColumn(test);
  const status = getResultStatus(result);
  statusUpdate(`Updating ${port} ${test} run ${runid} with '${status}'.`)
  setRowState(port, runid);
  const gridElement = setGridValue(port, test, runid, status);
  if (result.report) {
    addReportBucket(origin, port, runid, result.report);
  }
  if (test === 'info') {
    makeConfigLink(gridElement, status, port, runid);
  }
  if (test == 'startup') {
    makeActivateLink(gridElement, port);
  }
}

function makeConfigLink(element, info, port, runid) {
  const parts = info.split('/');
  const device_id = parts[0];
  const device_link = document.createElement('a');
  device_link.href = `config.html?origin=${origin_id}&device=${device_id}&port=${port}&runid=${runid}`;
  device_link.innerHTML = element.innerHTML;
  element.innerHTML = '';
  element.appendChild(device_link);
}

function activateRun(port) {
  console.log('Activate run port', port);
  const origin_doc = db.collection('origin').doc(origin_id);
  const control_doc = origin_doc.collection('control').doc(port).collection('config').doc('definition');
  control_doc.update({
    'config.paused': false
  });
}

function makeActivateLink(element, port) {
  element.onclick = () => activateRun(port)
}

function addReportBucket(origin, row, runid, reportName) {
  const storage = firebase.app().storage();
  storage.ref().child(reportName).getDownloadURL().then((url) => {
    setGridValue(row, 'report', runid, `<a href="${url}">${reportName}</a>`);
  }).catch((e) => {
    console.error(e);
  });
}

function handlePortResult(origin, port, runid, test, result) {
  const timestamp = result.timestamp;
  if (timestamp > last_result_time_sec) {
    last_result_time_sec = timestamp;
  }
  ensureGridRow(runid, runid, PORT_ROW_COUNT);
  ensureGridColumn(test);
  const status = getResultStatus(result);
  statusUpdate(`Updating ${port} ${test} run ${runid} with '${status}'.`)
  setRowState(runid, runid);
  setGridValue(runid, test, runid, status);
  if (result.info) {
    setGridValue(runid, 'info', runid, result.info);
  }
  const element = setGridValue(runid, 'timer', runid);
  const oldtime = element.getAttribute('timer') || 0;
  if ((timestamp && oldtime < timestamp) || oldtime == 0) {
    element.setAttribute('timer', timestamp);
    setGridValue(runid, 'timer', runid, timestamp);
  }
  if (result.report) {
    addReportBucket(origin, runid, runid, result.report);
  }
}

function watcherAdd(ref, collection, limit, handler) {
  const base = ref.collection(collection);
  const target = limit ? limit(base) : base;
  target.onSnapshot((snapshot) => {
    let delay = 100;
    snapshot.docChanges().forEach((change) => {
      if (change.type === 'added') {
        setTimeout(() => handler(ref.collection(collection).doc(change.doc.id), change.doc.id), delay);
        delay = delay + 100;
      }
    });
  }, (e) => console.error(e));
}

function listOrigins(db) {
  const link_group = document.getElementById('origins');
  db.collection('origin').get().then((snapshot) => {
    snapshot.forEach((origin) => {
      origin = origin.id;
      const origin_link = document.createElement('a');
      origin_link.setAttribute('href', '/?origin=' + origin);
      origin_link.innerHTML = origin;
      link_group.appendChild(origin_link);
      link_group.appendChild(document.createElement('p'));
    });
  }).catch((e) => statusUpdate('origin list error', e));
}

function listRegistries(db) {
  db.collection('registry').get().then((snapshot) => {
    snapshot.forEach((registry) => {
      listDevices(db, registry.id);
    });
  }).catch((e) => statusUpdate('registry list error', e));
}

function listDevices(db, registryId) {
  const link_group = document.getElementById('devices');
  db
    .collection('registry').doc(registryId)
    .collection('device').get().then((snapshot) => {
      snapshot.forEach((device) => {
        const deviceId = device.id;
        const origin_link = document.createElement('a');
        origin_link.setAttribute('href', `/?registry=${registryId}&device=${deviceId}`);
        origin_link.innerHTML = `${registryId}/${deviceId}`
        link_group.appendChild(origin_link);
        link_group.appendChild(document.createElement('p'));
      });
    }).catch((e) => statusUpdate('registry list error', e));
}

function dashboardSetup() {
  if (port_id) {
    ensureGridRow('header');
    ensureGridColumn('row', port_id);
    triggerPort(db, origin_id, port_id);
  } else if (origin_id) {
    ensureGridRow('header');
    ensureGridColumn('row', 'port');
    triggerOrigin(db, origin_id);
  } else if (registry_id && device_id) {
    triggerDevice(db, registry_id, device_id);
  } else {
    listOrigins(db);
    listRegistries(db);
  }

  return origin_id;
}

function triggerOrigin(db, origin_id) {
  const latest = (ref) => {
    return ref.orderBy('updated', 'desc').limit(3);
  };

  let ref = db.collection('origin').doc(origin_id);
  ref.collection('runner').doc('heartbeat').onSnapshot((result) => {
    const message = result.data().message;
    message.states && ensureColumns(message.states);
    const description = document.querySelector('#description .description');
    description.innerHTML = message.description;
    description.href = `config.html?origin=${origin_id}`;
    const version = `DAQ v${message.version}`;
    document.querySelector('#version').innerHTML = version
  });
  watcherAdd(ref, "port", undefined, (ref, port_id) => {
    watcherAdd(ref, "runid", latest, (ref, runid_id) => {
      watcherAdd(ref, "test", undefined, (ref, test_id) => {
        ref.onSnapshot((result) => {
          // TODO: Handle results going away.
          handleOriginResult(origin_id, port_id, runid_id, test_id, result.data());
        });
      });
    });
  });
}

function triggerPort(db, origin_id, port_id) {
  const latest = (ref) => {
    return ref.orderBy('updated', 'desc').limit(PORT_ROW_COUNT);
  };

  const origin_doc = db.collection('origin').doc(origin_id);
  const heartbeat_doc = origin_doc.collection('runner').doc('heartbeat');

  heartbeat_doc.onSnapshot((result) => {
    ensureColumns(result.data().message.states)
  });

  watcherAdd(origin_doc.collection('port').doc(port_id), "runid", latest, (ref, runid_id) => {
    watcherAdd(ref, "test", undefined, (ref, test_id) => {
      ref.onSnapshot((result) => {
        // TODO: Handle results going away.
        handlePortResult(origin_id, port_id, runid_id, test_id, result.data());
      });
    });
  });
}

function triggerDevice(db, registry_id, device_id) {
  statusUpdate('Setup device trigger ' + device_id);
  db
    .collection('registry').doc(registry_id)
    .collection('device').doc(device_id)
    .collection('telemetry').doc('latest')
    .onSnapshot((snapshot) => {
      statusUpdate('');
      const hue = Math.floor(snapshot.data().random * 360);
      const hsl = `hsl(${hue}, 80%, 50%)`;
      console.log(hsl)
      document.body.style.backgroundColor = hsl;
    });
}

function interval_updater() {
  if (last_result_time_sec) {
    const time_delta_sec = Math.floor(Date.now()/1000.0 - last_result_time_sec);
    document.getElementById('update').innerHTML = `Last update ${time_delta_sec} sec ago.`
  }
  for (const row in row_timestamps) {
    const last_update = new Date(row_timestamps[row]);
    const time_delta_sec = Math.floor((Date.now() - last_update)/1000.0);
    const selector=`#testgrid table tr[label="${row}"`;
    const runid = document.querySelector(selector).getAttribute('runid');
    setGridValue(row, 'timer', runid, `${time_delta_sec} sec`);
    setRowClass(row, time_delta_sec > ROW_TIMEOUT_SEC);
  }
}

function applySchema(editor, schema_url) {
  if (!schema_url) {
    return;
  }

  // Not sure why this is required, but without it the system complains it's not defined??!?!
  const refs = {
    'http://json-schema.org/draft-07/schema#': true
  };

  console.log(`Loading editor schema ${schema_url}`);
  fetch(schema_url)
      .then(response => response.json())
      .then(json => editor.setSchema(json, refs))
      .catch(rejection => console.log(rejection));
}

function getJsonEditor(container_id, onChange, schema_url) {
  const container = document.getElementById(container_id);
  const options = {
    mode: onChange ? undefined : 'view',
    onChangeJSON: onChange
  };
  const editor = new JSONEditor(container, options);
  applySchema(editor, schema_url);
  return editor;
}

function setDatedStatus(attribute, value) {
  data_state[attribute] = value;

  const element = document.getElementById('config_body');
  element.classList.toggle('dirty', data_state.dirty > data_state.saved);
  element.classList.toggle('saving', data_state.pushed > data_state.saved);
  element.classList.toggle('dated', data_state.saved > data_state.updated);
  element.classList.toggle('provisional', data_state.provisional);
}

function pushConfigChange(config_editor, config_doc) {
  const json = config_editor.get();
  const timestamp = new Date().toJSON();
  config_doc.update({
    'config': json,
    'timestamp': timestamp
  });
  setDatedStatus('pushed', timestamp);
}

function setDirtyState() {
  setDatedStatus('dirty', new Date().toJSON());
}

function loadEditor(config_doc, element_id, label, onConfigEdit, schema) {
  const editor = getJsonEditor(element_id, onConfigEdit, schema);
  editor.setName(label);
  editor.set(null);
  config_doc.onSnapshot((snapshot) => {
    const firstUpdate = editor.get() == null;
    let snapshot_data = snapshot.data();
    snapshot_data && editor.update(snapshot_data.config);
    if (firstUpdate) {
      editor.expandAll();
    }
    if (onConfigEdit) {
      setDatedStatus('saved', snapshot_data && snapshot_data.saved);
    } else {
      setDatedStatus('updated', snapshot_data && snapshot_data.updated);
      const snapshot_config = (snapshot_data && snapshot_data.config && snapshot_data.config.config) || {};
      setDatedStatus('provisional', !snapshot_config.run_info);
    }
  });
  return editor;
}

function loadJsonEditors() {
  let latest_doc;
  let config_doc;
  let schema_url;
  const subtitle = device_id
        ? `${origin_id} device ${device_id}`
        : `${origin_id} system`;
  document.getElementById('title_origin').innerHTML = subtitle;

  const origin_doc = db.collection('origin').doc(origin_id);
  if (device_id) {
    config_doc = origin_doc.collection('device').doc(device_id).collection('config').doc('definition');
    latest_doc = origin_doc.collection('device').doc(device_id).collection('config').doc('latest');
    schema_url = 'schema_device.json';
  } else {
    config_doc = origin_doc.collection('runner').doc('setup').collection('config').doc('definition');
    latest_doc = origin_doc.collection('runner').doc('setup').collection('config').doc('latest');
    schema_url = 'schema_system.json';
  }
  loadEditor(latest_doc, 'latest_editor', 'latest', null);
  const config_editor = loadEditor(config_doc, 'config_editor', 'config', setDirtyState, schema_url);

  document.querySelector('#config_body .save_button').onclick = () => pushConfigChange(config_editor, config_doc)
}

function authenticated(userData) {
  if (!userData) {
    statusUpdate('Authentication failed, please sign in.');
    return;
  }

  const perm_doc = db.collection('permissions').doc(userData.uid);
  const user_doc = db.collection('users').doc(userData.uid);
  const timestamp = new Date().toJSON();
  user_doc.set({
    name: userData.displayName,
    email: userData.email,
    updated: timestamp
  }).then(function() {
    statusUpdate('User info updated');
    perm_doc.get().then((doc) => {
      if (doc.exists && doc.data().enabled) {
        setupUser();
      } else {
        statusUpdate('User not enabled, contact your system administrator.');
      }
    });
  }).catch((e) => statusUpdate('Error updating user info', e));
}

function setupUser() {
  try {
    if (document.getElementById('config_editor')) {
      loadJsonEditors();
    } else {
      dashboardSetup();
    }
    statusUpdate('System initialized.');
    setInterval(interval_updater, 1000);
  } catch (e) {
    statusUpdate('Loading error', e);
  }
}
