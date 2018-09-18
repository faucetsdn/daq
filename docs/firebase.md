# Firebase setup instructions for DAQ.

DAQ uses a simple Firebase-hosted web page to provide a dynamic dashboard
of test results.

0. There should be a GCP project that can be used to host everything.
1. Goto the [Firebase Console](https://console.firebase.google.com/) and add a new project.
   * Add the hosting GCP project to link it to this Firebase setup.
2. Navigate to the
[Google Cloud Platform (GCP) service accounts page]
(https://console.cloud.google.com/iam-admin/serviceaccounts?project=atmosphere-gcp-dev)
   * This is <em>not</em> from the Firebase page: it has to be from the base GCP page.
   * Create a new service account.
   * Use a semi-meaningful name descriptive of the install, like 'daq-testing-lab'.
   * Add the _Pub/Sub Publisher_ and _Storage Admin_ roles.
   * Furnish a new private key.
4. Install the downloaded key into the DAQ install.
   * Copy the download JSON key file to the `daq/local/` directory.
   * Edit `daq/local/system.conf` to specify the `gcp_cred` setting to point to the downloaded file
     (with a path relative to the `daq/` install directory), e.g.
     `gcp_cred=local/bos-daq-testing-de56aa4b1e47.json`.
5. (Re)Start the DAQ install.
   * There should be something in the top 10-20 startup log lines that look something like:
     <br>`INFO:gcp:Loading gcp credentials from local/bos-daq-testing-de56aa4b1e47.json`
     <br>`INFO:gcp:Initialized gcp publisher client bos-daq-testing:daq-laptop`
6. Follow the [Firebase CLI setup instructions](https://firebase.google.com/docs/cli/).
7. Goto the 'daq/firebase/` directory.
   * Run `firebase use` to set the GCP project to use (as created above).
   * Run `firebase deploy` to deploy the Cloud Functions and static hosting pages.
   * Follow the link to the indicated _Hosting URL_ to see the newly installed pages.
