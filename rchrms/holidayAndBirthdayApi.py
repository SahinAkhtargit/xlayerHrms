import frappe

from frappe.utils import strip_html

@frappe.whitelist(allow_guest=True)
def get_holiday_list(employee=None, holiday_list_name=None):
    try:
        if employee and not holiday_list_name:
            employee_doc = frappe.get_doc("Employee", employee)
            holiday_list_name = employee_doc.holiday_list

        if not holiday_list_name:
            frappe.response["status"] = False
            frappe.response["message"] = "No holiday list found for given input"
            frappe.response["data"] = None
            return

        # Get only holidays where weekly_off is 0
        holidays = frappe.get_all(
            "Holiday",
            filters={"parent": holiday_list_name, "weekly_off": 0},
            fields=["holiday_date", "description", "weekly_off"],
            order_by="holiday_date asc"
        )

        # Strip HTML from descriptions
        for holiday in holidays:
            holiday["description"] = strip_html(holiday["description"] or "")

        frappe.response["status"] = True
        frappe.response["message"] = f"Holidays (excluding weekly offs) fetched for: {holiday_list_name}"
        frappe.response["summary"] = {
            "total_non_weekly_off_holidays": len(holidays)
        }
        frappe.response["data"] = holidays

    except Exception as e:
        frappe.response["status"] = False
        frappe.response["message"] = str(e)
        frappe.response["data"] = None


@frappe.whitelist(allow_guest=False)
def get_employee_birthdays():
    try:
        employees = frappe.get_all(
            "Employee",
            fields=["employee_name", "date_of_birth", "branch", "designation"],
            filters={"status": "Active"},  # Optional: filter only active employees
            order_by="date_of_birth asc"
        )
        frappe.response["status"]=True
        frappe.response["message"]="Employee birthdays fetched successfully"
        frappe.response["total_birthdays"]=len(employees)
        frappe.response["data"]=employees

    except Exception as e:
        frappe.response["status"]=False
        frappe.response["message"]=str(e)
        frappe.response["data"]=None

