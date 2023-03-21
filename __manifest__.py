{
    'name': 'Biotime Server Integration',
    'version': '15.0.0.0',
    'category': 'Generic Modules/Human Resources',
    'author': 'Ryad Abderrahim',
    'depends': ['hr', 'hr_attendance', 'resource', 'hr_work_entry', 'hr_work_entry_contract'],
    'data': [
        'security/ir.model.access.csv',

        'wizards/get_transactions.xml',

        'views/biotime_server.xml',
        'views/biotime_transaction.xml',
        'views/biotime_shift.xml',
        'views/hr_employee.xml',
        'views/hr_attendance.xml',
        'views/menus.xml',
    ],
    'images': ['static/description/banner.gif'],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
