import unittest

from .tasks import Task, topological_sort


class TestTopologicalSort(unittest.TestCase):
    def testNoDependencies(self):
        tasks = {
            "A": Task("A"),
        }
        self.assertEqual(topological_sort(tasks), ["A"])
        tasks = {
            "A": Task("A"),
            "B": Task("B"),
        }
        self.assertEqual(topological_sort(tasks), ["A", "B"])
        tasks = {
            "A": Task("A"),
            "B": Task("B"),
            "C": Task("C"),
        }
        self.assertEqual(topological_sort(tasks), ["A", "B", "C"])

    def testSingleDependency(self):
        tasks = {
            "A": Task("A"),
            "B": Task("B", dependencies=["A"]),
            "C": Task("C"),
        }
        self.assertEqual(topological_sort(tasks), ["A", "B", "C"])
        tasks = {
            "A": Task("A"),
            "B": Task("B", dependencies=["C"]),
            "C": Task("C"),
        }
        self.assertEqual(topological_sort(tasks), ["A", "C", "B"])
        tasks = {
            "A": Task("A"),
            "B": Task("B", dependencies=["C"]),
            "C": Task("C", dependencies=["A"]),
        }
        self.assertEqual(topological_sort(tasks), ["A", "C", "B"])
        tasks = {
            "A": Task("A"),
            "B": Task("B", dependencies=["C"]),
            "C": Task("C", dependencies=["D"]),
            "D": Task("D"),
        }
        self.assertEqual(topological_sort(tasks), ["A", "D", "C", "B"])
        tasks = {
            "A": Task("A"),
            "B": Task("B", dependencies=["C"]),
            "C": Task("C", dependencies=["A"]),
            "D": Task("D", dependencies=["B"]),
        }
        self.assertEqual(topological_sort(tasks), ["A", "C", "B", "D"])

    def testMultipleDependencies(self):
        tasks = {
            "A": Task("A"),
            "B": Task("B", dependencies=["A"]),
            "C": Task("C", dependencies=["A"]),
            "D": Task("D", dependencies=["B", "C", "A"]),
        }
        self.assertEqual(topological_sort(tasks), ["A", "B", "C", "D"])
        tasks = {
            "A": Task("A"),
            "B": Task("B", dependencies=["A", "C"]),
            "C": Task("C", dependencies=["A"]),
            "D": Task("D", dependencies=["B", "C"]),
        }
        self.assertEqual(topological_sort(tasks), ["A", "C", "B", "D"])
        tasks = {
            "A": Task("A", dependencies=["E"]),
            "B": Task("B", dependencies=["A", "C"]),
            "C": Task("C", dependencies=["A"]),
            "D": Task("D", dependencies=["B", "C"]),
            "E": Task("E"),
        }
        self.assertEqual(topological_sort(tasks), ["E", "A", "C", "B", "D"])

    def testCircularDependency(self):
        tasks = {
            "A": Task("A", dependencies=["B"]),
            "B": Task("B", dependencies=["A"]),
        }
        with self.assertRaises(ValueError) as e:
            topological_sort(tasks)
        tasks = {
            "A": Task("A", dependencies=["B"]),
            "B": Task("B", dependencies=["C"]),
            "C": Task("C", dependencies=["A"]),
        }
        with self.assertRaises(ValueError) as e:
            topological_sort(tasks)
        tasks = {
            "A": Task("A", dependencies=["B"]),
            "B": Task("B", dependencies=["C"]),
            "C": Task("C", dependencies=["D"]),
            "D": Task("D", dependencies=["A"]),
        }
        with self.assertRaises(ValueError) as e:
            topological_sort(tasks)

    def testUnknownTask(self):
        tasks = {
            "A": Task("A", dependencies=["B"]),
        }
        with self.assertRaises(ValueError) as e:
            topological_sort(tasks)
        tasks = {
            "A": Task("A", dependencies=["B"]),
            "B": Task("B", dependencies=["C"]),
        }
        with self.assertRaises(ValueError) as e:
            topological_sort(tasks)
        tasks = {
            "A": Task("A", dependencies=["E"]),
            "B": Task("B", dependencies=["C"]),
            "C": Task("C"),
        }


unittest.main()
