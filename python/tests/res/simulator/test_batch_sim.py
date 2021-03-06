import os
import time
import sys
import unittest
import datetime
from functools import partial

from ecl.util.test import TestAreaContext

from res.simulator import BatchSimulator, BatchContext
from res.enkf import ResConfig

from tests import ResTest

class TestMonitor(object):

    def __init__(self):
        self.sim_context = None

    def start_callback(self, *args, **kwargs): 
        self.sim_context = args[0]



class BatchSimulatorTest(ResTest):


    def test_invalid_simulator_creation(self):
        config_file = self.createTestPath("local/batch_sim/batch_sim.ert")

        with TestAreaContext("batch_sim") as test_area:
            test_area.copy_parent_content(config_file)

            # Not valid ResConfig instance as first argument
            with self.assertRaises(ValueError):
                rsim = BatchSimulator("ARG",
                                      {
                                          "WELL_ORDER": ["W1", "W2", "W3"],
                                          "WELL_ON_OFF": ["W1", "W2", "W3"]
                                      },
                                      ["ORDER", "ON_OFF"])

            res_config = ResConfig(user_config_file=os.path.basename(config_file))

            # Control argument not a dict - Exception
            with self.assertRaises(Exception):
                rsim = BatchSimulator(res_config, ["WELL_ORDER", ["W1", "W2", "W3"]], ["ORDER"])

            rsim = BatchSimulator(res_config,
                                  {"WELL_ORDER" : ["W1", "W2", "W3"],
                                   "WELL_ON_OFF" : ["W1", "W2", "W3"]},
                                  ["ORDER", "ON_OFF"])

            # The key for one of the controls is invalid => KeyError
            with self.assertRaises(KeyError):
                rsim.start("case",
                           [
                               (2,
                                {
                                    "WELL_ORDERX": {"W1": 0, "W2": 0, "W3": 1},
                                    "WELL_ON_OFF": {"W1": 0, "W2": 0, "W3": 1},
                                }),
                               (2,
                                {
                                    "WELL_ORDER": {"W1": 0, "W2": 0, "W3": 0},
                                    "WELL_ON_OFF": {"W1": 0, "W2": 0, "W3": 1},
                                }),
                           ])

            # The key for one of the variables is invalid => KeyError
            with self.assertRaises(KeyError):
                rsim.start("case",
                           [
                               (2,
                                {
                                    "WELL_ORDER": {"W1": 0, "W4": 0, "W3": 1},
                                    "WELL_ON_OFF": {"W1": 0, "W2": 0, "W3": 1},
                                }),
                               (1,
                                {
                                    "WELL_ORDER": {"W1": 0, "W2": 0, "W3": 0},
                                    "WELL_ON_OFF": {"W1": 0, "W2": 0, "W3": 1},
                                }),
                           ])

            # The key for one of the variables is invalid => KeyError
            with self.assertRaises(KeyError):
                rsim.start("case",
                           [
                               (2,
                                {
                                    "WELL_ORDER": {"W1": 0, "W2": 0, "W3": 1, "W0": 0},
                                    "WELL_ON_OFF": {"W1": 0, "W2": 0, "W3": 1},
                                }),
                               (1,
                                {
                                    "WELL_ORDER": {"W1": 0, "W2": 0, "W3": 0},
                                    "WELL_ON_OFF": {"W1": 0, "W2": 0, "W3": 1},
                                }),
                           ])


            # Missing the key WELL_ON_OFF => KeyError
            with self.assertRaises(KeyError):
                rsim.start("case", [
                    (2, {"WELL_ORDER" : {"W1": 0, "W2": 0, "W3": 1}})])

            # One of the numeric vectors has wrong length => ValueError:
            with self.assertRaises(KeyError):
                rsim.start("case",
                           [
                               (2,
                                {
                                    "WELL_ORDER": {"W1": 0, "W2": 0, "W3": 1},
                                    "WELL_ON_OFF": {"W2": 0}
                                }),
                           ])

            # Not numeric values => Exception
            with self.assertRaises(Exception):
                rsim.start("case",
                           [
                               (2,
                                {
                                    "WELL_ORDER": {"W1": 0, "W2": 0, "W3": 1},
                                    "WELL_ON_OFF": {"W1": 0, "W2": 1, "W3": 'X'}
                                }),
                           ])

            # Not numeric values => Exception
            with self.assertRaises(Exception):
                rsim.start("case",
                           [
                               ('2',
                                {
                                    "WELL_ORDER": {"W1": 0, "W2": 0, "W3": 1},
                                    "WELL_ON_OFF" : {"W1": 0, "W2": 1, "W3": 4},
                                }),
                           ])


    def test_batch_simulation(self):
        config_file = self.createTestPath("local/batch_sim/batch_sim.ert")

        with TestAreaContext("batch_sim") as test_area:
            test_area.copy_parent_content(config_file)

            res_config = ResConfig(user_config_file=os.path.basename(config_file))
            monitor = TestMonitor()
            rsim = BatchSimulator(res_config,
                                  {
                                      "WELL_ORDER" : ["W1", "W2", "W3"],
                                      "WELL_ON_OFF" : ["W1", "W2", "W3"]
                                  },
                                  ["ORDER", "ON_OFF"],
                                  callback=monitor.start_callback)

            # Starting a simulation which should actually run through.
            case_data = [
                (2,
                 {
                     "WELL_ORDER": {"W1": 1, "W2": 2, "W3": 3},
                     "WELL_ON_OFF": {"W1": 4, "W2": 5, "W3": 6}
                 }),
                (1,
                 {
                     "WELL_ORDER": {"W1": 7, "W2": 8, "W3": 9},
                     "WELL_ON_OFF" : {"W1": 10, "W2": 11, "W3": 12}
                 }),
            ]

            ctx = rsim.start("case", case_data)
            self.assertTrue( isinstance(ctx.status_timestamp(), datetime.datetime))
            start_time = ctx.status_timestamp()
            progress_ts = ctx.progress_timestamp()

            # Asking for results before it is complete.
            with self.assertRaises(RuntimeError):
                ctx.results()

            # Ask for status of simulation we do not have.
            with self.assertRaises(KeyError):
                ctx.job_status(1973)

            with self.assertRaises(KeyError):
                ctx.job_progress(1987)

            # Carry out simulations..
            while ctx.running():
                status = ctx.status
                time.sleep(1)
                sys.stderr.write("status: %s\n" % str(status))
                for job_index in range(len(case_data)):
                    status = ctx.job_status(job_index)
                    progress = ctx.job_progress(job_index)
                    if progress:
                        for job in progress.jobs:
                            sys.stderr.write("   %s ts: %s \n" % (str(job), ctx.progress_timestamp(job_index)))

            # Fetch and validate results
            results = ctx.results()
            self.assertEqual(len(results), 2)
            self.assertTrue( ctx.status_timestamp() > start_time )

            for result, (_, controls) in zip(results, case_data):
                self.assertEqual(sorted(["ORDER", "ON_OFF"]),
                                 sorted(result.keys()))

                for res_key, ctrl_key in (
                        ("ORDER", "WELL_ORDER"),
                        ("ON_OFF", "WELL_ON_OFF"),
                    ):

                    # The forward model job SQUARE_PARAMS will load the control
                    # values and square them before writing results to disk in
                    # the order W1, W2, W3.
                    self.assertEqual(
                        [controls[ctrl_key][var_name]**2 for var_name in ["W1", "W2", "W3"]],
                        list(result[res_key])
                        )

            self.assertTrue( isinstance(monitor.sim_context, BatchContext))


    def test_stop_sim(self):
        config_file = self.createTestPath("local/batch_sim/batch_sim.ert")
        with TestAreaContext("batch_sim_stop") as test_area:
            test_area.copy_parent_content(config_file)
            res_config = ResConfig(user_config_file=os.path.basename(config_file))

            rsim = BatchSimulator(res_config,
                                  {
                                      "WELL_ORDER" : ["W1", "W2", "W3"],
                                      "WELL_ON_OFF" : ["W1", "W2", "W3"]
                                  },
                                  ["ORDER", "ON_OFF"])

            case_name = 'MyCaseName_123'

            # Starting a simulation which should actually run through.
            ctx = rsim.start(case_name,
                             [
                                 (2,
                                  {
                                      "WELL_ORDER": {"W1": 1, "W2": 2, "W3": 3},
                                      "WELL_ON_OFF": {"W1": 4, "W2": 5, "W3": 6}
                                  }),
                                 (1,
                                  {
                                      "WELL_ORDER": {"W1": 7, "W2": 8, "W3": 9},
                                      "WELL_ON_OFF": {"W1": 10, "W2": 11, "W3": 12}
                                  })
                             ])

            ctx.stop()
            status = ctx.status

            self.assertEqual(status.complete, 0)
            self.assertEqual(status.running, 0)

            runpath = 'storage/batch_sim/runpath/%s/realisation-0' % case_name
            self.assertTrue(os.path.exists(runpath))


if __name__ == "__main__":
    unittest.main()
