# This file is part of the Indico plugin indico-sso-group-mapping.
# Copyright (C) 2022 - 2023 University of Bonn
#
# The Indico plugin indico-sso-group-mapping is free software; you can
# redistribute it and/or modify it under the terms of the MIT License;
# see the LICENSE file for more details.

from celery.schedules import crontab

from indico.core.celery import celery
from indico.core.db import db
from indico.util.date_time import now_utc


@celery.periodic_task(run_every=crontab(minute='*/5'), plugin='sso_group_mapping')
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
    for user in group.members.copy():
        for identity in user.identities:
            if identity.provider == identity_provider:
                if (not SSOGroupMappingPlugin.settings.get('identities_domain')
                        or identity.identifier.endswith('@' + SSOGroupMappingPlugin.settings.get('identities_domain'))):
                    last_login_dt = identity.safe_last_login_dt
                    login_ago = now_utc() - last_login_dt
                    SSOGroupMappingPlugin.logger.warning(f"User with identifier {identity.identifier} "
                                                         "has last logged in {login_ago.days} days ago")
                    if login_ago.days > SSOGroupMappingPlugin.settings.get('expire_login_days'):
                        SSOGroupMappingPlugin.logger.info(f"Removing user with identity {identity.identifier} "
                                                          "from local group {group}")
                        group.members.remove(user)
                        db.session.flush()
