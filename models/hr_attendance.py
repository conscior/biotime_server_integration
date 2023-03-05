import pytz

from odoo import api, fields, models
from odoo import _


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    # Remove check in/out checks
    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        pass

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        pass

    @api.depends('check_in', 'check_out', 'employee_id')
    def _compute_undertime(self):
        for rec in self:
            employee_shift_lines = rec.employee_id.biotime_shift_id.biotime_shift_lines
            if rec.check_in and employee_shift_lines:
                local_check_in = pytz.utc.localize(rec.check_in, is_dst=None).astimezone(
                    pytz.timezone(self.env.user.partner_id.tz or 'GMT'))
                try:
                    shift_line = employee_shift_lines.filtered(lambda shift_line: int(
                        shift_line.day_in) == local_check_in.weekday())[0]
                    hour_from = shift_line.work_from
                except:
                    hour_from = 0

                if hour_from:
                    check_in_hour = local_check_in.hour + \
                        (local_check_in.minute / 60)
                    rec.undertime = (
                        check_in_hour - hour_from) if check_in_hour > hour_from else 0
                else:
                    rec.undertime = 0
            else:
                rec.undertime = 0

    @api.depends('check_in', 'check_out', 'employee_id')
    def _compute_overtime(self):
        for rec in self:
            employee_shift_lines = rec.employee_id.biotime_shift_id.biotime_shift_lines
            if rec.check_out:
                local_check_out = pytz.utc.localize(rec.check_out, is_dst=None).astimezone(
                    pytz.timezone(self.env.user.partner_id.tz or 'GMT'))
                try:
                    shift_line = employee_shift_lines.filtered(lambda shift_line: int(
                        shift_line.day_out) == local_check_out.weekday())[-1]
                    hour_to = shift_line.work_to
                except:
                    hour_to = 0
                if hour_to:
                    check_out_hour = local_check_out.hour + \
                        (local_check_out.minute / 60)
                    rec.overtime = (check_out_hour -
                                    hour_to) if check_out_hour > hour_to else 0
                else:
                    rec.overtime = 0
            else:
                rec.overtime = 0

    check_in = fields.Datetime(
        string="Check In", default=False, required=False)  # Overide
    undertime = fields.Float(string="Retard", compute="_compute_undertime")
    overtime = fields.Float(string='Heure(s) supplémentaire',
                            compute="_compute_overtime")
    
