import pytest

from indico.core.plugins import plugin_engine

from indico_sso_group_mapping.plugin import SSOGroupMappingPlugin

#from indico.modules.auth.models.identities import Identity
from indico.modules.auth.util import save_identity_info

from flask_multipass import IdentityInfo

from indico.web.flask.app import make_app

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
        'IDENTITIY_PROVIDERS': {
          'uni-bonn-sso': {
	    'type':             'shibboleth',
	    'title':            'Uni-ID',
            'identifier_field': 'eppn',
          },
        }
        #FIXME: Add identity provider config!!!
    }
    return make_app(testing=True, config_override=config_override)

def test_sso_group_mapping_plugin(app):
    my_plugin = SSOGroupMappingPlugin(plugin_engine, app)
    assert my_plugin.configurable is True

def test_create_sso_user(create_user):
    #FIXME: Need to import multipass from Indico!
    #identity_providers = multipass.identity_providers.values()
    # From this, get the active provider and pass it into IdentityInfo!

    identity = Identity(provider='uni-bonn-sso', identifier='foobar@uni-bonn.de')

    user = create_user(1, email='foobar@uni-bonn.de', identity=identity)
    #identity_info = IdentityInfo('uni-bonn-sso', identifier='foobar@uni-bonn.de')
    #save_identity_info(identity_info, user)
