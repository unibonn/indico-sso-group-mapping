# This file is part of the Indico plugin indico-sso-group-mapping.
# Copyright (C) 2022 - 2023 University of Bonn
#
# The Indico plugin indico-sso-group-mapping is free software; you can
# redistribute it and/or modify it under the terms of the MIT License;
# see the LICENSE file for more details.

from operator import attrgetter

from wtforms.fields import BooleanField, IntegerField, SelectField, StringField
from wtforms.validators import HiddenUnless, InputRequired, NumberRange
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
    identity_provider = SelectField(_('Provider'), [InputRequired()],
                                    description=_('The identity provider accounts need to be '
                                                  'associated with to be added to the group.'))
    identities_domain = StringField(_('Identities Domain'), allow_blank=True,
                                    description=_('If non-empty, identities must match given domain.'))
    sso_group = QuerySelectField(_('Local Users Group'), [InputRequired()],
                                 query_factory=lambda: LocalGroup.query, get_label='name',
                                 description=_('The group to which anyone logging in '
                                               'with a matching SSO account is added.'))
    enable_group_cleanup = BooleanField(_('Enable periodic Local Users Group cleanup'), widget=SwitchWidget(),
                                        description=_('Enable periodic cleanup of Local Users Group '
                                                      'for SSO accounts without login in configured days.'))
    expire_login_days = IntegerField(_('Expire login after days'),
                                     [HiddenUnless('enable_group_cleanup', preserve_data=True),
                                      InputRequired(), NumberRange(min=1)],
                                     description=_('Days after which logins are considered too old '
                                                   'and users are removed from group in cleanup.'))


class SSOGroupMappingPlugin(IndicoPlugin):
    """SSO Group Mapping

    Provides SSO group mapping to local group for Indico
    """

    configurable = True
    settings_form = SettingsForm
    default_settings = {
        'identity_provider': None,
        'identities_domain': '',
        'sso_group': None,
        'enable_group_cleanup': False,
        'expire_login_days': 365,
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
        identity_provider = self.settings.get('identity_provider')
        if not identity_provider:
            self.logger.warning('Identity provider not set, plugin ineffective')
        group = self.settings.get('sso_group')
        if not group:
            self.logger.warning('Local Users Group not set, plugin ineffective')
            return
        if identity.provider == identity_provider:
            if (not self.settings.get('identities_domain')
                    or identity.identifier.endswith('@' + self.settings.get('identities_domain'))):
                self.logger.info(f"Adding user with identity {identity.identifier} to local group {group}")
                group.members.add(user)
