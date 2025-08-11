# This file is part of the Indico plugin indico-sso-group-mapping.
# Copyright (C) 2022 - 2025 University of Bonn
#
# The Indico plugin indico-sso-group-mapping is free software; you can
# redistribute it and/or modify it under the terms of the MIT License;
# see the LICENSE file for more details.

import os
from datetime import timedelta

import pytest

from indico.core import signals
from indico.core.plugins import plugin_engine
from indico.util.date_time import now_utc
from indico.web.flask.app import make_app

from indico_sso_group_mapping.plugin import SSOGroupMappingPlugin
from indico_sso_group_mapping.task import scheduled_groupmembers_check


# Override app fixture imported from Indico pytest plugin:
@pytest.fixture(scope='session')
def app(request, redis_proc):
    """Create the flask app."""
    config_override = {
        'BASE_URL': 'http://localhost',
        'SMTP_SERVER': ('localhost', 0),  # invalid port - just in case so we NEVER send emails!
        'TEMP_DIR': request.config.indico_temp_dir.strpath,
        'CACHE_DIR': request.config.indico_temp_dir.strpath,
        'REDIS_CACHE_URL': f'redis://{redis_proc.host}:{redis_proc.port}/0',
        'STORAGE_BACKENDS': {'default': 'mem:'},
        'PLUGINS': request.config.indico_plugins,
        'ENABLE_ROOMBOOKING': True,
        'SECRET_KEY': os.urandom(16),
        'SMTP_USE_CELERY': False,
        'AUTH_PROVIDERS': {
            'acme-sso': {
                'type':             'shibboleth',
                'title':            'ACME-ID',
                'attrs_prefix':     '',
                'callback_uri':     '/shibboleth',
            },
        },
        'IDENTITY_PROVIDERS': {
            'acme-sso': {
                'type':             'shibboleth',
                'title':            'ACME-ID',
                'identifier_field': 'eppn',
            },
        },
        'PROVIDER_MAP': {
            'acme-sso': {'identity_provider': 'acme-sso'},
        }
    }
    return make_app(testing=True, config_override=config_override)


def test_create_sso_group_mapping_plugin(app):
    ssog_plugin = SSOGroupMappingPlugin(plugin_engine, app)
    assert ssog_plugin.configurable is True


def test_login_sso_user(app, create_group, create_identity, create_user, db):
    group = create_group(1, 'acme-users')

    ssog_plugin = SSOGroupMappingPlugin(plugin_engine, app)
    ssog_plugin.settings.set('identity_provider', 'acme-sso')
    ssog_plugin.settings.set('identities_domain', 'acme.ch')
    ssog_plugin.settings.set('sso_group', group.group)

    user = create_user(1, email='foobar@acme.ch')
    identity = create_identity(user, provider='acme-sso', identifier='foobar@acme.ch')
    assert identity in user.identities

    assert user not in group.get_members()

    signals.users.logged_in.send(user, identity=identity, admin_impersonation=False)

    assert user in group.get_members()


def test_login_sso_user_with_foreign_domain(app, create_group, create_identity, create_user, db):
    group = create_group(1, 'acme-users')

    ssog_plugin = SSOGroupMappingPlugin(plugin_engine, app)
    ssog_plugin.settings.set('identity_provider', 'acme-sso')
    ssog_plugin.settings.set('identities_domain', 'acme.ch')
    ssog_plugin.settings.set('sso_group', group.group)

    user = create_user(1, email='foobar@acme.ch')
    identity = create_identity(user, provider='acme-sso', identifier='foobar@acme-foreign.ch')

    assert user not in group.get_members()

    signals.users.logged_in.send(user, identity=identity, admin_impersonation=False)

    assert user not in group.get_members()


def test_login_sso_user_unchecked_domain(app, create_group, create_identity, create_user, db):
    group = create_group(1, 'acme-users')

    ssog_plugin = SSOGroupMappingPlugin(plugin_engine, app)
    ssog_plugin.settings.set('identity_provider', 'acme-sso')
    ssog_plugin.settings.set('identities_domain', '')
    ssog_plugin.settings.set('sso_group', group.group)

    user = create_user(1, email='foobar@acme.ch')
    identity = create_identity(user, provider='acme-sso', identifier='foobar@acme-foreign.ch')

    assert user not in group.get_members()

    signals.users.logged_in.send(user, identity=identity, admin_impersonation=False)

    assert user in group.get_members()


def test_local_user(app, create_group, create_identity, create_user, db):
    group = create_group(1, 'acme-users')

    ssog_plugin = SSOGroupMappingPlugin(plugin_engine, app)
    ssog_plugin.settings.set('identity_provider', 'acme-sso')
    ssog_plugin.settings.set('identities_domain', 'acme.ch')
    ssog_plugin.settings.set('sso_group', group.group)

    user = create_user(1, email='foobar@cern.ch')
    identity = create_identity(user, provider='indico', identifier='foobar@cern.ch')

    assert user not in group.get_members()

    signals.users.logged_in.send(user, identity=identity, admin_impersonation=False)

    assert user not in group.get_members()


def test_group_cleanup_neverloggedinuser(app, create_group, create_identity, create_user, db):
    group = create_group(1, 'acme-users')

    ssog_plugin = SSOGroupMappingPlugin(plugin_engine, app)
    ssog_plugin.settings.set('identity_provider', 'acme-sso')
    ssog_plugin.settings.set('identities_domain', 'acme.ch')
    ssog_plugin.settings.set('sso_group', group.group)
    ssog_plugin.settings.set('enable_group_cleanup', True)
    ssog_plugin.settings.set('expire_login_days', 200)

    user = create_user(1, email='foobar@acme.ch')
    identity = create_identity(user, provider='acme-sso', identifier='foobar@acme.ch')

    signals.users.logged_in.send(user, identity=identity, admin_impersonation=False)

    last_login_dt = identity.safe_last_login_dt
    login_ago = now_utc() - last_login_dt
    assert login_ago.days > 200

    scheduled_groupmembers_check()

    assert user not in group.get_members()


def test_group_cleanup_expireduser(app, create_group, create_identity, create_user, db):
    group = create_group(1, 'acme-users')

    ssog_plugin = SSOGroupMappingPlugin(plugin_engine, app)
    ssog_plugin.settings.set('identity_provider', 'acme-sso')
    ssog_plugin.settings.set('identities_domain', 'acme.ch')
    ssog_plugin.settings.set('sso_group', group.group)
    ssog_plugin.settings.set('enable_group_cleanup', True)
    ssog_plugin.settings.set('expire_login_days', 200)

    user = create_user(1, email='foobar@acme.ch')
    identity = create_identity(user, provider='acme-sso', identifier='foobar@acme.ch')

    assert identity in user.identities

    identity.register_login('127.0.0.1')
    identity.last_login_dt = now_utc() - timedelta(days=300)
    signals.users.logged_in.send(user, identity=identity, admin_impersonation=False)

    last_login_dt = identity.safe_last_login_dt
    login_ago = now_utc() - last_login_dt
    assert login_ago.days > 200

    scheduled_groupmembers_check()

    assert user not in group.get_members()


def test_group_cleanup_unexpireduser(app, create_group, create_identity, create_user, db):
    group = create_group(1, 'acme-users')

    ssog_plugin = SSOGroupMappingPlugin(plugin_engine, app)
    ssog_plugin.settings.set('identity_provider', 'acme-sso')
    ssog_plugin.settings.set('identities_domain', 'acme.ch')
    ssog_plugin.settings.set('sso_group', group.group)
    ssog_plugin.settings.set('enable_group_cleanup', True)
    ssog_plugin.settings.set('expire_login_days', 200)

    user = create_user(1, email='foobar@acme.ch')
    identity = create_identity(user, provider='acme-sso', identifier='foobar@acme.ch')

    identity.register_login('127.0.0.1')
    identity.last_login_dt = now_utc() - timedelta(days=100)
    signals.users.logged_in.send(user, identity=identity, admin_impersonation=False)

    last_login_dt = identity.safe_last_login_dt
    login_ago = now_utc() - last_login_dt
    assert login_ago.days < 200

    scheduled_groupmembers_check()

    assert user in group.get_members()


def test_group_cleanup_freshuser(app, create_group, create_identity, create_user, db):
    group = create_group(1, 'acme-users')

    ssog_plugin = SSOGroupMappingPlugin(plugin_engine, app)
    ssog_plugin.settings.set('identity_provider', 'acme-sso')
    ssog_plugin.settings.set('identities_domain', 'acme.ch')
    ssog_plugin.settings.set('sso_group', group.group)
    ssog_plugin.settings.set('enable_group_cleanup', True)
    ssog_plugin.settings.set('expire_login_days', 200)

    user = create_user(1, email='foobar@acme.ch')
    identity = create_identity(user, provider='acme-sso', identifier='foobar@acme.ch')

    identity.register_login('127.0.0.1')
    signals.users.logged_in.send(user, identity=identity, admin_impersonation=False)

    last_login_dt = identity.safe_last_login_dt
    login_ago = now_utc() - last_login_dt
    assert login_ago.days < 1

    scheduled_groupmembers_check()

    assert user in group.get_members()
