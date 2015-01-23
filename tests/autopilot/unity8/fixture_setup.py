# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#
# Unity Autopilot Test Suite
# Copyright (C) 2015 Canonical
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import fixtures

from autopilot import introspection
from autopilot.matchers import Eventually
from autopilot.matchers import Equals

from unity8 import process_helpers, sensors
from unity8.shell import emulators


class LaunchUnityWithFakeSensors(fixtures.Fixture):

    """Fixture to launch Unity8 with an injectable sensors backend."""

    def setUp(self):
        """Restart Unity8 with testability and create sensors."""
        fixtures.EnvironmentVariable(
            'UBUNTU_PLATFORM_API_TEST_OVERRIDE',
            newvalue='sensors')
        super(LaunchUnityWithFakeSensors, self).setUp()
        self.fake_sensors = sensors.FakePlatformSensors()
        self.unity_proxy = process_helpers.restart_unity_with_testability()
        self.fifo_path = '/tmp/sensor-fifo-{0}'.format(
            process_helpers.get_unity_pid())
        Eventually(Equals(True)).match(
            lambda: os.path.exists(self.fifo_path))
        with open(self.fifo_path) as fifo:
            fifo.write('create accel 0 1000 0.1')
            fifo.write('create light 0 10 1')
            fifo.write('create proximity')


class LaunchDashApp(fixtures.Fixture):

    """Fixture to launch the Dash app."""

    def __init__(self, binary_path, variables):
        """Initialize an instance.

        :param str binary_path: The path to the Dash app binary.
        :param variables: The variables to use when launching the app.
        :type variables: A dictionary.

        """
        super(LaunchDashApp, self).__init__()
        self.binary_path = binary_path
        self.variables = variables

    def setUp(self):
        """Launch the dash app when the fixture is used."""
        super(LaunchDashApp, self).setUp()
        self.addCleanup(self.stop_application)
        self.application_proxy = self.launch_application()

    def launch_application(self):
        binary_arg = 'BINARY={}'.format(self.binary_path)
        testability_arg = 'QT_LOAD_TESTABILITY={}'.format(1)
        env_args = [
            '{}={}'.format(key, value) for key, value in self.variables.items()
        ]
        all_args = [binary_arg, testability_arg] + env_args

        pid = process_helpers.start_job('unity8-dash', *all_args)
        return introspection.get_proxy_object_for_existing_process(
            pid=pid,
            emulator_base=emulators.UnityEmulatorBase,
        )

    def stop_application(self):
        process_helpers.stop_job('unity8-dash')
