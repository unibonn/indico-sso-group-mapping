# import pytest

from indico.core.plugins import plugin_engine

from indico_sso_group_mapping.plugin import SSOGroupMappingPlugin

#from indico.modules.auth.models.identities import Identity
from indico.modules.auth.util import save_identity_info

from flask_multipass import IdentityInfo

def test_sso_group_mapping_plugin(app):
    my_plugin = SSOGroupMappingPlugin(plugin_engine, app)
    assert my_plugin.configurable is True

def test_create_sso_user(create_user):
    user = create_user(1, email='foobar@uni-bonn.de')
    identity_info = IdentityInfo('uni-bonn-sso', 'foobar@uni-bonn.de')
    save_identity_info(identity_info, user)
