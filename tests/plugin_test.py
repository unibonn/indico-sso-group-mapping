import pytest

from indico.core.plugins import plugin_engine

from indico_sso_group_mapping.plugin import SSOGroupMappingPlugin

def test_sso_group_mapping_plugin(app):
    my_plugin = SSOGroupMappingPlugin(plugin_engine, app)
    assert my_plugin.configurable == True
