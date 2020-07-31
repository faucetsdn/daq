# Service Account for DAQ and Registrar

Many functions of DAQ require a standard GCP service account, rather than personal credentials.
Once created, there's a limited set of permissions that can be granted to enable various bits
and pieces of functionality.

Each individual install of DAQ should have it's own service account. The account name is
assumed to be unique, and having multiple installs with the same account will cause confusion
and unpredictable results.

1. Acquire a service account key. If one has been provided, skip to the next step.
   * Navigate to [Google Cloud Platform (GCP) service accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
   * Create a new service account with a semi-meaningful name, like `daq-testlab`, that uniquely
   describes this install.
   * Add the _Pub/Sub Admin_, _Storage Admin_, _Cloud Datastore User_, _Logs Writer_,
   and _Firebase Admin_ roles.
   * Create a new private key in JSON format.

2. Install the downloaded key into the DAQ install.
   * Copy the download JSON key file to the `local/` directory.
   * Edit `local/system.conf` to specify the `gcp_cred` setting to point to the downloaded file
     (with a path relative to the `daq` install directory), e.g.
     `gcp_cred=local/daq-testlab-de56aa4b1e47.json`.

4. When running DAQ, it should show appropriate log messages. This is not necessary for the `registrar` or `validator` tools.
There should be something in the top 10-20 startup log lines that look something like:
     <br>`INFO:gcp:Loading gcp credentials from local/daq-testlab-de56aa4b1e47.json`
     <br>`INFO:gcp:Initialized gcp publisher client daq-project:daq-testlab`
