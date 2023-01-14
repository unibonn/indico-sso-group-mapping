

import os

import pytest

from indico.core import signals
from indico.core.auth import multipass
from indico.core.plugins import plugin_engine
# from indico.modules.auth.models.identities import Identity
from indico.modules.auth import Identity
from indico.modules.groups.models.groups import LocalGroup
from indico.util.date_time import now_utc
# from indico.modules.auth.util import save_identity_info
# from flask_multipass import IdentityInfo
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
            'uni-bonn-sso': {
                'type':             'shibboleth',
                'title':            'Uni-ID',
                'attrs_prefix':     '',
                'callback_uri':     '/shibboleth',
            },
        },
        'IDENTITY_PROVIDERS': {
            'uni-bonn-sso': {
                'type':             'shibboleth',
                'title':            'Uni-ID',
                'identifier_field': 'eppn',
            },
        },
        'PROVIDER_MAP': {
            'uni-bonn-sso': {'identity_provider': 'uni-bonn-sso'},
        }
        #FIXME: Add identity provider config!!!
    }
    return make_app(testing=True, config_override=config_override)


@pytest.fixture
def create_group(db):
    """Return a callable which lets you create dummy groups."""
    def _create_group(id_, group_name):
        group = LocalGroup()
        group.id = id_
        group.name = group_name
        db.session.add(group)
        db.session.flush()
        return group.proxy

    return _create_group


def test_create_sso_group_mapping_plugin(app):
    my_plugin = SSOGroupMappingPlugin(plugin_engine, app)
    assert my_plugin.configurable is True


def test_login_sso_user(app, create_group, create_user, db):
    #FIXME: Need to import multipass from Indico!
    # identity_providers = multipass.identity_providers.values()
    #  From this, get the active provider and pass it into IdentityInfo!

    group = create_group(1, 'uni-bonn-users')

    my_plugin = SSOGroupMappingPlugin(plugin_engine, app)
    my_plugin.settings.set('sso_group', group.group)

    user = create_user(1, email='foobar@uni-bonn.de')
    identity = Identity(user_id=1, provider='uni-bonn-sso', identifier='foobar@uni-bonn.de')

    assert user not in group.get_members()

    signals.users.logged_in.send(user, identity=identity, admin_impersonation=False)

    assert user in group.get_members()

    # identity_info = IdentityInfo('uni-bonn-sso', identifier='foobar@uni-bonn.de')
    # save_identity_info(identity_info, user)


def test_local_sso_user(app, create_group, create_user, db):
    local_provider = multipass.default_local_auth_provider

    group = create_group(1, 'uni-bonn-users')

    my_plugin = SSOGroupMappingPlugin(plugin_engine, app)
    my_plugin.settings.set('sso_group', group.group)

    user = create_user(1, email='foobar@cern.ch')
    identity = Identity(user_id=1, provider=local_provider, identifier='foobar@cern.ch')

    assert user not in group.get_members()

    signals.users.logged_in.send(user, identity=identity, admin_impersonation=False)

    assert user not in group.get_members()


def test_group_cleanup(app, create_group, create_user, db):
    group = create_group(1, 'uni-bonn-users')

    my_plugin = SSOGroupMappingPlugin(plugin_engine, app)
    my_plugin.settings.set('sso_group', group.group)
    my_plugin.settings.set('enable_group_cleanup', True)

    user = create_user(1, email='foobar@uni-bonn.de')
    identity = Identity(user_id=1, provider='uni-bonn-sso', identifier='foobar@uni-bonn.de')

    assert identity in user.identities

    signals.users.logged_in.send(user, identity=identity, admin_impersonation=False)

    last_login_dt = identity.safe_last_login_dt
    login_ago = now_utc() - last_login_dt
    assert login_ago.days > 365

    scheduled_groupmembers_check()

    assert user not in group.get_members()
