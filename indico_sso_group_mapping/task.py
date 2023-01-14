# SPDX-License-Identifier: MIT

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
    group = SSOGroupMappingPlugin.settings.get('sso_group')
    if not group:
        SSOGroupMappingPlugin.logger.warning('Local Users Group not set, not cleaning up group')
        return
    for user in group.members.copy():
        for identity in user.identities:
            if identity.provider == 'uni-bonn-sso' and identity.identifier.endswith('@uni-bonn.de'):
                last_login_dt = identity.safe_last_login_dt
                login_ago = now_utc() - last_login_dt
                SSOGroupMappingPlugin.logger.warning(f"User with identifier {identity.identifier} "
                                                     "has last logged in {login_ago.days} days ago")
                if login_ago.days > 365:
                    SSOGroupMappingPlugin.logger.info(f"Removing user with identity {identity.identifier} "
                                                      "from local group {group}")
                    group.members.remove(user)
                    db.session.flush()
