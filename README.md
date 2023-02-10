# indico-sso-group-mapping
An [Indico](https://getindico.io/) plugin to map SSO groups to local Indico groups.

## Functionality
This plugin adds users logging in via a given identity provider, configurably filtered by the domain of the identity, to a configurable local group. The goal is to grant privileges (such as room booking) to all users using a given identity provider and, optionally, identity domain. An example use case would be Shibboleth SSO via federated identities, only granting those users with a given identity domain local privileges.

Furthermore, this plugin features a celery cron job which can optionally clean out users from the local group after they have not used the configured identity provider and identity domain for a configured number of days. This covers changes in a user's affiliation.

## Settings
After installation, the plugin (named `SSO Group Mapping`) offers various settings in the Admin backend.

### Provider
The identity provider to which accounts need to be associated to be added to the group.

### Identities Domain
If non-empty, identities must match given domain.

### Local Users Group
The group to which anyone logging in with a matching SSO account is added.

### Enable daily Local Users Group cleanup
Enable periodic cleanup of Local Users Group for SSO accounts without login in configured days.

### Expire login after days
Days after which logins are considered too old and users are removed from group in cleanup.

(only shown if daily cleanup is enabled)