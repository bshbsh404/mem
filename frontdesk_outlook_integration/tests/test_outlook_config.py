# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestOutlookConfig(TransactionCase):
    
    def setUp(self):
        super(TestOutlookConfig, self).setUp()
        self.OutlookConfig = self.env['outlook.config']
        
    def test_create_outlook_config(self):
        config = self.OutlookConfig.create({
            'name': 'Test Outlook Config',
            'client_id': 'test-client-id',
            'client_secret': 'test-client-secret',
            'tenant_id': 'test-tenant-id',
            'redirect_uri': 'http://localhost:8000/auth',
            'active': True,
        })
        
        self.assertTrue(config.id)
        self.assertEqual(config.name, 'Test Outlook Config')
        self.assertEqual(config.client_id, 'test-client-id')
        self.assertTrue(config.active)
    
    def test_get_auth_url(self):
        config = self.OutlookConfig.create({
            'name': 'Test Outlook Config',
            'client_id': 'test-client-id',
            'client_secret': 'test-client-secret',
            'tenant_id': 'test-tenant-id',
            'redirect_uri': 'http://localhost:8000/auth',
            'active': True,
        })
        
        auth_url = config.get_auth_url()
        self.assertTrue(auth_url)
        self.assertIn('login.microsoftonline.com', auth_url)
        self.assertIn(config.tenant_id, auth_url)
    
    def test_multiple_configs_one_active(self):
        config1 = self.OutlookConfig.create({
            'name': 'Config 1',
            'client_id': 'client-1',
            'client_secret': 'secret-1',
            'tenant_id': 'tenant-1',
            'active': True,
        })
        
        config2 = self.OutlookConfig.create({
            'name': 'Config 2',
            'client_id': 'client-2',
            'client_secret': 'secret-2',
            'tenant_id': 'tenant-2',
            'active': False,
        })
        
        active_configs = self.OutlookConfig.search([('active', '=', True)])
        self.assertGreaterEqual(len(active_configs), 1)
        self.assertIn(config1, active_configs)
