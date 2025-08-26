import frappe
from frappe.utils import now_datetime, getdate
from datetime import datetime, timedelta, time
def auto_checkout():
    
    today = getdate(now_datetime())
    start_of_day = datetime.combine(today, datetime.min.time())
 
    checkins = frappe.get_all(
        "Employee Checkin",
        filters={
            "log_type": "IN",
             "time": [">=", start_of_day]
        },
        fields=["name", "employee", "time"]
    )
 
    for checkin in checkins:
        out_exists = frappe.db.exists("Employee Checkin", {
            "employee": checkin.employee,
            "log_type": "OUT",
            "time": [">", checkin.time]
        })
 
        if not out_exists:
            frappe.get_doc({
                "doctype": "Employee Checkin",
                "employee": checkin.employee,
                "log_type": "OUT",
                "time": now_datetime(),
                "skip_auto_attendance": 0
            }).insert(ignore_permissions=True)
            frappe.db.commit()

def autoAttendance():
    shift_type_name = "Day Shift"
    day_before_yesterday = (datetime.today() - timedelta(days=2)).date()
    today_10pm = datetime.combine(datetime.today(), time(22, 0))
 
    try:
        shift = frappe.get_doc("Shift Type", shift_type_name)
        shift.process_attendance_after = day_before_yesterday
        shift.last_sync_of_checkin = today_10pm
        shift.save()
        frappe.db.commit()
        #frappe.log_error("Shift updated successfully. Triggering attendance marking...")
 
        shift.process_auto_attendance()
 
        #frappe.log_error("Attendance marking triggered successfully.")
 
    except Exception as e:
        frappe.log_error("Error in update_shift_sync_dates: " + str(e))
