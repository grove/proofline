import copy
import itertools
import json
import pathlib
import subprocess
import sys
import unittest

import app
import service


class AllocationTests(unittest.TestCase):
    def test_known_allocations(self):
        cases = [
            (0, [1, 2, 0], [0, 0, 0]),
            (1000, [7], [1000]),
            (7, [0, 5, 0], [0, 7, 0]),
            (7, [1, 1, 1], [3, 2, 2]),
            (2, [1, 1, 1], [1, 1, 0]),
            (10, [1, 2, 3], [2, 3, 5]),
            (5, [1] * 10, [1] * 5 + [0] * 5),
            (1, [10**100, 10**100 + 1], [0, 1]),
        ]
        for units, weights, expected in cases:
            with self.subTest(units=units, weights=weights):
                payload = {"units": units, "weights": weights}
                original = copy.deepcopy(payload)
                self.assertEqual(app.process(payload), {"allocations": expected})
                self.assertEqual(payload, original)

    def test_small_cases_obey_allocation_rules(self):
        for length in range(1, 5):
            for weights in itertools.product(range(4), repeat=length):
                total = sum(weights)
                if total == 0:
                    continue
                for units in range(11):
                    result = app.process({"units": units, "weights": list(weights)})
                    allocations = result["allocations"]
                    floors = [units * weight // total for weight in weights]
                    bonuses = [allocated - floor for allocated, floor in zip(allocations, floors)]
                    self.assertEqual(sum(allocations), units)
                    self.assertTrue(all(type(value) is int for value in allocations))
                    self.assertTrue(all(bonus in (0, 1) for bonus in bonuses))
                    # Every recipient precedes every nonrecipient by remainder,
                    # with earlier indices taking priority when remainders tie.
                    for recipient in range(length):
                        if bonuses[recipient] != 1:
                            continue
                        for other in range(length):
                            if bonuses[other] != 0:
                                continue
                            self.assertGreater(
                                (units * weights[recipient] % total, -recipient),
                                (units * weights[other] % total, -other),
                            )

    def test_malformed_payloads_raise_value_error(self):
        invalid = [None, [], True, 1, "payload", {}, {"units": 1}, {"weights": [1]}]
        invalid += [{"units": units, "weights": [1]} for units in
                    (None, True, False, -1, 1001, 1.0, "1", [], {})]
        invalid += [{"units": 1, "weights": weights} for weights in
                    (None, (), (1,), "1", {}, [], [1] * 11, [0], [0, 0],
                     [True], [False, 1], [-1, 2], [1.0], ["1"], [None], [[1]], [{}])]
        for payload in invalid:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    app.process(payload)

    def test_service_handle(self):
        self.assertEqual(service.handle({"units": 2, "weights": [1, 1, 1]}),
                         {"allocations": [1, 1, 0]})

    def test_json_cli(self):
        repo = pathlib.Path(__file__).resolve().parents[1]
        for payload, expected_code, expected_output in [
            ({"units": 2, "weights": [1, 1, 1]}, 0, {"allocations": [1, 1, 0]}),
            ({"units": True, "weights": [1]}, 2, None),
        ]:
            with self.subTest(payload=payload):
                result = subprocess.run(
                    [sys.executable, "-B", str(repo / "cli.py")],
                    input=json.dumps(payload), cwd=repo,
                    capture_output=True, text=True, timeout=5,
                )
                self.assertEqual(result.returncode, expected_code)
                if expected_code == 0:
                    self.assertEqual(json.loads(result.stdout), expected_output)
                    self.assertEqual(result.stderr, "")
                else:
                    self.assertEqual(result.stdout, "")
                    self.assertTrue(result.stderr.startswith("ERROR: "))
