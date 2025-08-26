import frappe
from frappe.utils import getdate, date_diff, add_days

def update_attendance_on_leave_submit(doc, method):
    from_date = getdate(doc.from_date)
    to_date = getdate(doc.to_date)
    half_day = doc.half_day
    half_day_date = getdate(doc.half_day_date) if doc.half_day else None

    for i in range(date_diff(to_date, from_date) + 1):
        d = add_days(from_date, i)

        att_name = frappe.db.get_value(
            "Attendance",
            {"employee": doc.employee, "attendance_date": d}
        )
        if att_name:
            # update existing
            att_doc = frappe.get_doc("Attendance", att_name)
        else:
            # create new
            att_doc = frappe.new_doc("Attendance")
            att_doc.employee = doc.employee
            att_doc.attendance_date = d

        # status assignment
        if half_day and d == half_day_date:
            att_doc.status = "Half Day"
        else:
            att_doc.status = "On Leave"

        att_doc.leave_application = doc.name
        att_doc.leave_type = doc.leave_type
        att_doc.save(ignore_permissions=True)


import hrms
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication

class CustomLeaveApplication(LeaveApplication):
    def validate_attendance(self):
        """
        Skip ERPNext's default duplicate attendance check.
        We allow Leave to co-exist with already marked Attendance.
        Actual overwrite will happen in on_submit.
        """
        return

