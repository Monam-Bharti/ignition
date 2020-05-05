import connexion
import unittest
from unittest.mock import patch, MagicMock
from ignition.api.exceptions import BadRequest
from ignition.model.infrastructure import InfrastructureTask, CreateInfrastructureResponse, DeleteInfrastructureResponse, FindInfrastructureResponse, FindInfrastructureResult
from ignition.model.failure import FailureDetails, FAILURE_CODE_INFRASTRUCTURE_ERROR
from ignition.service.infrastructure import InfrastructureService, InfrastructureApiService, InfrastructureTaskMonitoringService, InfrastructureMessagingService, TemporaryInfrastructureError, UnreachableDeploymentLocationError, InfrastructureNotFoundError, InfrastructureRequestNotFoundError
from ignition.service.messaging import Envelope, Message
from ignition.service.logging import LM_HTTP_HEADER_PREFIX, LM_HTTP_HEADER_TXNID
from ignition.service.messaging import Envelope, Message, TopicConfigProperties
from ignition.utils.propvaluemap import PropValueMap

class TestInfrastructureApiService(unittest.TestCase):

    def __props_with_types(self, orig_props):
        return {k:{'type': 'string', 'value': v} for k,v in orig_props.items()}

    def __propvaluemap(self, orig_props):
        return PropValueMap(self.__props_with_types(orig_props))

    @patch('ignition.service.infrastructure.logging_context')
    def test_init_without_service_throws_error(self, logging_context):
        with self.assertRaises(ValueError) as context:
            InfrastructureApiService()
        self.assertEqual(str(context.exception), 'No service instance provided')

    @patch('ignition.service.infrastructure.logging_context')
    def test_create(self, logging_context):
        mock_service = MagicMock()
        mock_service.create_infrastructure.return_value = CreateInfrastructureResponse('123', '456')
        controller = InfrastructureApiService(service=mock_service)
        response, code = controller.create(**{ 'body': { 'template': 'template', 'templateType': 'TOSCA', 'systemProperties': self.__props_with_types({'resourceId': '1'}), 'properties': self.__props_with_types({'a': '1'}), 'deploymentLocation': {'name': 'test'} } })
        mock_service.create_infrastructure.assert_called_once_with('template', 'TOSCA', {'resourceId': { 'type': 'string', 'value': '1'}}, {'a': { 'type': 'string', 'value': '1'}}, {'name': 'test'})
        self.assertEqual(response, {'infrastructureId': '123', 'requestId': '456'})
        self.assertEqual(code, 202)
        logging_context.set_from_headers.assert_called_once()

    @patch('ignition.service.infrastructure.logging_context')
    def test_create_missing_template(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.create(**{ 'body': { 'templateType': 'TOSCA', 'systemProperties': self.__props_with_types({'resourceId': '1'}), 'properties': self.__props_with_types({'a': '1'}), 'deploymentLocation': {'name': 'test' } } })
        self.assertEqual(str(context.exception), '\'template\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_create_missing_template_type(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.create(**{ 'body': { 'template': 'template', 'systemProperties': self.__props_with_types({'resourceId': '1'}), 'properties': self.__props_with_types({'a': '1'}), 'deploymentLocation': {'name': 'test' } } })
        self.assertEqual(str(context.exception), '\'templateType\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_create_missing_deployment_location(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.create(**{ 'body': { 'properties': self.__props_with_types({'a': '1'}),  'systemProperties': self.__props_with_types({'resourceId': '1'}), 'template': 'template', 'templateType': 'TOSCA' } })
        self.assertEqual(str(context.exception), '\'deploymentLocation\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_create_missing_system_properties(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.create(**{ 'body': { 'properties': self.__props_with_types({'a': '1'}), 'template': 'template', 'templateType': 'TOSCA', 'deploymentLocation': {'name': 'test'} } })
        self.assertEqual(str(context.exception), '\'systemProperties\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_create_missing_properties_uses_default(self, logging_context):
        mock_service = MagicMock()
        mock_service.create_infrastructure.return_value = CreateInfrastructureResponse('123', '456')
        controller = InfrastructureApiService(service=mock_service)
        response, code = controller.create(**{ 'body': { 'template': 'template', 'templateType': 'TOSCA', 'systemProperties': {'resourceId': '1'}, 'deploymentLocation': {'name': 'test'} } })
        mock_service.create_infrastructure.assert_called_once_with('template', 'TOSCA', {'resourceId': '1'}, {}, {'name': 'test'})
        self.assertEqual(response, {'infrastructureId': '123', 'requestId': '456'})
        self.assertEqual(code, 202)

    @patch('ignition.service.infrastructure.logging_context')
    def test_delete(self, logging_context):
        mock_service = MagicMock()
        mock_service.delete_infrastructure.return_value = DeleteInfrastructureResponse('123', '456')
        controller = InfrastructureApiService(service=mock_service)
        response, code = controller.delete(**{ 'body': { 'infrastructureId': '123', 'deploymentLocation': {'name': 'test'} } })
        mock_service.delete_infrastructure.assert_called_once_with('123', {'name': 'test'})
        self.assertEqual(response, {'infrastructureId': '123', 'requestId': '456'})
        self.assertEqual(code, 202)

    @patch('ignition.service.infrastructure.logging_context')
    def test_delete_missing_deployment_location(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.delete(**{ 'body': { 'infrastructureId': '123' } })
        self.assertEqual(str(context.exception), '\'deploymentLocation\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_delete_missing_infrastructure_id(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.delete(**{ 'body': { 'deploymentLocation': {'name': 'test'} } })
        self.assertEqual(str(context.exception), '\'infrastructureId\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_query(self, logging_context):
        mock_service = MagicMock()
        mock_service.get_infrastructure_task.return_value = InfrastructureTask('123', '456', 'IN_PROGRESS')
        controller = InfrastructureApiService(service=mock_service)
        response, code = controller.query(**{ 'body': { 'infrastructureId': '123', 'requestId': '456', 'deploymentLocation': {'name': 'test'} } })
        mock_service.get_infrastructure_task.assert_called_once_with('123', '456', {'name': 'test'})
        self.assertEqual(response, {'infrastructureId': '123', 'requestId': '456', 'status': 'IN_PROGRESS'})
        self.assertEqual(code, 200)

    @patch('ignition.service.infrastructure.logging_context')
    def test_query_with_outputs(self, logging_context):
        mock_service = MagicMock()
        mock_service.get_infrastructure_task.return_value = InfrastructureTask('123', '456', 'COMPLETE', None, {'a': '1'})
        controller = InfrastructureApiService(service=mock_service)
        response, code = controller.query(**{ 'body': { 'infrastructureId': '123', 'requestId': '456', 'deploymentLocation': {'name': 'test'} } })
        mock_service.get_infrastructure_task.assert_called_once_with('123', '456', {'name': 'test'})
        self.assertEqual(response, {'infrastructureId': '123', 'requestId': '456', 'status': 'COMPLETE', 'outputs': {'a': '1'}})
        self.assertEqual(code, 200)

    @patch('ignition.service.infrastructure.logging_context')
    def test_query_failed_task(self, logging_context):
        mock_service = MagicMock()
        mock_service.get_infrastructure_task.return_value = InfrastructureTask('123', '456', 'FAILED', FailureDetails(FAILURE_CODE_INFRASTRUCTURE_ERROR, 'because it was meant to fail'))
        controller = InfrastructureApiService(service=mock_service)
        response, code = controller.query(**{ 'body': { 'infrastructureId': '123', 'requestId': '456', 'deploymentLocation': {'name': 'test'} } })
        mock_service.get_infrastructure_task.assert_called_once_with('123', '456', {'name': 'test'})
        self.assertEqual(response, {'infrastructureId': '123', 'requestId': '456', 'status': 'FAILED', 'failureDetails': { 'failureCode': FAILURE_CODE_INFRASTRUCTURE_ERROR, 'description': 'because it was meant to fail'}})
        self.assertEqual(code, 200)

    @patch('ignition.service.infrastructure.logging_context')
    def test_query_missing_deployment_location(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.query(**{ 'body': { 'infrastructureId': '123', 'requestId': '456' } })
        self.assertEqual(str(context.exception), '\'deploymentLocation\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_query_missing_infrastructure_id(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.query(**{ 'body': { 'requestId': '456', 'deploymentLocation': {'name': 'test'} } })
        self.assertEqual(str(context.exception), '\'infrastructureId\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_query_missing_request_id(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.query(**{ 'body': { 'infrastructureId': '123', 'deploymentLocation': {'name': 'test'} } })
        self.assertEqual(str(context.exception), '\'requestId\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_find(self, logging_context):
        mock_service = MagicMock()
        mock_service.find_infrastructure.return_value = FindInfrastructureResponse(FindInfrastructureResult('123', {'b': 2}))
        controller = InfrastructureApiService(service=mock_service)
        response, code = controller.find(**{ 'body': { 'template': 'template', 'templateType': 'TOSCA', 'instanceName': 'test', 'deploymentLocation': {'name': 'test'} } })
        mock_service.find_infrastructure.assert_called_once_with('template', 'TOSCA', 'test', {'name': 'test'})
        self.assertEqual(response, {'result': {'infrastructureId': '123', 'outputs': {'b': 2} } })
        self.assertEqual(code, 200)

    @patch('ignition.service.infrastructure.logging_context')
    def test_find_not_found(self, logging_context):
        mock_service = MagicMock()
        mock_service.find_infrastructure.return_value = FindInfrastructureResponse(None)
        controller = InfrastructureApiService(service=mock_service)
        response, code = controller.find(**{ 'body': { 'template': 'template', 'templateType': 'TOSCA', 'instanceName': 'test', 'deploymentLocation': {'name': 'test'} } })
        mock_service.find_infrastructure.assert_called_once_with('template', 'TOSCA', 'test', {'name': 'test'})
        self.assertEqual(response, {'result': None})
        self.assertEqual(code, 200)

    @patch('ignition.service.infrastructure.logging_context')
    def test_find_missing_template(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.find(**{ 'body': { 'templateType': 'TOSCA', 'deploymentLocation': {'name': 'test' } } })
        self.assertEqual(str(context.exception), '\'template\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_find_missing_template_type(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.find(**{ 'body': { 'template': 'template', 'deploymentLocation': {'name': 'test' } } })
        self.assertEqual(str(context.exception), '\'templateType\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_find_missing_deployment_location(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.find(**{ 'body': { 'instanceName': 'test', 'template': 'template', 'templateType': 'TOSCA' } })
        self.assertEqual(str(context.exception), '\'deploymentLocation\' is a required field but was not found in the request data body')

    @patch('ignition.service.infrastructure.logging_context')
    def test_find_missing_instance_name(self, logging_context):
        mock_service = MagicMock()
        controller = InfrastructureApiService(service=mock_service)
        with self.assertRaises(BadRequest) as context:
            controller.find(**{ 'body': { 'deploymentLocation': {'name': 'test' }, 'template': 'template', 'templateType': 'TOSCA' } })
        self.assertEqual(str(context.exception), '\'instanceName\' is a required field but was not found in the request data body')

class TestInfrastructureService(unittest.TestCase):

    def __props_with_types(self, orig_props):
        return {k:{'type': 'string', 'value': v} for k,v in orig_props.items()}

    def __propvaluemap(self, orig_props):
        return PropValueMap(self.__props_with_types(orig_props))

    def assert_requests_equal(self, actual_request, expected_request):
        expected_request_id = expected_request.get('request_id', None)
        expected_infrastructure_id = expected_request.get('infrastructure_id', None)
        expected_template = expected_request.get('template', None)
        expected_template_type = expected_request.get('template_type', None)
        expected_properties = expected_request.get('properties', None)
        expected_system_properties = expected_request.get('system_properties', None)
        expected_deployment_location = expected_request.get('deployment_location', None)
        if expected_request_id is not None:
            actual_request_id = actual_request.get('request_id', None)
            self.assertIsNotNone(actual_request_id)
            self.assertEqual(expected_request_id, actual_request_id)

        if expected_infrastructure_id is not None:
            actual_infrastructure_id = actual_request.get('infrastructure_id', None)
            self.assertIsNotNone(actual_infrastructure_id)
            self.assertEqual(expected_infrastructure_id, actual_infrastructure_id)

        if expected_template is not None:
            actual_template = actual_request.get('template', None)
            self.assertIsNotNone(actual_template)
            self.assertEqual(expected_template, actual_template)

        if expected_template_type is not None:
            actual_template_type = actual_request.get('template_type', None)
            self.assertIsNotNone(actual_template_type)
            self.assertEqual(expected_template_type, actual_template_type)

        if expected_deployment_location is not None:
            actual_deployment_location = actual_request.get('deployment_location', None)
            self.assertIsNotNone(actual_deployment_location)
            self.assertDictEqual(expected_deployment_location, actual_deployment_location)

        if expected_properties is not None:
            actual_properties = actual_request.get('properties', None)
            self.assertIsNotNone(actual_properties)
            self.assertDictEqual(expected_properties, actual_properties)

        if expected_system_properties is not None:
            actual_system_properties = actual_request.get('system_properties', None)
            self.assertIsNotNone(actual_system_properties)
            self.assertDictEqual(expected_system_properties, actual_system_properties)

    def test_init_without_driver_throws_error(self):
        mock_infrastructure_config = MagicMock()
        with self.assertRaises(ValueError) as context:
            InfrastructureService(infrastructure_config=mock_infrastructure_config)
        self.assertEqual(str(context.exception), 'driver argument not provided')

    def test_init_without_configuration_throws_error(self):
        mock_service_driver = MagicMock()
        with self.assertRaises(ValueError) as context:
            InfrastructureService(driver=mock_service_driver)
        self.assertEqual(str(context.exception), 'infrastructure_config argument not provided')

    def test_init_without_monitor_service_when_async_enabled_throws_error(self):
        mock_service_driver = MagicMock()
        mock_infrastructure_config = MagicMock()
        mock_infrastructure_config.async_messaging_enabled = True
        with self.assertRaises(ValueError) as context:
            InfrastructureService(driver=mock_service_driver, infrastructure_config=mock_infrastructure_config)
        self.assertEqual(str(context.exception), 'inf_monitor_service argument not provided (required when async_messaging_enabled is True)')

    def test_init_without_request_queue_service_when_async_requests_enabled_throws_error(self):
        mock_service_driver = MagicMock()
        mock_infrastructure_config = MagicMock()
        mock_infrastructure_config.async_messaging_enabled = False
        mock_infrastructure_config.request_queue.enabled = True
        with self.assertRaises(ValueError) as context:
            InfrastructureService(driver=mock_service_driver, infrastructure_config=mock_infrastructure_config)
        self.assertEqual(str(context.exception), 'request_queue argument not provided (required when async_requests_enabled is True)')

    def test_create_with_request_queue(self):
        mock_service_driver = MagicMock()
        mock_request_queue = MagicMock()
        mock_infrastructure_config = MagicMock()
        mock_infrastructure_config.async_messaging_enabled = False
        mock_infrastructure_config.request_queue.enabled = True
        service = InfrastructureService(driver=mock_service_driver, infrastructure_config=mock_infrastructure_config, request_queue=mock_request_queue)
        template = 'template'
        template_type = 'TOSCA'
        system_properties = {'resourceId': '1'}
        properties = {'propA': 'valueA'}
        deployment_location = {'name': 'TestDl'}
        result = service.create_infrastructure(template, template_type, system_properties, properties, deployment_location)
        self.assertIsNotNone(result.infrastructure_id)
        self.assertIsNotNone(result.request_id)
        mock_service_driver.create_infrastructure.assert_not_called()
        mock_request_queue.queue_infrastructure_request.assert_called_once()
        name, args, kwargs = mock_request_queue.queue_infrastructure_request.mock_calls[0]
        request = args[0]
        self.assert_requests_equal(request, {
            'infrastructure_id': result.infrastructure_id,
            'request_id': result.request_id,
            'template': template,
            'template_type': template_type,
            'properties': properties,
            'system_properties': system_properties,
            'deployment_location': deployment_location
        })

    def test_create_infrastructure_uses_driver(self):
        mock_service_driver = MagicMock()
        create_response = CreateInfrastructureResponse('test', 'test_req')
        mock_service_driver.create_infrastructure.return_value = create_response
        mock_infrastructure_config = MagicMock()
        mock_infrastructure_config.async_messaging_enabled = False
        mock_infrastructure_config.request_queue.enabled = False
        service = InfrastructureService(driver=mock_service_driver, infrastructure_config=mock_infrastructure_config)
        template = 'template'
        template_type = 'TOSCA'
        system_properties = self.__propvaluemap({'resourceId': '1'})
        properties = self.__propvaluemap({'propA': 'valueA'})
        deployment_location = {'name': 'TestDl'}
        result = service.create_infrastructure(template, template_type, system_properties, properties, deployment_location)
        mock_service_driver.create_infrastructure.assert_called_once_with(template, template_type, self.__propvaluemap(system_properties), self.__propvaluemap(properties), deployment_location)
        self.assertEqual(result, create_response)

    def test_create_infrastructure_uses_monitor_when_async_enabled(self):
        mock_service_driver = MagicMock()
        create_response = CreateInfrastructureResponse('test', 'test_req')
        mock_service_driver.create_infrastructure.return_value = create_response
        mock_infrastructure_config = MagicMock()
        mock_infrastructure_config.async_messaging_enabled = True
        mock_infrastructure_config.request_queue.enabled = False
        mock_inf_monitor_service = MagicMock()
        service = InfrastructureService(driver=mock_service_driver, infrastructure_config=mock_infrastructure_config, inf_monitor_service=mock_inf_monitor_service)
        template = 'template'
        template_type = 'TOSCA'
        system_properties = self.__propvaluemap({'resourceId': '1'})
        properties = self.__propvaluemap({'propA': 'valueA'})
        deployment_location = {'name': 'TestDl'}
        result = service.create_infrastructure(template, template_type, self.__propvaluemap(system_properties), self.__propvaluemap(properties), deployment_location)
        mock_inf_monitor_service.monitor_task.assert_called_once_with('test', 'test_req', deployment_location)

    def test_get_infrastructure_task_uses_driver(self):
        mock_service_driver = MagicMock()
        retuned_task = InfrastructureTask('test', 'test_req', 'COMPLETE', None)
        mock_service_driver.get_infrastructure_task.return_value = retuned_task
        mock_infrastructure_config = MagicMock()
        mock_infrastructure_config.async_messaging_enabled = False
        mock_infrastructure_config.request_queue.enabled = False
        service = InfrastructureService(driver=mock_service_driver, infrastructure_config=mock_infrastructure_config)
        infrastructure_id = 'test'
        request_id = 'test_req'
        deployment_location = {'name': 'TestDl'}
        result = service.get_infrastructure_task(infrastructure_id, request_id, deployment_location)
        mock_service_driver.get_infrastructure_task.assert_called_once_with(infrastructure_id, request_id, deployment_location)
        self.assertEqual(result, retuned_task)

    def test_delete_infrastructure_uses_driver(self):
        mock_service_driver = MagicMock()
        delete_response = DeleteInfrastructureResponse('test', 'test_req')
        mock_service_driver.delete_infrastructure.return_value = delete_response
        mock_infrastructure_config = MagicMock()
        mock_infrastructure_config.async_messaging_enabled = False
        mock_infrastructure_config.request_queue.enabled = False
        service = InfrastructureService(driver=mock_service_driver, infrastructure_config=mock_infrastructure_config)
        infrastructure_id = 'test'
        deployment_location = {'name': 'TestDl'}
        result = service.delete_infrastructure(infrastructure_id, deployment_location)
        mock_service_driver.delete_infrastructure.assert_called_once_with(infrastructure_id, deployment_location)
        self.assertEqual(result, delete_response)

    def test_delete_infrastructure_uses_monitor_when_async_enabled(self):
        mock_service_driver = MagicMock()
        delete_response = DeleteInfrastructureResponse('test', 'test_req')
        mock_service_driver.delete_infrastructure.return_value = delete_response
        mock_infrastructure_config = MagicMock()
        mock_infrastructure_config.async_messaging_enabled = True
        mock_infrastructure_config.request_queue.enabled = False
        mock_inf_monitor_service = MagicMock()
        service = InfrastructureService(driver=mock_service_driver, infrastructure_config=mock_infrastructure_config, inf_monitor_service=mock_inf_monitor_service)
        infrastructure_id = 'test'
        deployment_location = {'name': 'TestDl'}
        result = service.delete_infrastructure(infrastructure_id, deployment_location)
        mock_inf_monitor_service.monitor_task.assert_called_once_with('test', 'test_req', deployment_location)

    def test_find_infrastructure_uses_driver(self):
        mock_service_driver = MagicMock()
        find_response = FindInfrastructureResponse(FindInfrastructureResult('123', {'outputA': 1}))
        mock_service_driver.find_infrastructure.return_value = find_response
        mock_infrastructure_config = MagicMock()
        mock_infrastructure_config.async_messaging_enabled = False
        mock_infrastructure_config.request_queue.enabled = False
        service = InfrastructureService(driver=mock_service_driver, infrastructure_config=mock_infrastructure_config)
        template = 'template'
        template_type = 'TOSCA'
        instance_name = 'valueA'
        deployment_location = {'name': 'TestDl'}
        result = service.find_infrastructure(template, template_type, instance_name, deployment_location)
        mock_service_driver.find_infrastructure.assert_called_once_with(template, template_type, instance_name, deployment_location)
        self.assertEqual(result, find_response)


class TestInfrastructureTaskMonitoringService(unittest.TestCase):

    def setUp(self):
        self.mock_job_queue = MagicMock()
        self.mock_inf_messaging_service = MagicMock()
        self.mock_driver = MagicMock()
    
    def test_init_without_job_queue_throws_error(self):
        with self.assertRaises(ValueError) as context:
            InfrastructureTaskMonitoringService(inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        self.assertEqual(str(context.exception), 'job_queue_service argument not provided')

    def test_init_without_inf_messaging_service_throws_error(self):
        with self.assertRaises(ValueError) as context:
            InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, driver=self.mock_driver)
        self.assertEqual(str(context.exception), 'inf_messaging_service argument not provided')

    def test_init_without_driver_throws_error(self):
        with self.assertRaises(ValueError) as context:
            InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service)
        self.assertEqual(str(context.exception), 'driver argument not provided')

    def test_init_registers_handler_to_job_queue(self):
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        self.mock_job_queue.register_job_handler.assert_called_once_with('InfrastructureTaskMonitoring', monitoring_service.job_handler)

    def test_monitor_task_schedules_job(self):
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        monitoring_service.monitor_task('inf123', 'req123', {'name': 'TestDl'})
        self.mock_job_queue.queue_job.assert_called_once_with({
            'job_type': 'InfrastructureTaskMonitoring',
            'infrastructure_id': 'inf123',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })

    def test_monitor_task_throws_error_when_infrastructure_id_is_none(self):
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        with self.assertRaises(ValueError) as context:
            monitoring_service.monitor_task(None, 'req123', {'name': 'TestDl'})
        self.assertEqual(str(context.exception), 'Cannot monitor task when infrastructure_id is not given')
    
    def test_monitor_task_throws_error_when_request_id_is_none(self):
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        with self.assertRaises(ValueError) as context:
            monitoring_service.monitor_task('inf123', None, {'name': 'TestDl'})
        self.assertEqual(str(context.exception), 'Cannot monitor task when request_id is not given')
        
    def test_monitor_task_throws_error_when_deployment_location_is_none(self):
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        with self.assertRaises(ValueError) as context:
            monitoring_service.monitor_task('inf123', 'req123', None)
        self.assertEqual(str(context.exception), 'Cannot monitor task when deployment_location is not given')

    def test_job_handler_does_not_mark_job_as_finished_if_temporary_error_thrown(self):
        self.mock_driver.get_infrastructure_task.side_effect = TemporaryInfrastructureError('Retry it')
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'InfrastructureTaskMonitoring',
            'infrastructure_id': 'inf123',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, False)
        self.mock_driver.get_infrastructure_task.assert_called_once_with('inf123', 'req123', {'name': 'TestDl'})

    def test_job_handler_does_not_mark_job_as_finished_if_unreachable_dl_error_thrown(self):
        self.mock_driver.get_infrastructure_task.side_effect = UnreachableDeploymentLocationError('Retry it')
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'InfrastructureTaskMonitoring',
            'infrastructure_id': 'inf123',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, False)
        self.mock_driver.get_infrastructure_task.assert_called_once_with('inf123', 'req123', {'name': 'TestDl'})

    def test_job_handler_marks_job_as_finished_if_inf_not_found_error_thrown(self):
        self.mock_driver.get_infrastructure_task.side_effect = InfrastructureNotFoundError('Not Found')
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'InfrastructureTaskMonitoring',
            'infrastructure_id': 'inf123',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, True)
        self.mock_driver.get_infrastructure_task.assert_called_once_with('inf123', 'req123', {'name': 'TestDl'})

    def test_job_handler_marks_job_as_finished_if_request_not_found_error_thrown(self):
        self.mock_driver.get_infrastructure_task.side_effect = InfrastructureRequestNotFoundError('Not Found')
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'InfrastructureTaskMonitoring',
            'infrastructure_id': 'inf123',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, True)
        self.mock_driver.get_infrastructure_task.assert_called_once_with('inf123', 'req123', {'name': 'TestDl'})

    def test_job_handler_does_not_mark_job_as_finished_if_in_progress(self):
        self.mock_driver.get_infrastructure_task.return_value = InfrastructureTask('inf123', 'req123', 'IN_PROGRESS', None)
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'InfrastructureTaskMonitoring',
            'infrastructure_id': 'inf123',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, False)
        self.mock_driver.get_infrastructure_task.assert_called_once_with('inf123', 'req123', {'name': 'TestDl'})

    def test_job_handler_sends_message_when_task_complete(self):
        self.mock_driver.get_infrastructure_task.return_value = InfrastructureTask('inf123', 'req123', 'COMPLETE', None)
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'InfrastructureTaskMonitoring',
            'infrastructure_id': 'inf123',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, True)
        self.mock_driver.get_infrastructure_task.assert_called_once_with('inf123', 'req123', {'name': 'TestDl'})
        self.mock_inf_messaging_service.send_infrastructure_task.assert_called_once_with(self.mock_driver.get_infrastructure_task.return_value)
        
    def test_job_handler_sends_message_when_task_failed(self):
        self.mock_driver.get_infrastructure_task.return_value = InfrastructureTask('inf123', 'req123', 'FAILED', None)
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'InfrastructureTaskMonitoring',
            'infrastructure_id': 'inf123',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, True)
        self.mock_driver.get_infrastructure_task.assert_called_once_with('inf123', 'req123', {'name': 'TestDl'})
        self.mock_inf_messaging_service.send_infrastructure_task.assert_called_once_with(self.mock_driver.get_infrastructure_task.return_value)
         
    def test_job_handler_ignores_job_without_infrastructure_id(self):
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'InfrastructureTaskMonitoring',
            'request_id': 'req123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, True)
        self.mock_driver.get_infrastructure_task.assert_not_called()
        self.mock_inf_messaging_service.send_infrastructure_task.assert_not_called()

    def test_job_handler_ignores_job_without_request_id(self):
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'InfrastructureTaskMonitoring',
            'infrastructure_id': 'inf123',
            'deployment_location': {'name': 'TestDl'}
        })
        self.assertEqual(job_finished, True)
        self.mock_driver.get_infrastructure_task.assert_not_called()
        self.mock_inf_messaging_service.send_infrastructure_task.assert_not_called()

    def test_job_handler_ignores_job_without_deployment_location_id(self):
        monitoring_service = InfrastructureTaskMonitoringService(job_queue_service=self.mock_job_queue, inf_messaging_service=self.mock_inf_messaging_service, driver=self.mock_driver)
        job_finished = monitoring_service.job_handler({
            'job_type': 'InfrastructureTaskMonitoring',
            'infrastructure_id': 'inf123',
            'request_id': 'req123'
        })
        self.assertEqual(job_finished, True)
        self.mock_driver.get_infrastructure_task.assert_not_called()
        self.mock_inf_messaging_service.send_infrastructure_task.assert_not_called()

class TestInfrastructureMessagingService(unittest.TestCase):

    def setUp(self):
        self.mock_postal_service = MagicMock()
        self.mock_topics_configuration = MagicMock(infrastructure_task_events = TopicConfigProperties(name='task_events_topic'))

    def test_init_without_postal_service_throws_error(self):
        with self.assertRaises(ValueError) as context:
            InfrastructureMessagingService(topics_configuration=self.mock_topics_configuration)
        self.assertEqual(str(context.exception), 'postal_service argument not provided')

    def test_init_without_topics_configuration_throws_error(self):
        with self.assertRaises(ValueError) as context:
            InfrastructureMessagingService(postal_service=self.mock_postal_service)
        self.assertEqual(str(context.exception), 'topics_configuration argument not provided')

    def test_init_without_infrastructure_task_events_topic_throws_error(self):
        mock_topics_configuration = MagicMock(infrastructure_task_events = None)
        with self.assertRaises(ValueError) as context:
            InfrastructureMessagingService(postal_service=self.mock_postal_service, topics_configuration=mock_topics_configuration)
        self.assertEqual(str(context.exception), 'infrastructure_task_events topic must be set')

    def test_init_without_infrastructure_task_events_topic_name_throws_error(self):
        mock_topics_configuration = MagicMock(infrastructure_task_events = TopicConfigProperties())
        with self.assertRaises(ValueError) as context:
            InfrastructureMessagingService(postal_service=self.mock_postal_service, topics_configuration=mock_topics_configuration)
        self.assertEqual(str(context.exception), 'infrastructure_task_events topic name must be set')

    def test_send_infrastructure_task_sends_message(self):
        messaging_service = InfrastructureMessagingService(postal_service=self.mock_postal_service, topics_configuration=self.mock_topics_configuration)
        messaging_service.send_infrastructure_task(InfrastructureTask('inf123', 'req123', 'FAILED', FailureDetails(FAILURE_CODE_INFRASTRUCTURE_ERROR, 'because it was meant to fail')))
        self.mock_postal_service.post.assert_called_once()
        args, kwargs = self.mock_postal_service.post.call_args
        self.assertEqual(kwargs, {})
        self.assertEqual(len(args), 1)
        envelope_arg = args[0]
        self.assertIsInstance(envelope_arg, Envelope)
        self.assertEqual(envelope_arg.address, self.mock_topics_configuration.infrastructure_task_events.name)
        self.assertIsInstance(envelope_arg.message, Message)
        self.assertEqual(envelope_arg.message.content, b'{"requestId": "req123", "infrastructureId": "inf123", "status": "FAILED", "failureDetails": {"failureCode": "INFRASTRUCTURE_ERROR", "description": "because it was meant to fail"}}')
    
    def test_send_infrastrucutre_task_throws_error_when_task_is_none(self):
        messaging_service = InfrastructureMessagingService(postal_service=self.mock_postal_service, topics_configuration=self.mock_topics_configuration)
        with self.assertRaises(ValueError) as context:
            messaging_service.send_infrastructure_task(None)
        self.assertEqual(str(context.exception), 'infrastructure_task must be set to send an infrastructure task event')
