# Copyright (c) 2024 CRS4
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from rocrate_validator.models import Severity
from tests.ro_crates import InvalidProvRC
from tests.shared import do_entity_test

# set up logging
logger = logging.getLogger(__name__)


def test_provrc_workflow_no_haspart():
    """\
    Test a Provenance Run Crate where a ComputationalWorkflow does not have
    the hasPart property.
    """
    do_entity_test(
        InvalidProvRC().workflow_no_haspart,
        Severity.REQUIRED,
        False,
        ["Provenance Run Crate ComputationalWorkflow MUST"],
        ["ComputationalWorkflow MUST refer to orchestrated tools via hasPart"],
        profile_identifier="provenance-run-crate"
    )


def test_provrc_workflow_bad_haspart():
    """\
    Test a Provenance Run Crate where a ComputationalWorkflow does not point
    to the orchestrated tools via hasPart.
    """
    do_entity_test(
        InvalidProvRC().workflow_bad_haspart,
        Severity.REQUIRED,
        False,
        ["Provenance Run Crate ComputationalWorkflow MUST"],
        ["ComputationalWorkflow MUST refer to orchestrated tools via hasPart"],
        profile_identifier="provenance-run-crate"
    )
