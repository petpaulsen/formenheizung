import json
import os.path
import unittest

import flask_testing

import webui


class PlotTest(flask_testing.TestCase):

    def create_app(self):
        webui.app.config['TESTING'] = True
        webui.app.config['PROFILE_DIRECTORY'] = os.path.join(os.path.dirname(__file__))
        return webui.app

    def test_plot(self):
        self.client.get('/plot/')
        self.assertTemplateUsed('plot.html')

    def test_trajectory_preview(self):
        response = self.client.get('/plot/trajectory-preview', query_string={'temperatureprofile': 'profile'})
        self.assertEqual(
            json.loads(response.data),
            [
                {'time': 0.0, 'temperature': 20.0},
                {'time': 0.5, 'temperature': 30.0},
                {'time': 5.0, 'temperature': 50.0},
                {'time': 15.0, 'temperature': 60.0},
                {'time': 20.0, 'temperature': 60.0},
                {'time': 30.0, 'temperature': 50.0},
                {'time': 60.0, 'temperature': 20.0},
            ])


if __name__ == '__main__':
    unittest.main()
