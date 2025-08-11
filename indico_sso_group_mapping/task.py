# This file is part of the Indico plugin indico-sso-group-mapping.
# Copyright (C) 2022 - 2025 University of Bonn
#
# The Indico plugin indico-sso-group-mapping is free software; you can
# redistribute it and/or modify it under the terms of the MIT License;
# see the LICENSE file for more details.

from celery.schedules import crontab

from indico.core.celery import celery
from indico.core.db import db
from indico.util.date_time import now_utc


@celery.periodic_task(run_every=crontab(minute='0', hour='2'), plugin='sso_group_mapping')
def scheduled_groupmembers_check():
    from indico_sso_group_mapping.plugin import SSOGroupMappingPlugin
    if not SSOGroupMappingPlugin.settings.get('enable_group_cleanup'):
        SSOGroupMappingPlugin.logger.warning('Local Group cleanup not enabled, skipping run')
        return
    identity_provider = SSOGroupMappingPlugin.settings.get('identity_provider')
    if not identity_provider:
        SSOGroupMappingPlugin.logger.warning('Identity provider not set, not cleaning up group')
        return
    group = SSOGroupMappingPlugin.settings.get('sso_group')
    if not group:
        SSOGroupMappingPlugin.logger.warning('Local Users Group not set, not cleaning up group')
        return
    any_users_discarded = False
    for user in group.members.copy():
        for identity in user.identities:
            if identity.provider == identity_provider:
                if (not SSOGroupMappingPlugin.settings.get('identities_domain')
                        or identity.identifier.endswith('@' + SSOGroupMappingPlugin.settings.get('identities_domain'))):
                    last_login_dt = identity.safe_last_login_dt
                    login_ago = now_utc() - last_login_dt
                    if login_ago.days > SSOGroupMappingPlugin.settings.get('expire_login_days'):
                        SSOGroupMappingPlugin.logger.info('Removing user with identity %s '
                                                          'from local group %s, last login was '
                                                          '%d days ago', identity.identifier, group, login_ago.days)
                        group.members.discard(user)
                        any_users_discarded = True
    if any_users_discarded:
        db.session.commit()
