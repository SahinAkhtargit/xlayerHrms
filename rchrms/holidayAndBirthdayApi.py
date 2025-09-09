import frappe
from datetime import datetime, timedelta
from frappe.utils import strip_html


@frappe.whitelist(allow_guest=False) 
def get_holiday_list():
    try:
        if frappe.request.method != "GET":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use GET request."
            frappe.local.response["data"] = None
            return
        user = frappe.session.user
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")

        if not employee:
            frappe.response["status"] = False
            frappe.response["message"] = f"No Employee linked with this user: {user}"
            frappe.response["data"] = None
            return

        holiday_list_name = frappe.db.get_value("Employee", employee, "holiday_list")
        if not holiday_list_name:
            frappe.response["status"] = False
            frappe.response["message"] = "No holiday list found for this employee"
            frappe.response["data"] = None
            return

        holidays = frappe.get_all(
            "Holiday",
            filters={"parent": holiday_list_name, "weekly_off": 0},
            fields=["holiday_date", "description", "weekly_off"],
            order_by="holiday_date asc"
        )

        for holiday in holidays:
            holiday["description"] = strip_html(holiday["description"] or "")

        frappe.response["status"] = True
        frappe.response["message"] = f"Holidays (excluding weekly offs) fetched for: {holiday_list_name}"
        frappe.response["summary"] = {"total_non_weekly_off_holidays": len(holidays)}
        frappe.response["data"] = holidays

    except Exception as e:
        frappe.response["status"] = False
        frappe.response["message"] = str(e)
        frappe.response["data"] = None


@frappe.whitelist(allow_guest=False)
def get_employee_birthdays():
    try:
        if frappe.request.method != "GET":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use GET request."
            frappe.local.response["data"] = None
            return
        today = datetime.today().date()
        next_year = today + timedelta(days=365)

        employees = frappe.get_all(
            "Employee",
            fields=["employee_name", "date_of_birth", "branch", "designation"],
            filters={"status": "Active"},
        )

        upcoming_birthdays = []
        for emp in employees:
            if emp.date_of_birth:

                dob_this_year = emp.date_of_birth.replace(year=today.year)

                if dob_this_year < today:
                    dob_this_year = emp.date_of_birth.replace(year=today.year + 1)

                if today <= dob_this_year <= next_year:
                    upcoming_birthdays.append({
                        "employee_name": emp.employee_name,
                        "date_of_birth": emp.date_of_birth,  
                        "branch": emp.branch,
                        "designation": emp.designation,
                        "next_birthday": dob_this_year  
                    })

   
        upcoming_birthdays.sort(key=lambda x: x["next_birthday"])

        frappe.response["status"] = True
        frappe.response["message"] = "Employee birthdays fetched successfully"
        frappe.response["total_birthdays"] = len(upcoming_birthdays)
        frappe.response["data"] = upcoming_birthdays

    except Exception as e:
        frappe.response["status"] = False
        frappe.response["message"] = str(e)
        frappe.response["data"] = None
                                       
