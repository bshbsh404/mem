# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged, TransactionCase
import json


@tagged('post_install', '-at_install')
class TestVisitorAPI(TransactionCase):

    def setUp(self):
        super().setUp()
        
        # Create test employee
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
            'employee_number': '12345',
        })
        
        # Create test visitor
        self.partner = self.env['res.partner'].create({
            'name': 'Test Visitor',
            'is_visitor': True,
            'is_company': False,
        })
        
        self.visitor = self.env['frontdesk.visitor'].create({
            'partner_id': self.partner.id,
            'employee_id': self.employee.id,
            'date': '2025-09-10',
            'state': 'planned',
            'purpose': 'Business Meeting',
        })

    def test_get_pending_approvals(self):
        """Test getting pending approvals for an employee"""
        approvals = self.employee.get_pending_approvals()
        
        self.assertEqual(len(approvals), 1)
        self.assertEqual(approvals[0]['visitor_name'], 'Test Visitor')
        self.assertEqual(approvals[0]['purpose'], 'Business Meeting')
        self.assertTrue(approvals[0]['approval_id'].startswith('A'))

    def test_approve_visitor(self):
        """Test approving a visitor request"""
        approval_id = f"A{self.visitor.id}"
        result = self.employee.approve_reject_visitor(approval_id, 'approve')
        
        self.assertEqual(result['status'], 'Y')
        self.assertIn('approved', result['validation_message'])

    def test_reject_visitor(self):
        """Test rejecting a visitor request"""
        approval_id = f"A{self.visitor.id}"
        result = self.employee.approve_reject_visitor(approval_id, 'reject')
        
        self.assertEqual(result['status'], 'Y')
        self.assertIn('rejected', result['validation_message'])
        
        # Refresh visitor and check state
        self.visitor.refresh()
        self.assertEqual(self.visitor.state, 'canceled')