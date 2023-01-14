# SPDX-License-Identifier: MIT

from indico.core import signals
from indico.util.i18n import make_bound_gettext


_ = make_bound_gettext('SSOGroupMapping')

@signals.core.import_tasks.connect
def _import_tasks(sender, **kwargs):
    import indico_sso_group_mapping.plugin.task
