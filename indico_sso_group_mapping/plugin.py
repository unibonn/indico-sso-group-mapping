# SPDX-License-Identifier: MIT

from operator import attrgetter

from wtforms.fields import BooleanField, SelectField
from wtforms_sqlalchemy.fields import QuerySelectField

from indico.core import signals
from indico.core.auth import multipass
from indico.core.plugins import IndicoPlugin
from indico.core.settings.converters import ModelConverter
from indico.modules.groups.models.groups import LocalGroup
from indico.web.forms.base import IndicoForm
from indico.web.forms.widgets import SwitchWidget

from indico_sso_group_mapping import _


class SettingsForm(IndicoForm):
    identity_provider = SelectField(_('Provider'))
    sso_group = QuerySelectField(_('Local Users Group'), allow_blank=True,
                                 query_factory=lambda: LocalGroup.query, get_label='name',
                                 description=_('The group to which anyone logging in '
                                               'with a matching SSO account is added.'))
    enable_group_cleanup = BooleanField(_('Enable periodic Local Users Group cleanup'), widget=SwitchWidget(),
                                        description=_('Enable periodic cleanup of Local Users Group '
                                                      'for SSO accounts without login in the past year.'))


class SSOGroupMappingPlugin(IndicoPlugin):
    """SSO Group Mapping

    Provides SSO group mapping to local group for Indico
    """

    configurable = True
    settings_form = SettingsForm
    default_settings = {
        'sso_group': None,
        'enable_group_cleanup': False,
    }
    settings_converters = {
        'sso_group': ModelConverter(LocalGroup),
    }

    def init(self):
        # identity_providers = [p for p in multipass.identity_providers.values()]
        identity_providers = multipass.identity_providers.values()
        if not identity_providers:
            del self.settings_form.identity_provider
        idp_choices = [(p.name, p.title) for p in sorted(identity_providers, key=attrgetter('title'))]
        self.settings_form.identity_provider.choices = idp_choices

        super().init()
        self.connect(signals.users.logged_in, self._user_logged_in)

    def _user_logged_in(self, user, identity, admin_impersonation, **kwargs):
        if admin_impersonation:
            return
        group = self.settings.get('sso_group')
        if not group:
            self.logger.warning('Local Users Group not set, plugin ineffective')
            return
        if identity.provider == 'uni-bonn-sso' and identity.identifier.endswith('@uni-bonn.de'):
            self.logger.info(f"Adding user with identity {identity.identifier} to local group {group}")
            group.members.add(user)
