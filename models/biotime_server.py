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
        self.ensure_one()
        biotime = Biotime(self.server_ip, self.server_port)
        try:
            conn = biotime.test_connection()
            if conn:
                auth_res = biotime.get_jwt_token(self.username, self.password)
                if auth_res:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': "Succés",
                            'message': "Connexion établie avec succès.",
                            'sticky': False,
                        }
                    }
                else:
                    raise UserError(
                        _("Impossible de récupérer le token JWT, vérifiez les paramètres de connexion et la disponibilité du serveur Biotime."))
            else:
                raise UserError(_('Problème lors du test de connexion.'))
        except error:
            raise UserError(_('Problème lors du test de connexion.', error))

    def download_employees(self):
        employee_obj = self.env['hr.employee']

        for server in self:
            biotime = Biotime(server.server_ip, server.server_port)
            server_conn = biotime.test_connection()
            if server_conn:
                token_res = biotime.get_jwt_token(
                    server.username, server.password)
                if token_res:
                    # Biotime attendances
                    biotime_employees = biotime.get_employees()
                    if isinstance(biotime_employees, list):
                        for biotime_employee in biotime_employees:
                            # Check if employee exists in Odoo
                            if not employee_obj.search([('biotime_code', '=', biotime_employee['emp_code'])]):
                                employee_obj.create({
                                    "name": biotime_employee['first_name'] if biotime_employee['first_name'] else "" + " " + biotime_employee['last_name'] if biotime_employee['last_name'] else "",
                                    "biotime_code": biotime_employee['emp_code'],
                                })
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': "Success",
                                'message': "Employees downloaded into Odoo Successfully.",
                                'sticky': False,
                            }
                        }
                    else:
                        raise UserError(
                            _("Unable to retrieve biotime employees, please check the login parameters and network connections."))
                else:
                    raise UserError(
                        _("Unable to retrieve jwt token, please check the login parameters and network connections."))
            else:
                raise UserError(
                    _('Unable to connect, please check the parameters and network connections.'))

    def upload_employees(self):
        employee_obj = self.env['hr.employee']

        for server in self:
            biotime = Biotime(server.server_ip, server.server_port)
            server_conn = biotime.test_connection()
            if server_conn:
                token_res = biotime.get_jwt_token(
                    server.username, server.password)
                if token_res:
                    # Biotime attendances
                    biotime_employees = biotime.get_employees()
                    if isinstance(biotime_employees, list):
                        biotime_employees = [biotime_employee['emp_code']
                                             for biotime_employee in biotime_employees]
                        odoo_employees = employee_obj.search(
                            [('biotime_code', 'not in', biotime_employees)])

                        for employee in odoo_employees:
                            name_split = employee.name.split(" ")
                            biotime.create_employee({
                                'emp_code': employee.biotime_code,
                                'first_name': name_split[0],
                                'last_name': name_split[-1]
                            })
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': "Success",
                                'message': "Employees uploaded into Biotime Successfully.",
                                'sticky': False,
                            }
                        }
                    else:
                        raise UserError(
                            _("Unable to upload Odoo employees, please check the login parameters and network connections."))
                else:
                    raise UserError(
                        _("Unable to retrieve jwt token, please check the login parameters and network connections."))
            else:
                raise UserError(
                    _('Unable to connect, please check the parameters and network connections.'))

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
                    transaction_list = biotime.get_transactions()
                    if isinstance(transaction_list, list):
                        for transaction in transaction_list:
                            punch_time = fields.Datetime.to_datetime(
                                transaction['punch_time'])
                            # Local timezone datetime obj
                            local_dt = local_tz.localize(
                                punch_time, is_dst=None)
                            # utc timezone datetime obj
                            utc_dt = local_dt.astimezone(pytz.utc)
                            utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                            punch_time = datetime.strptime(
                                utc_dt, "%Y-%m-%d %H:%M:%S")
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

                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': "Succés",
                                'message': "Transactions téléchargées avec succès depuis Biotime.",
                                'sticky': False,
                            }
                        }
                    else:
                        raise UserError(
                            _("Unable to retrieve biotime attendances, please check the login parameters and network connections."))
                else:
                    raise UserError(
                        _("Unable to retrieve jwt token, please check the login parameters and network connections."))
            else:
                raise UserError(
                    _('Unable to connect, please check the parameters and network connections.'))

    def _get_punch_type(self, punch_time: datetime, shift_lines):
        """
        _get_punch_type is used to 'as you might guess' determine the punch type ('Check-in or Check-out') based on the employee's shift.

        :param punch_time: Datetime object of the punch time. (Should be in UTC timezone format - Odoo already stores datetimes object in UTC timezone)
        :param shift_lines: List of biotime.shift.line records that are linked to the employee shift. (Check biotime.shift model)
        """
        local_tz = pytz.timezone(self.env.user.partner_id.tz or 'GMT')
        utc_dt = pytz.utc.localize(punch_time, is_dst=None)
        local_dt = utc_dt.astimezone(local_tz)
        punch_time = local_dt.strftime("%Y-%m-%d %H:%M:%S")
        punch_time = datetime.strptime(
            punch_time, "%Y-%m-%d %H:%M:%S")

        transaction_day = str(datetime.weekday(punch_time))
        transaction_hour = punch_time.time()
        transaction_float = transaction_hour.hour + transaction_hour.minute / 60.0

        check_in_line = shift_lines.filtered(lambda shift_line: transaction_day == shift_line.day_in and (shift_line.check_in_start <=
                                                                                                          transaction_float <= shift_line.check_in_end))
        check_out_line = shift_lines.filtered(lambda shift_line: transaction_day == shift_line.day_out and (shift_line.check_out_start <=
                                                                                                            transaction_float <= shift_line.check_out_end))

        if (check_in_line and check_out_line) or len(check_in_line) > 1 or len(check_out_line) > 1:
            raise UserError(
                _("Une transaction '{}' ne doit appartenir qu'à une seule fiche de temps.".format(str(punch_time))))
        elif check_in_line:
            return 'I', check_in_line
        elif check_out_line:
            return 'O', check_out_line
        else:
            return False, False

    def _handle_attendance_creation(self, employee, punch_type: str, punch_time: datetime, shift_line):
        """
        _handle_attendance_creation is used to handle the attendance creation and verification

        :param employee: hr.employee object.
        :param punch_type: Punch type. (First return statement of _get_punch_type func)
        :param punch_time: Datetime object of the punch time. (Should be in UTC timezone format - Odoo already stores datetimes object in UTC timezone)
        :param shift_line: Shift line that the punch time belongs to. (Second return statement of _get_punch_type func)
        """
        attendance_obj = self.env['hr.attendance']
        local_tz = pytz.timezone(self.env.user.partner_id.tz or 'GMT')

        if punch_type and punch_time and shift_line:
            if punch_type == 'I':
                if attendance_obj.search([('employee_id', '=', employee.id), ('check_in', '=', punch_time)]):
                    return

                check_in_start_dt = datetime(punch_time.year, punch_time.month, punch_time.day, int(
                    shift_line.check_in_start), int((shift_line.check_in_start - int(shift_line.check_in_start)) * 60))
                check_in_end_dt = datetime(punch_time.year, punch_time.month, punch_time.day, int(
                    shift_line.check_in_end), int((shift_line.check_in_end - int(shift_line.check_in_end)) * 60))

                # Converting from local timezone to utc (Converting because of the shift_line hours that represent local tz hours)
                check_in_start_dt = local_tz.localize(
                    check_in_start_dt, is_dst=None).astimezone(pytz.utc)
                check_in_end_dt = local_tz.localize(
                    check_in_end_dt, is_dst=None).astimezone(pytz.utc)

                employee_att = attendance_obj.search(
                    [('employee_id', '=', employee.id), ('check_in', '>=', check_in_start_dt), ('check_in', '<=', check_in_end_dt)])

                if not employee_att:
                    attendance_obj.create({
                        'employee_id': employee.id,
                        'check_in': punch_time
                    })
                elif employee_att and punch_time < employee_att[-1].check_in:
                    employee_att[-1].update({
                        'check_in': punch_time
                    })

            elif punch_type == 'O':
                if attendance_obj.search([('employee_id', '=', employee.id), ('check_out', '=', punch_time)]):
                    return

                check_in_start_dt = datetime(punch_time.year, punch_time.month, punch_time.day, int(
                    shift_line.check_in_start), int((shift_line.check_in_start - int(shift_line.check_in_start)) * 60))
                check_in_end_dt = datetime(punch_time.year, punch_time.month, punch_time.day, int(
                    shift_line.check_in_end), int((shift_line.check_in_end - int(shift_line.check_in_end)) * 60))

                check_in_start_dt = local_tz.localize(
                    check_in_start_dt, is_dst=None).astimezone(pytz.utc)
                check_in_end_dt = local_tz.localize(
                    check_in_end_dt, is_dst=None).astimezone(pytz.utc)

                employee_att = attendance_obj.search(
                    [('employee_id', '=', employee.id), ('check_in', '>=', check_in_start_dt), ('check_in', '<=', check_in_end_dt)], order="id asc")

                if employee_att and not employee_att[-1].check_out:
                    employee_att[-1].write({
                        'check_out': punch_time
                    })
                elif employee_att and punch_time > employee_att[-1].check_out:
                    employee_att[-1].write({
                        'check_out': punch_time
                    })
                elif not employee_att:
                    attendance_obj.create({
                        'employee_id': employee.id,
                        'check_out': punch_time
                    })

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
                # Get punch type and corresponding shift line
                punch_type, shift_line = self._get_punch_type(transaction.punch_time,
                                                              transaction.employee_id.biotime_shift_id.biotime_shift_lines)
                # Generate attendance
                self._handle_attendance_creation(
                    transaction.employee_id, punch_type, transaction.punch_time, shift_line)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Succés",
                'message': "Présences synchronisées avec Biotime.",
                'sticky': False,
            }
        }

    # TODO: Recheck algo and verify code
    def download_generate_attendances(self):
        _logger.info(
            "++++++++++++ Cron job 'download_generate_attendances' executed ++++++++++++++++++++++")

        employee_obj = self.env['hr.employee']
        biotime_transaction_obj = self.env['biotime.transaction']
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
                    transaction_list = biotime.get_transactions()
                    if isinstance(transaction_list, list):
                        for transaction in transaction_list:
                            # Creating transaction record
                            punch_time = fields.Datetime.to_datetime(
                                transaction['punch_time'])
                            # Local timezone datetime obj
                            local_dt = local_tz.localize(
                                punch_time, is_dst=None)
                            # utc timezone datetime obj
                            utc_dt = local_dt.astimezone(pytz.utc)
                            # utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                            punch_time = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                            # punch_time = datetime.strptime(
                            #     utc_dt, "%Y-%m-%d %H:%M:%S")
                            # punch_time = fields.Datetime.to_string(punch_time)
                            punch_time = fields.Datetime.to_datetime(
                                punch_time)

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

                            # Get the puch type and the according shift line
                            punch_type, shift_line = self._get_punch_type(punch_time,
                                                                          employee.biotime_shift_id.biotime_shift_lines)

                            # Generate attendance
                            self._handle_attendance_creation(
                                employee, punch_type, punch_time, shift_line)

                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': "Success",
                                'message': "Transactions downloaded and attendances generated with success.",
                                'sticky': False,
                            }
                        }
                    else:
                        raise UserError(
                            _("Error while retrieving biotime attendances."))
                else:
                    raise UserError(
                        _("Unable to retrieve jwt token, please check the login parameters and network connections."))

            else:
                raise UserError(
                    _('Unable to connect, please check the parameters and network connections.'))

    @api.model
    def cron_download(self):
        servers = self.env['biotime.serve'].search([])
        for server in servers:
            server.download_transactions()
            server.generate_attendances()
