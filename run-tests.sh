#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2019 CERN.
# SPDX-FileCopyrightText: 2019-2021 Northwestern University.
# SPDX-FileCopyrightText: 2022 Graz University of Technology.
# SPDX-License-Identifier: MIT


pytest_args=()
for arg in $@; do
	# note: we don't use "getopts" here b/c of some limitations (e.g. long options),
	#       which means that we can't combine short options (e.g. "./run-tests -Kk pattern")
    pytest_args+=( ${arg} )
done


python -m sphinx.cmd.build -qnNW docs docs/_build/html
# Note: expansion of pytest_args looks like below to not cause an unbound
# variable error when 1) "nounset" and 2) the array is empty.
python -m pytest ${pytest_args[@]+"${pytest_args[@]}"}
