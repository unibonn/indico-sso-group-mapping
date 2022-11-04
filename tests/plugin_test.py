import pytest

from indico_sso_group_mapping import plugin

def test_sso_group_mapping_plugin():
    my_plugin = plugin.SSOGroupMappingPlugin()
    assert my_plugin.configurable == True
