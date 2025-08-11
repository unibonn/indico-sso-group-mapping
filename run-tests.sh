#!/bin/bash
# This file is part of the Indico plugin indico-sso-group-mapping.
# Copyright (C) 2022 - 2025 University of Bonn
#
# The Indico plugin indico-sso-group-mapping is free software; you can
# redistribute it and/or modify it under the terms of the MIT License;
# see the LICENSE file for more details.

for dir in $(find -name pytest.ini -exec dirname {} \;); do
    pushd "$dir" >/dev/null
    pytest "$@"
    popd >/dev/null
done
