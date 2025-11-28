# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestOutlookIntegration(TransactionCase):
    
    def setUp(self):
        super(TestOutlookIntegration, self).setUp()
        
        self.OutlookConfig = self.env['outlook.config']
        self.HrEmployee = self.env['hr.employee']
        self.FrontdeskVisitor = self.env['frontdesk.visitor']
        self.ResPartner = self.env['res.partner']
        self.FrontdeskStation = self.env['frontdesk.frontdesk']
        
        self.outlook_config = self.OutlookConfig.create({
            'name': 'Test Config',
            'client_id': 'test-client-id',
            'client_secret': 'test-client-secret',
            'tenant_id': 'test-tenant-id',
            'redirect_uri': 'http://localhost:8000/auth',
            'active': True,
        })
        
        self.station = self.FrontdeskStation.search([], limit=1)
        if not self.station:
            self.station = self.FrontdeskStation.create({
                'name': 'Test Station',
            })
        
        self.employee = self.HrEmployee.create({
            'name': 'Test Employee',
            'outlook_calendar_sync': True,
            'outlook_access_token': 'test-access-token',
            'outlook_refresh_token': 'test-refresh-token',
            'outlook_token_expiry': datetime.now() + timedelta(hours=1),
        })
        
        self.visitor_partner = self.ResPartner.create({
            'name': 'Test Visitor',
            'email': 'visitor@test.com',
            'phone': '1234567890',
            'is_visitor': True,
            'is_company': False,
        })
    
    def test_employee_outlook_setup(self):
        employee = self.HrEmployee.create({
            'name': 'New Employee',
        })
        
        self.assertFalse(employee.outlook_calendar_sync)
        self.assertFalse(employee.outlook_access_token)
        
        employee.outlook_calendar_sync = True
        self.assertTrue(employee.outlook_calendar_sync)
    
    def test_visitor_outlook_fields(self):
        visitor = self.FrontdeskVisitor.create({
            'partner_id': self.visitor_partner.id,
            'host_ids': [(6, 0, [self.employee.id])],
            'date': datetime.now().date(),
            'planned_date': datetime.now().date(),
            'planned_time': 10.0,
            'planned_duration': 60,
            'station_id': self.station.id,
            'state': 'planned',
        })
        
        self.assertFalse(visitor.outlook_event_id)
        self.assertEqual(visitor.outlook_sync_status, 'not_synced')
    
    def test_prepare_outlook_event_data(self):
        visitor = self.FrontdeskVisitor.create({
            'partner_id': self.visitor_partner.id,
            'host_ids': [(6, 0, [self.employee.id])],
            'date': datetime.now().date(),
            'planned_date': datetime.now().date(),
            'planned_time': 10.0,
            'planned_duration': 60,
            'station_id': self.station.id,
            'visit_purpose': 'Business Meeting',
        })
        
        event_data = visitor._prepare_outlook_event_data()
        
        self.assertIn('subject', event_data)
        self.assertIn('body', event_data)
        self.assertIn('start', event_data)
        self.assertIn('end', event_data)
        self.assertIn('attendees', event_data)
        
        self.assertIn(self.visitor_partner.name, event_data['subject'])
        self.assertEqual(event_data['body']['contentType'], 'HTML')
    
    def test_prepare_outlook_event_data_without_planned_time(self):
        visitor = self.FrontdeskVisitor.create({
            'partner_id': self.visitor_partner.id,
            'host_ids': [(6, 0, [self.employee.id])],
            'date': datetime.now().date(),
            'station_id': self.station.id,
        })
        
        event_data = visitor._prepare_outlook_event_data()
        
        self.assertIn('subject', event_data)
        self.assertIn('start', event_data)
        self.assertIn('end', event_data)
    
    @patch('requests.post')
    def test_create_outlook_event_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': 'event-123'}
        mock_post.return_value = mock_response
        
        visitor = self.FrontdeskVisitor.create({
            'partner_id': self.visitor_partner.id,
            'host_ids': [(6, 0, [self.employee.id])],
            'date': datetime.now().date(),
            'planned_date': datetime.now().date(),
            'planned_time': 10.0,
            'planned_duration': 60,
            'station_id': self.station.id,
            'state': 'planned',
        })
        
        visitor.create_outlook_event()
        
        self.assertTrue(mock_post.called)
        self.assertEqual(visitor.outlook_event_id, 'event-123')
        self.assertEqual(visitor.outlook_sync_status, 'synced')
    
    @patch('requests.post')
    def test_create_outlook_event_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_post.return_value = mock_response
        
        visitor = self.FrontdeskVisitor.create({
            'partner_id': self.visitor_partner.id,
            'host_ids': [(6, 0, [self.employee.id])],
            'date': datetime.now().date(),
            'planned_date': datetime.now().date(),
            'planned_time': 10.0,
            'planned_duration': 60,
            'station_id': self.station.id,
            'state': 'planned',
        })
        
        visitor.create_outlook_event()
        
        self.assertTrue(mock_post.called)
        self.assertEqual(visitor.outlook_sync_status, 'sync_failed')
    
    @patch('requests.patch')
    def test_update_outlook_event(self, mock_patch):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response
        
        visitor = self.FrontdeskVisitor.create({
            'partner_id': self.visitor_partner.id,
            'host_ids': [(6, 0, [self.employee.id])],
            'date': datetime.now().date(),
            'planned_date': datetime.now().date(),
            'planned_time': 10.0,
            'planned_duration': 60,
            'station_id': self.station.id,
            'outlook_event_id': 'event-123',
            'outlook_sync_status': 'synced',
        })
        
        visitor.update_outlook_event()
        
        self.assertTrue(mock_patch.called)
    
    @patch('requests.delete')
    def test_cancel_outlook_event(self, mock_delete):
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response
        
        visitor = self.FrontdeskVisitor.create({
            'partner_id': self.visitor_partner.id,
            'host_ids': [(6, 0, [self.employee.id])],
            'date': datetime.now().date(),
            'planned_date': datetime.now().date(),
            'planned_time': 10.0,
            'planned_duration': 60,
            'station_id': self.station.id,
            'outlook_event_id': 'event-123',
            'outlook_sync_status': 'synced',
        })
        
        visitor.cancel_outlook_event()
        
        self.assertTrue(mock_delete.called)
        self.assertFalse(visitor.outlook_event_id)
        self.assertEqual(visitor.outlook_sync_status, 'cancelled')
    
    def test_token_refresh_mechanism(self):
        employee = self.HrEmployee.create({
            'name': 'Token Test Employee',
            'outlook_calendar_sync': True,
            'outlook_access_token': 'expired-token',
            'outlook_refresh_token': 'refresh-token',
            'outlook_token_expiry': datetime.now() - timedelta(hours=1),
        })
        
        self.assertTrue(employee.outlook_token_expiry <= datetime.now())
    
    def test_visitor_without_host(self):
        visitor = self.FrontdeskVisitor.create({
            'partner_id': self.visitor_partner.id,
            'date': datetime.now().date(),
            'planned_date': datetime.now().date(),
            'station_id': self.station.id,
        })
        
        visitor.create_outlook_event()
        
        self.assertEqual(visitor.outlook_sync_status, 'not_synced')
