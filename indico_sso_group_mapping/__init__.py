# This file is part of the Indico plugin indico-sso-group-mapping.
# Copyright (C) 2002 - 2023 University of Bonn
#
# The Indico plugin indico-sso-group-mapping is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core import signals
from indico.util.i18n import make_bound_gettext


_ = make_bound_gettext('SSOGroupMapping')


@signals.core.import_tasks.connect
def _import_tasks(sender, **kwargs):
    import indico_sso_group_mapping.task  # noqa: F401
