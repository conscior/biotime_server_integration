
from odoo import models, fields

class BiotimeTransactionWizard(models.TransientModel):
    _name = 'biotime.transaction.wizard'

    date_start = fields.Datetime('Date start', required=True)
    date_end = fields.Datetime('Date end', required=True)

    def get_transactions(self):
        for rec in self:
            date_start = rec.date_start
            date_end = rec.date_end
            for server in self.env['biotime.server'].search([]):
                server.download_transactions(
                    req_params={'start_time': f'{date_start}', 'end_time': f'{date_end}'})
