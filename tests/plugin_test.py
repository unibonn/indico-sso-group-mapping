import pytest

from indico_sso_group_mapping.plugin import SSOGroupMappingPlugin

def test_sso_group_mapping_plugin(app):
    my_plugin = SSOGroupMappingPlugin(app)
    assert my_plugin.configurable == True
