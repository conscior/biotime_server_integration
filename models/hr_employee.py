from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    biotime_code = fields.Char(string="Biotime Code")
    biotime_shift_id = fields.Many2one('biotime.shift', string='Biotime Shift')

    _sql_constraints = [
        ('biotime_code_unique',
         'unique(biotime_code)',
         'Veuillez choisir code biotime unique!')
    ]
