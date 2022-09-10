# SPDX-License-Identifier: MIT

from wtforms_sqlalchemy.fields import QuerySelectField

from indico.core import signals
from indico.core.plugins import IndicoPlugin
from indico.core.settings.converters import ModelConverter
from indico.modules.groups.models.groups import LocalGroup
from indico.web.forms.base import IndicoForm


class SettingsForm(IndicoForm):
    sso_group = QuerySelectField('Local Users Group', allow_blank=True,
                                 query_factory=lambda: LocalGroup.query, get_label='name',
                                 description='The group to which anyone logging in with a matching SSO account is added.')


class SSOGroupMappingPlugin(IndicoPlugin):
    """SSOGroupMapping

    Provides SSO group mapping to local group for Indico
    """

    configurable = True
    settings_form = SettingsForm
    default_settings = {
        'sso_group': None,
    }
    settings_converters = {
        'sso_group': ModelConverter(LocalGroup),
    }

    def init(self):
        super().init()
        self.connect(signals.users.logged_in, self._user_logged_in)

    def _user_logged_in(self, user, identity, admin_impersonation, **kwargs):
        if admin_impersonation:
            return
        group = self.settings.get('sso_group')
        if not group:
            return
        if identity.provider == 'shib-sso' and identity.identifier.endswith('@uni-bonn.de'):
            group.members.add(user)
