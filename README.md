# indico-sso-group-mapping
An [Indico](https://getindico.io/) plugin to map SSO groups to local Indico groups.

## Functionality
This plugin adds users logging in via a given identity provider, configurably filtered by the domain of the identity, to a configurable local group. The goal is to grant privileges (such as room booking) to all users using a given identity provider and, optionally, identity domain. An example use case would be Shibboleth SSO via federated identities, only grating those users with a given identity domain local privileges.

Furthermore, this plugin features a celery cron job which can optionally clean out users from the local group after they have not used the configured identity provider and identity domain for a configured number of days. This covers changes in a user's affiliation.
