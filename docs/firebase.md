# Firebase setup instructions for DAQ.

DAQ uses a simple Firebase-hosted web page to provide a dynamic dashboard
of test results.

1. Goto the [Firebase Console](https://console.firebase.google.com/) and add a new project.
2. Navigate to the Google Cloud Platform (GCP) service accounts page:
   * From the service menu (gear icon), select the _Users and permissions_ option.
   * Select the _SERVICE ACCOUNTS_ tab.
   * Follow _Manage all service accounts_ link.
3. From the IAM & admin page, create a new service account.
   * Use a semi-meaningful name descriptive of the install, like 'daq-testing-lab'.
   * Add the _Pub/Sub Publisher_ role.
   * Furnish a new private key.
4. Install the downloaded key into your install.
   * Copy the download JSON key file to the `daq/local/` directory.
   * Edit `daq/local/system.conf` to specify the `gcp_cred` setting to point to the downloaded file
     (with a path relative to the `daq/` install directory).
5. (Re)Start the DAQ install.
   * There should be something in the top 10-20 startup log lines that look something like:
     <br>`INFO:gcp:Loading gcp credentials from local/bos-daq-testing-de56aa4b1e47.json`
     <br>`INFO:gcp:Initialized gcp publisher client bos-daq-testing:daq-laptop`
6. Follow the [Firebase CLI setup instructions](https://firebase.google.com/docs/cli/).
7. Goto the 'daq/firebase/` directory.
   * Run `firebase use` to set the GCP project to use (as created above).
   * Run`firebase deploy` to deploy the Cloud Functions and static hosting pages.
   * Follow the link to the _Hosting URL_ to see the newly installed pages.




