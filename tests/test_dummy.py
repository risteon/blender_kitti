import blender_kitti_examples
import unittest
import os


class TestStuff(unittest.TestCase):
    def __init__(self, test_name):
        super(TestStuff, self).__init__(test_name)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_example_is_working(self):
        blender_kitti_examples.render_kitti_point_cloud()
        print("This is just a really basic test for demonstration purposes!")
        print("Replace with more sensible tests!")

        num_pngs = len(
            [
                name
                for name in os.listdir("/tmp")
                if os.path.isfile(os.path.join("/tmp", name)) and name.endswith(".png")
            ]
        )
        self.assertTrue(
            num_pngs > 0, "render_kitti_point_cloud example did not produce any .png"
        )


if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    loader = unittest.TestLoader()
    suite = loader.discover(dir_path)

    unittest.TextTestRunner(verbosity=2).run(suite)
