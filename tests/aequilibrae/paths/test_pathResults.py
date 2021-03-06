from unittest import TestCase
import sys, os
from aequilibrae.paths import path_computation, Graph
from aequilibrae.paths.results import PathResults

# Adds the folder with the data to the path and collects the paths to the files
lib_path = os.path.abspath(os.path.join('..', '../tests'))
sys.path.append(lib_path)
from data import path_test, test_graph

origin = 5
dest =27

class TestPathResults(TestCase):
    def test_prepare(self):
        # graph
        self.g = Graph()
        self.g.load_from_disk(test_graph)
        self.g.set_graph(cost_field='distance', skim_fields=None)

        self.r = PathResults()
        try:
            self.r.prepare(self.g)
        except:
            self.fail('Path result preparation failed')


    def test_reset(self):
        self.test_prepare()
        try:
            self.r.reset()
        except:
            self.fail('Path result resetting failed')

    def test_update_trace(self):
        self.test_prepare()
        try:
            self.r.reset()
        except:
            self.fail('Path result resetting failed')

        path_computation(origin, dest, self.g, self.r)

        if list(self.r.path) != [53, 52, 13]:
            self.fail('Path computation failed. Wrong sequence of links')

        if list(self.r.path_nodes) != [5, 168, 166, 27]:
            self.fail('Path computation failed. Wrong sequence of path nodes')

        if list(self.r.milepost) != [0, 341, 1398, 2162]:
            self.fail('Path computation failed. Wrong milepost results')
