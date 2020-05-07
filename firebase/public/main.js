/**
 * Simple file to handle test results events from DAQ.
 * Uses firebase for data management, and renders straight to HTML.
 */

const ROW_TIMEOUT_SEC = 500;
const display_columns = [];
const display_rows = [];
const row_timestamps = {};

const data_state = {};

let last_result_time_sec = 0;
let heartbeatTimestamp = 0;

const origin_id = getQueryParam('origin');
const site_name = getQueryParam('site');
const port_id = getQueryParam('port');
const registry_id = getQueryParam('registry');
const device_id = getQueryParam('device');
const run_id = getQueryParam('runid');
const from = getQueryParam('from');
const to = getQueryParam('to');
var db;
var activePorts = [];
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
}

function ensureGridRow(label, content) {
  let added = false;
  if (display_rows.indexOf(label) < 0) {
    display_rows.push(label)
    const testTable = document.querySelector("#testgrid table")
    const rowElement = document.createElement('tr');
    testTable.appendChild(rowElement)
    rowElement.setAttribute('label', label)
    for (column of display_columns) {
      appendTestCell(label, column);
    }
  }
  setGridValue(label, 'row', undefined, content || label);
  return added;
}

function setGridValue(row, column, runid, value, append) {
  const selector = `#testgrid table tr[label="${row}"] td[label="${column}"]`;
  const targetElement = document.querySelector(selector);
  if (targetElement) {
    const previous = targetElement.getAttribute('runid');
    if (!previous || !runid || runid >= previous) {
      if (runid) {
        targetElement.setAttribute('runid', runid);
      }
      if (value) {
        if (append) {
          targetElement.innerHTML += "<br />" + value;
        } else {
          targetElement.innerHTML = value;
          targetElement.setAttribute('status', value);
        }
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
  console.debug('rowstate', row, 'mudgee', new_runid, runid, prev);
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
  var reg = new RegExp('[?&]' + field + '=([^&#]*)', 'i');
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

function handleFileLinks(row, runid, result) {
  const paths = Object.keys(result).filter(key => key.indexOf("path") >= 0);
  if (paths.length) {
    const col = result.name;
    paths.forEach((path) => {
      let name = path.replace("_path", "");
      addReportBucket(row, col, runid, result[path], name);
    })
  }
}

function handleOriginResult(origin, port, runid, test, result) {
  if (result.timestamp > last_result_time_sec) {
    last_result_time_sec = result.timestamp;
  }
  if (!row_timestamps[port] || row_timestamps[port] < result.timestamp) {
    row_timestamps[port] = result.timestamp;
  }
  if (test === "terminate") {
    row_timestamps[port] = false;
  }
  const numPort = Number(port.replace('port', ''));
  const href = `?origin=${origin}&port=${numPort}`;
  ensureGridRow(port, `<a href="${href}">${port}</a>`);
  ensureGridColumn(test);
  const status = getResultStatus(result);
  statusUpdate(`Updating ${port} ${test} run ${runid} with '${status}'.`)
  setRowState(port, runid);
  setGridValue(port, 'active', runid, activePorts.has(numPort) + "")
  const gridElement = setGridValue(port, test, runid, status);
  handleFileLinks(port, runid, result);
  if (test === 'info') {
    makeConfigLink(gridElement, status, port, runid);
  }
  if (test == 'startup') {
    makeActivateLink(gridElement, port);
  }
}

function handleFilterResult(origin, site, runid, test, result) {
  const id = origin + runid;
  if (result.timestamp > last_result_time_sec) {
    last_result_time_sec = result.timestamp;
  }
  if ((!row_timestamps[id] && row_timestamps[id] !== false) || row_timestamps[id] < result.timestamp) {
    row_timestamps[id] = result.timestamp;
  }
  if (test === "terminate") {
    row_timestamps[id] = false;
  }

  ensureGridRow(id, runid);
  setGridValue(id, 'origin', runid, origin);
  setGridValue(id, 'port', runid, result.port);
  setGridValue(id, 'site', runid, site);
  ensureGridColumn(test);
  const status = getResultStatus(result);
  setRowState(id, runid);
  const gridElement = setGridValue(id, test, runid, status);
  handleFileLinks(id, runid, result);
  if (test === 'info') {
    makeConfigLink(gridElement, status, id, runid);
  }
  if (test == 'startup') {
    makeActivateLink(gridElement, id);
  }
}

function makeConfigLink(element, info, port, runid) {
  const parts = info.split('/');
  const deviceId = parts[0];
  const deviceLink = document.createElement('a');
  deviceLink.href = `config.html?origin=${origin_id}&device=${deviceId}&port=${port}&runid=${runid}`;
  deviceLink.innerHTML = element.innerHTML;
  element.innerHTML = '';
  element.appendChild(deviceLink);
}

function activateRun(port) {
  console.log('Activate run port', port);
  const originDoc = db.collection('origin').doc(origin_id);
  const controlDoc = originDoc.collection('control').doc(port).collection('config').doc('definition');
  controlDoc.update({
    'config.paused': false
  });
}

function makeActivateLink(element, port) {
  element.onclick = () => activateRun(port)
}

function addReportBucket(row, col, runid, path, name) {
  const storage = firebase.app().storage();
  if (!name) {
    name = path;
  }
  storage.ref().child(path).getDownloadURL().then((url) => {
    setGridValue(row, col, runid, `<a href="${url}">${name}</a>`, true);
  }).catch((e) => {
    console.error(e);
  });
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

function listSites(db) {
  const linkGroup = document.querySelector('#listings .sites');
  db.collection('site').get().then((snapshot) => {
    snapshot.forEach((site_doc) => {
      site = site_doc.id;
      const siteLink = document.createElement('a');
      siteLink.setAttribute('href', '/?site=' + site);
      siteLink.innerHTML = site;
      linkGroup.appendChild(siteLink);
      linkGroup.appendChild(document.createElement('p'));
    });
  }).catch((e) => statusUpdate('registry list error', e));
}

function listOrigins(db) {
  const linkGroup = document.querySelector('#listings .origins');
  db.collection('origin').get().then((snapshot) => {
    snapshot.forEach((originDoc) => {
      const origin = originDoc.id;
      const originLink = document.createElement('a');
      originLink.setAttribute('href', '/?origin=' + origin);
      originLink.innerHTML = origin;
      linkGroup.appendChild(originLink);
      linkGroup.appendChild(document.createElement('p'));
    });
  }).catch((e) => statusUpdate('origin list error', e));
}

function listUsers(db) {
  const link_group = document.querySelector('#listings .users');
  db.collection('users').get().then((snapshot) => {
    snapshot.forEach((user_doc) => {
      const userLink = document.createElement('a');
      userLink.innerHTML = user_doc.data().email
      link_group.appendChild(userLink);
      link_group.appendChild(document.createElement('p'));
    });
  }).catch((e) => statusUpdate('user list error', e));
}

function dashboardSetup() {
  if (registry_id && device_id) {
    triggerDevice(db, registry_id, device_id);
  } else if (port_id || device_id || site_name || run_id || from || to) {
    document.getElementById('filters').classList.add('active');
    ensureGridRow('header');
    ensureGridColumn('row', 'runid');
    ensureGridColumn('origin');
    ensureGridColumn('site');
    ensureGridColumn('port');
    document.getElementById('fromFilter').value = from;
    document.getElementById('toFilter').value = to;
    document.getElementById('deviceFilter').value = device_id;
    document.getElementById('siteFilter').value = site_name;
    document.getElementById('originFilter').value = origin_id;
    document.getElementById('portFilter').value = port_id;
    document.getElementById('runidFilter').value = run_id;
    triggerFilter(db);
  } else if (origin_id) {
    ensureGridRow('header');
    ensureGridColumn('row', 'port');
    ensureGridColumn('active');
    triggerOrigin(db, origin_id);
  } else {
    document.getElementById('listings').classList.add('active');
    listSites(db);
    listOrigins(db);
    listUsers(db);
  }

  return origin_id;
}

function applyFilter() {
  const filters = {
    from: document.getElementById('fromFilter').value,
    to: document.getElementById('toFilter').value,
    site: document.getElementById('siteFilter').value,
    origin: document.getElementById('originFilter').value,
    port: document.getElementById('portFilter').value,
    device: document.getElementById('deviceFilter').value,
    runid: document.getElementById('runidFilter').value
  };
  const str = Object.keys(filters).map((filter) => {
    return filter + "=" + filters[filter];
  }).join('&');
  document.location = "?" + str;
}

function showActivePorts(message) {
  activePorts = new Set(message.ports);
  const ports = document.querySelectorAll(`#testgrid table td[label="row"]`);
  heartbeatTimestamp = message.timestamp;
  ports.forEach((port) => {
    const numPort = Number(port.innerText.replace('port', ''));
    if (!numPort) {
      return;
    }
    setGridValue("port" + numPort, "active", undefined, activePorts.has(numPort) + "");
    if (activePorts.has(numPort) && (!row_timestamps["port" + numPort]
      || Math.floor((Date.now() - row_timestamps["port" + numPort]) / 1000.0) >= ROW_TIMEOUT_SEC)) {
      row_timestamps["port" + numPort] = new Date();
      const cols = document.querySelectorAll(`#testgrid table tr[label="port${numPort}"] td`);
      cols.forEach((entry) => {
        if (entry.innerText == port.innerText || entry.getAttribute("label") == "active") {
          return;
        }
        entry.classList.add('old');
        entry.classList.remove('current', 'gone');
      });
    }
  });
}

function showMetadata(originId, showActive) {
  db.collection('origin').doc(originId).collection('runner').doc('heartbeat').onSnapshot((result) => {
    const message = result.data().message;
    if (message.timestamp && message.timestamp < heartbeatTimestamp) {
      return;
    }
    message.states && ensureColumns(message.states);
    const description = document.querySelector('#description .description');
    description.innerHTML = message.description;
    description.href = `config.html?origin=${origin_id}`;
    document.querySelector('#daq-version').innerHTML = message.version;
    document.querySelector('#lsb-version').innerHTML = message.lsb;
    document.querySelector('#sys-version').innerHTML = message.uname;
    document.querySelector('#daq-versions').classList.add('valid');
    if (showActive) {
      showActivePorts(message);
    }
  });
}

function triggerOrigin(db, originId) {
  const latest = (ref) => {
    return ref.orderBy('updated', 'desc').limit(1);
  };

  const originRef = db.collection('origin').doc(originId);
  showMetadata(originId, true);

  watcherAdd(originRef, "port", undefined, (ref, port_id) => {
    watcherAdd(ref, "runid", latest, (ref, runid_id) => {
      ref = originRef.collection("runid").doc(runid_id);
      watcherAdd(ref, "test", undefined, (ref, test_id) => {
        ref.onSnapshot((result) => {
          // TODO: Handle results going away.
          handleOriginResult(originId, port_id, runid_id, test_id, result.data());
        });
      });
    });
  });
}

function triggerFilter(db) {
  const filters = {
    siteName: site_name,
    port: Number(port_id),
    deviceId: device_id,
    from,
    to
  };
  const filtered = (ref) => {
    ref = ref.orderBy('updated', "desc");
    for (let filter in filters) {
      let value = filters[filter];
      if (value) {
        let op = "==";
        if (filter == "to" || filter == "from") {
          op = filter == "to" ? "<=" : ">=";
          value = value.replace('"', '');
          value += (filter == "to" ? "\uf8FF" : "");
          filter = "updated";
        }
        ref = ref.where(filter, op, value);
      }
    }
    // Gonna wait to do pagination.
    return ref.limit(100);
  };

  const processOrigin = (originId) => {
    const ref = db.collection('origin').doc(originId);
    if (run_id) {
      const runIds = run_id.split(',');
      runIds.map((runId) => {
        const runDoc = db.collection('origin').doc(originId).collection('runid').doc(runId);
        runDoc.get().then((doc) => {
          const data = doc.data();
          const site = data && data.siteName;
          const port = data && data.port;
          const deviceId = data && data.deviceId;
          const updated = data && new Date(data.updated);
          if ((filters.siteName && filters.siteName != site)
            || (filters.port && filters.port != port)
            || (filters.deviceId && filters.deviceId != deviceId)
            || (filters.from && new Date(filters.from) > updated)
            || (filters.to && (Number(new Date(filters.to)) + 60 * 24 * 60 * 1000) < updated)) {
            return;
          }
          watcherAdd(runDoc, "test", undefined, (ref, test_id) => {
            ref.onSnapshot((result) => {
              // TODO: Handle results going away.
              handleFilterResult(originId, site, runId, test_id, result.data());
            });
          });
        });
      });
    } else {
      watcherAdd(ref, "runid", filtered, (ref, runid_id) => {
        ref.get().then((runDoc) => {
          const site = runDoc.data() && runDoc.data().siteName;
          watcherAdd(ref, "test", undefined, (ref, test_id) => {
            ref.onSnapshot((result) => {
              // TODO: Handle results going away.
              handleFilterResult(originId, site, runid_id, test_id, result.data());
            });
          });
        });
      });
    }
  };
  if (origin_id) {
    showMetadata(origin_id);
    processOrigin(origin_id);
  } else {
    db.collection('origin').get().then((collection) => {
      const origins = collection.docs;
      origins.map((origin, i) => {
        if (i == 0) {
          showMetadata(origin.id);
        }
        processOrigin(origin.id);
      })
    });
  }
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
      document.body.style.backgroundColor = hsl;
    });
}

function interval_updater() {
  if (last_result_time_sec) {
    const timeDeltaSec = Math.floor(Date.now() / 1000.0 - last_result_time_sec);
    document.getElementById('update').innerHTML = `Last update ${timeDeltaSec} sec ago.`
  }
  for (const row in row_timestamps) {
    const lastUpdate = new Date(row_timestamps[row]);
    const timeDeltaSec = Math.floor((Date.now() - lastUpdate) / 1000.0);
    const selector = `#testgrid table tr[label="${row}"`;
    const runid = document.querySelector(selector).getAttribute('runid');

    if (row_timestamps[row] === false || timeDeltaSec >= ROW_TIMEOUT_SEC) {
      setGridValue(row, 'timer', runid, row_timestamps[row] ? 'Timed Out' : 'Done');
      setRowClass(row, true);
    } else {
      setGridValue(row, 'timer', runid, `${timeDeltaSec}s`);
      setRowClass(row, false);
    }
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
    mode: onChange ? 'code' : 'view',
    onChange: onChange
  };
  const editor = new JSONEditor(container, options);
  applySchema(editor, schema_url);
  return editor;
}

function setDatedStatus(attribute, value) {
  data_state[attribute] = value;
  const element = document.getElementById('config_body');
  element.classList.toggle('dirty', !!(data_state.dirty > data_state.saved || (data_state.dirty && !data_state.saved)));
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
  }).then(() => {
    setDatedStatus('pushed', timestamp);
  });
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
    if (firstUpdate && editor.expandAll) {
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

  document.getElementById('dashboard_link').href = `index.html?origin=${origin_id}`

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

  // Prefill module configs from the latest config
  Promise.all([latest_doc.get(), config_doc.get()]).then((docs) => {
    latest_doc_resolved = docs[0].data();
    config_doc_resolved = docs[1].data();
    if (!config_doc_resolved) {
      config_doc_resolved = {};
    }
    if ((!config_doc_resolved.config || JSON.stringify(config_doc_resolved.config) == "{}") && latest_doc_resolved.config.config) {
      config_doc_resolved.config = { modules: latest_doc_resolved.config.config.modules }
      return config_doc.set(config_doc_resolved);
    }
  }).then(() => {
    loadEditor(latest_doc, 'latest_editor', 'latest', null);
    const config_editor = loadEditor(config_doc, 'config_editor', 'config', setDirtyState, schema_url);
    document.querySelector('#config_body .save_button').onclick = () => pushConfigChange(config_editor, config_doc)
  });
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
  }).then(function () {
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
