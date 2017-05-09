import io
import json
import unittest
from unittest.mock import patch, call
from zipfile import ZipFile

import webui


class ControllerTest(unittest.TestCase):

    def setUp(self):
        webui.app.config['TESTING'] = True
        self.app = webui.app.test_client()

    @patch('webui.views.controller.load_profile')
    @patch('webui.views.controller.send_request')
    def test_controller_start(self, send_request, load_profile):
        load_profile.return_value = [(0.0, 20.0), (60.0, 30.0), (120.0, 25.0)]
        self.app.post('/controller/start', data={'temperatureprofile': 'profile1'})
        load_profile.assert_called_with('profile1')
        send_request.assert_called_with({'id': 'start', 'trajectory': [(0.0, 20.0), (60.0, 30.0), (120.0, 25.0)]})

    @patch('webui.views.controller.send_request')
    def test_controller_stop(self, send_request):
        self.app.post('/controller/stop')
        send_request.assert_called_with({'id': 'stop'})

    @patch('webui.views.controller.send_request')
    def test_controller_status(self, send_request):
        send_request.side_effect = [
            {'response': 'ok', 'status': 'standby'},
            {'response': 'ok', 'status': 'stopping'},
            {'response': 'ok', 'status': 'running'},
        ]

        response = self.app.get('/controller/status')
        send_request.assert_called_with({'id': 'status'})
        self.assertEqual(
            json.loads(response.data),
            'Nicht aktiv'
        )

        response = self.app.get('/controller/status')
        self.assertEqual(
            json.loads(response.data),
            'Wird angehalten...',
        )

        response = self.app.get('/controller/status')
        self.assertEqual(
            json.loads(response.data),
            'Aktiv'
        )

    @patch('webui.views.controller.send_request')
    def test_controller_temperature(self, send_request):
        send_request.return_value = {
            'response': 'ok',
            'temperatures': [42.0, 13.0]
        }
        response = self.app.get('/controller/temperature')
        send_request.assert_called_with({'id': 'temperature'})
        self.assertEqual(json.loads(response.data), [42.0, 13.0])

    @patch('webui.views.controller.send_request')
    def test_controller_temperature_error(self, send_request):
        send_request.return_value = {
            'response': 'error',
            'temperatures': []
        }
        response = self.app.get('/controller/temperature')
        send_request.assert_called_with({'id': 'temperature'})
        self.assertEqual(json.loads(response.data), [])

    @patch('webui.views.controller.send_request')
    def test_controller_trajectory(self, send_request):
        send_request.return_value = {
            'response': 'ok',
            'trajectory': [(0.0, 20.0), (60.0, 30.0), (120.0, 25.0)]
        }
        response = self.app.get('/controller/trajectory')
        send_request.assert_called_with({'id': 'trajectory'})
        self.assertEqual(
            json.loads(response.data),
            [
                {'time': 0.0, 'temperature': 20.0},
                {'time': 1.0, 'temperature': 30.0},
                {'time': 2.0, 'temperature': 25.0},
            ])

    @patch('webui.views.controller.send_request')
    def test_controller_trajectory_error(self, send_request):
        send_request.return_value = {
            'response': 'error',
            'trajectory': []
        }
        response = self.app.get('/controller/trajectory')
        send_request.assert_called_with({'id': 'trajectory'})
        self.assertEqual(json.loads(response.data), [])

    @patch('webui.views.controller.send_request')
    def test_controller_measurement(self, send_request):
        send_request.return_value = {
            'response': 'ok',
            'measurement': [(0, 20.0, 40.0, 0.0), (60, 30.0, 45.0, 0.0), (120, 25.0, 55.0, 0.0)]
        }
        response = self.app.get('/controller/measurement')
        send_request.assert_called_with({'id': 'measurement'})
        self.assertEqual(
            json.loads(response.data),
            {
                'measurement': [
                    {'time': 0.0, 'temperature': 40.0},
                    {'time': 1.0, 'temperature': 45.0},
                    {'time': 2.0, 'temperature': 55.0},
                ],
                'reference': [
                    {'time': 0.0, 'temperature': 20.0},
                    {'time': 1.0, 'temperature': 30.0},
                    {'time': 2.0, 'temperature': 25.0},
                ]
            })

    @patch('webui.views.controller.send_request')
    def test_controller_measurement_snapshot(self, send_request):
        send_request.side_effect = [
            {
                'response': 'ok',
                'measurement': [(0, 20.0, 40.0, 0.0), (60, 30.0, 45.0, 0.0), (120, 25.0, 55.0, 0.0)]
            },
            {
                'response': 'ok',
                'trajectory': [(0.0, 20.0), (60.0, 30.0), (120.0, 25.0)]
            }
        ]
        response = self.app.get('/controller/snapshot')
        self.assertListEqual(send_request.mock_calls, [call({'id': 'measurement'}), call({'id': 'trajectory'})])
        data = io.BytesIO(response.data)
        with ZipFile(data) as zipfile:
            measurement_data = zipfile.read('measurement.json')
            self.assertEqual(
                json.loads(measurement_data),
                {
                    'response': 'ok',
                    'measurement': [[0, 20.0, 40.0, 0.0], [60, 30.0, 45.0, 0.0], [120, 25.0, 55.0, 0.0]]
                })
            trajectory_data = zipfile.read('trajectory.json')
            self.assertEqual(
                json.loads(trajectory_data),
                {
                    'response': 'ok',
                    'trajectory': [[0.0, 20.0], [60.0, 30.0], [120.0, 25.0]]
                })


if __name__ == '__main__':
    unittest.main()
