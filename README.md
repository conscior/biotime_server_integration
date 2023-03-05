# Biotime Server Integration
This Odoo module allow for the integration of a Biotime server.

## Documentation
* biotime.py : Basic python class that allows the creation of a Biotime object. This object will be initialised with the server IP adress, Port, timeout and the JWT token.
* biotime_server.py : Odoo model used to store the server and auth informations.
* biotime_shift.py : Odoo model used to store the employee's shifts.
* biotime_transaction.py : Odoo model used to store the existing transaction in the Biotime server.
* hr_attendance.py : Removing hr_attendance constraints and added overtime and undertime fields.
* hr_employee.py : Added biotime code and biotime shift fields.
 
## Credits
Developer: Ryad Abderrahim

## Contacts
* Mail : abderr.ryad@gmail.com
