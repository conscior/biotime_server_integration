from odoo import fields, models
from odoo import _


class BiotimeTransaction(models.Model):
    _name = 'biotime.transaction'
    _order = 'punch_time'

    server_id = fields.Many2one('biotime.server', string="Server name")
    employee_id = fields.Many2one('hr.employee', string='Employé(e)')
    employee_code = fields.Char(string="Employee code")
    punch_state = fields.Selection([
        ('I', 'Check in'),
        ('O', 'Check out'),
        ('0', 'Check in'),
        ('1', 'Check out'),
        ('2', 'Break out'),
        ('3', 'Break in'),
        ('4', 'Overtime in'),
        ('5', 'Overtime out'),
        ('255', 'Other')
    ], string='Punch state')
    verify_type = fields.Selection([
        ('0', 'Password'),
        ('1', 'Fingerprint'),
        ('2', 'Employee ID'),
        ('3', 'Password'),
        ('4', 'Card'),
        ('5', 'Fingerprint/Password'),
        ('6', 'Fingerprint/Card'),
        ('7', 'Password/Card'),
        ('8', 'Employee ID & Fingerprint'),
        ('9', 'Fingerprint & Password'),
        ('10', 'Fingerprint & Card'),
        ('11', 'Password & Card'),
        ('12', 'Fingerprint & Password & Card'),
        ('13', 'Employee ID & Fingerprint & Password'),
        ('14', 'Fingerprint & Card & Employee ID'),
        ('15', 'Face'),
        ('16', 'Face & Fingerprint'),
        ('17', 'Face & Password'),
        ('18', 'Face & Card'),
        ('19', 'Face & Fingerprint & Card'),
        ('20', 'Face & Fingerprint & Password'),
        ('21', 'Finger Vein'),
        ('22', 'Finger Vein & Password'),
        ('23', 'Finger Vein & Card'),
        ('24', 'Finger Vein & Password & Card'),
        ('25', 'Palm'),
        ('26', 'Palm & Card'),
        ('27', 'Palm & Face'),
        ('28', 'Palm & Fingerprint'),
        ('29', 'Palm & Fingerprint & Card'),
        ('101', 'GPS'),
        ('102', 'AI Camera'),
        ('200', 'Other'),
    ], string='Verify type')
    punch_time = fields.Datetime(string='Punching Time')
