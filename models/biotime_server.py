from .biotime import Biotime
from os import error
import logging

from datetime import datetime
import pytz

from odoo import api, fields, models
from odoo import _
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)


# try:
#     from zk import ZK
# except ImportError:
#     _logger.error("Please Install pyzk library.")

_logger = logging.getLogger(__name__)


class BiotimeServer(models.Model):
    _name = 'biotime.server'

    name = fields.Char(string="Nom du serveur",
                       required=True, default="Serveur x")
    server_ip = fields.Char(string='Addresse IP', required=True)
    server_port = fields.Char(string='Port', required=True)
    username = fields.Char(string="Nom d'utilisateur", required=True)
    password = fields.Char(string="Mot de passe", required=True)

    _sql_constraints = [
        ('biotime_server_name_unique',
         'unique(name)',
         'Veuillez choisir un nom unique pour chaque serveur !')
    ]

    def test_connection(self):
        biotime = Biotime(self.server_ip, self.server_port)
        try:
            conn = biotime.test_connection()
            if conn:
                # Change userError to maybe a widget
                raise UserError(_('Connection success'))
            else:
                raise UserError(_('Connection error'))
        except error:
            raise UserError(_('User error', error))

    def try_auth(self):
        biotime = Biotime(self.server_ip, self.server_port)
        try:
            res = biotime.get_jwt_token(self.username, self.password)
            if res:
                # Change userError to maybe a widget
                raise UserError(_('Username and password valid'))
            else:
                raise UserError(
                    _("Unable to retrieve jwt token, please check the login parameters and network connections."))
        except error:
            raise UserError(_('User error', error))

    def download_transactions(self):
        _logger.info(
            "++++++++++++ Cron job 'download_transactions' executed ++++++++++++++++++++++")

        biotime_transaction_obj = self.env['biotime.transaction']
        employee_obj = self.env['hr.employee']
        local_tz = pytz.timezone(self.env.user.partner_id.tz or 'GMT')

        biotime_transaction_obj.search([]).unlink()

        for server in self:
            biotime = Biotime(server.server_ip, server.server_port)
            server_conn = biotime.test_connection()
            if server_conn:
                token_res = biotime.get_jwt_token(
                    server.username, server.password)
                if token_res:
                    # Biotime attendances
                    transaction_list = biotime.get_attendances()
                    if isinstance(transaction_list, list):
                        for transaction in transaction_list:
                            punch_time = fields.Datetime.to_datetime(
                                transaction['punch_time'])
                            # Local timezone datetime obj
                            local_dt = local_tz.localize(
                                punch_time, is_dst=None)
                            utc_dt = local_dt.astimezone(pytz.utc)
                            utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                            punch_time = datetime.strptime(
                                utc_dt, "%Y-%m-%d %H:%M:%S")
                            punch_time_utc = punch_time  # UTC
                            punch_time = fields.Datetime.to_string(punch_time)

                            employee = employee_obj.search(
                                [('biotime_code', '=', transaction['emp_code'])])

                            biotime_transaction_obj.create({
                                "server_id": server.id,
                                "punch_state": str(transaction['punch_state']),
                                "verify_type": str(transaction['verify_type']),
                                "punch_time": punch_time,
                                "employee_id": employee.id if employee else False,
                                "employee_code": transaction['emp_code']
                            })
                    else:
                        raise UserError(
                            _("Unable to retrieve biotime attendances, please check the login parameters and network connections."))
                else:
                    raise UserError(
                        _("Unable to retrieve jwt token, please check the login parameters and network connections."))
            else:
                raise UserError(
                    _('Unable to connect, please check the parameters and network connections.'))

    def _get_punch_type(self, shift_lines, punch_time):
        local_tz = pytz.timezone(self.env.user.partner_id.tz or 'GMT')
        utc_dt = pytz.utc.localize(punch_time, is_dst=None)
        local_dt = utc_dt.astimezone(local_tz)
        punch_time = local_dt.strftime("%Y-%m-%d %H:%M:%S")
        punch_time = datetime.strptime(
            punch_time, "%Y-%m-%d %H:%M:%S")

        transaction_day = str(datetime.weekday(punch_time))
        transaction_hour = punch_time.time()
        transaction_float = transaction_hour.hour + transaction_hour.minute / 60.0

        check_in_line = shift_lines.filtered(lambda shift_line: transaction_day == shift_line.day_in and (shift_line.check_in_start <
                                                                                                          transaction_float < shift_line.check_in_end))
        check_out_line = shift_lines.filtered(lambda shift_line: transaction_day == shift_line.day_out and (shift_line.check_out_start <
                                                                                                            transaction_float < shift_line.check_out_end))

        if (check_in_line and check_out_line) or len(check_in_line) > 1 or len(check_out_line) > 1:
            raise UserError(
                _("Une transaction '{}' ne doit appartenir qu'à une seule fiche de temps.".format(str(punch_time))))
        elif check_in_line:
            return 'I', check_in_line
        elif check_out_line:
            return 'O', check_out_line
        else:
            return False, False

    def generate_attendances(self):
        _logger.info(
            "++++++++++++ Cron job 'generate_attendances' executed ++++++++++++++++++++++")

        biotime_transaction_obj = self.env['biotime.transaction']
        attendance_obj = self.env['hr.attendance']
        local_tz = pytz.timezone(self.env.user.partner_id.tz or 'GMT')

        if not len(biotime_transaction_obj.search([])):
            raise UserError(_("Aucune transaction existante."))

        for transaction in biotime_transaction_obj.search([], order="punch_time asc"):
            if transaction.employee_id and transaction.employee_id.biotime_shift_id:
                check_type, shift_line = self._get_punch_type(
                    transaction.employee_id.biotime_shift_id.biotime_shift_lines, transaction.punch_time)
                if check_type == 'I':
                    check_in_start_dt = datetime(transaction.punch_time.year, transaction.punch_time.month, transaction.punch_time.day, int(
                        shift_line.check_in_start), int((shift_line.check_in_start - int(shift_line.check_in_start)) * 60))
                    check_in_end_dt = datetime(transaction.punch_time.year, transaction.punch_time.month, transaction.punch_time.day, int(
                        shift_line.check_in_end), int((shift_line.check_in_end - int(shift_line.check_in_end)) * 60))

                    check_in_start_dt = local_tz.localize(
                        check_in_start_dt, is_dst=None).astimezone(pytz.utc)
                    check_in_end_dt = local_tz.localize(
                        check_in_end_dt, is_dst=None).astimezone(pytz.utc)

                    employee_att_check_in = attendance_obj.search(
                        [('employee_id', '=', transaction.employee_id.id), ('check_in', '>=', check_in_start_dt), ('check_in', '<=', check_in_end_dt)])
                    if not employee_att_check_in:
                        attendance_obj.create({
                            'employee_id': transaction.employee_id.id,
                            'check_in': transaction.punch_time
                        })
                    else:
                        if transaction.punch_time < employee_att_check_in[-1].check_in:
                            employee_att_check_in[-1].update({
                                'check_in': transaction.punch_time
                            })
                elif check_type == 'O':
                    check_in_start_dt = datetime(transaction.punch_time.year, transaction.punch_time.month, transaction.punch_time.day, int(
                        shift_line.check_in_start), int((shift_line.check_in_start - int(shift_line.check_in_start)) * 60))
                    check_in_end_dt = datetime(transaction.punch_time.year, transaction.punch_time.month, transaction.punch_time.day, int(
                        shift_line.check_in_end), int((shift_line.check_in_end - int(shift_line.check_in_end)) * 60))

                    check_in_start_dt = local_tz.localize(
                        check_in_start_dt, is_dst=None).astimezone(pytz.utc)
                    check_in_end_dt = local_tz.localize(
                        check_in_end_dt, is_dst=None).astimezone(pytz.utc)

                    employee_att = attendance_obj.search(
                        [('employee_id', '=', transaction.employee_id.id), ('check_in', '>=', check_in_start_dt), ('check_in', '<=', check_in_end_dt)], order="id asc")

                    if employee_att and not employee_att[-1].check_out:
                        employee_att[-1].write({
                            'check_out': transaction.punch_time
                        })
                    else:
                        attendance_obj.create({
                            'employee_id': transaction.employee_id.id,
                            'check_out': transaction.punch_time
                        })

    @ api.model
    def cron_download(self):
        servers = self.env['biotime.serve'].search([])
        for server in servers:
            server.download_transactions()
            server.generate_attendances()
