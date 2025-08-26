# Copyright (c) 2025, Sahin Akhtar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate

#class WeekendTracker(Document):
#	pass

class WeekendTracker(Document):
    def before_save(self):
        previous = self.get_doc_before_save()
        previous_total = previous.total_work_day if previous else 0
        current_total = self.total_work_day or 0

        if current_total == previous_total:
            return

        today = getdate(nowdate())
        current_year = today.year
        from_date = getdate(f"{current_year}-01-01")
        to_date = getdate(f"{current_year}-12-31")

        employee = self.employee
        leave_type = "Extra Earned Leave"

        existing = frappe.get_all(
            "Leave Allocation",
            filters={
                "employee": employee,
                "leave_type": leave_type,
                "from_date": from_date,
                "to_date": to_date,
                "docstatus": 1
            },
            fields=["name"]
        )

        if existing:
            allocation_name = existing[0].name

            frappe.db.sql("""
                UPDATE `tabLeave Allocation`
                SET new_leaves_allocated = %s,
                    total_leaves_allocated = %s
                WHERE name = %s
            """, (current_total, current_total, allocation_name))

            frappe.db.sql("""
                UPDATE `tabLeave Ledger Entry`
                SET leaves = %s
                WHERE employee = %s
                  AND leave_type = %s
            """, (current_total, employee, leave_type))

            frappe.msgprint(f"Updated Leave Allocation (SQL) for {employee}")
        else:
            new_alloc = frappe.get_doc({
                "doctype": "Leave Allocation",
                "employee": employee,
                "leave_type": leave_type,
                "from_date": from_date,
                "to_date": to_date,
                "new_leaves_allocated": current_total
            })
            new_alloc.insert()
            new_alloc.submit()
            frappe.msgprint(f"Created Leave Allocation for {employee}")

















































































































