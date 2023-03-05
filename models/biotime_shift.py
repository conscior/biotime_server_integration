from odoo import api, fields, models
from odoo.exceptions import UserError


class BiotimeShift(models.Model):
    _name = 'biotime.shift'

    name = fields.Char('Nom du Shift')
    biotime_shift_lines = fields.One2many(
        'biotime.shift.line', 'biotime_shift_id', string='Timetables')

    _sql_constraints = [
        ('biotime_shift_name_unique',
         'unique(name)',
         'Veuillez choisir un nom unique pour chaque shift !')
    ]

class BiotimeShiftLine(models.Model):
    _name = 'biotime.shift.line'

    @api.constrains('check_in_start', 'check_in_end', 'check_out_start', 'check_out_end')
    def _check_hour_format(self):
        for rec in self:
            if rec.check_in_start >= 24 or rec.check_in_start < 0:
                raise UserError('Format horaire erroné.')
            if rec.check_in_end >= 24 or rec.check_in_end < 0:
                raise UserError('Format horaire erroné.')
            if rec.check_out_start >= 24 or rec.check_out_start < 0:
                raise UserError('Format horaire erroné.')
            if rec.check_out_end >= 24 or rec.check_out_end < 0:
                raise UserError('Format horaire erroné.')
            if rec.check_out_end <= rec.check_out_start or rec.check_in_end <= rec.check_in_start:
                raise UserError(
                    'Check fin ne peut pas être inferieur a Check début.')

    biotime_shift_id = fields.Many2one('biotime.shift', string='Biotime Shift')
    day_in = fields.Selection([
        ('6', 'Dimanche'),
        ('0', 'Lundi'),
        ('1', 'Mardi'),
        ('2', 'Mercredi'),
        ('3', 'Jeudi'),
        ('4', 'Vendredi'),
        ('5', 'Samedi')
    ], string='Jours de la semaine In', required=True)
    work_from = fields.Float('Travail à partir de')
    check_in_start = fields.Float('Check-in Début')
    check_in_end = fields.Float('Check-in Fin')
    day_out = fields.Selection([
        ('6', 'Dimanche'),
        ('0', 'Lundi'),
        ('1', 'Mardi'),
        ('2', 'Mercredi'),
        ('3', 'Jeudi'),
        ('4', 'Vendredi'),
        ('5', 'Samedi')
    ], string='Jours de la semaine Out', required=True)
    work_to = fields.Float("Travail jusqu'à")
    check_out_start = fields.Float('Check-out Début')
    check_out_end = fields.Float('Check-out Fin')
