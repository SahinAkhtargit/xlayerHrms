# Copyright (c) 2025, Sahin Akhtar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class OffDayWorkEntry(Document):
    def autoname(self):
        prefix = self.employee_id or "UNKNOWN"
        series_key = f"{prefix}-"
        self.name = frappe.model.naming.make_autoname(f"{series_key}.###", self)

    def before_submit(self):
        if not self.total_work_day or self.total_work_day <= 0:
            frappe.throw("Total Work Day must be greater than 0 before submission.")
        employee = self.employee_id
        total_work_day = self.total_work_day

        redeem_rows = [row for row in self.work_day_details if row.redeem]
        non_redeem_rows = [row for row in self.work_day_details if not row.redeem]

        if not redeem_rows:
            frappe.throw("At least one row must have the redeem checkbox checked before submission.")

        if non_redeem_rows:
            new_doc = frappe.new_doc("Off Day Work Entry")
            new_doc.employee_id = self.employee_id
            new_doc.total_work_day = 0 
            for row in non_redeem_rows:
                new_doc.append("work_day_details", {
                    "attendance_req_link": row.attendance_req_link,
                    "from_date": row.from_date,
                    "to_date": row.to_date,
                    "total_working_hours": row.total_working_hours,
                    "redeem": 0
                })
            new_doc.insert(ignore_permissions=True)
            frappe.msgprint(f"New Off Day Work Entry created for non-redeem rows: {new_doc.name}")

            self.work_day_details = redeem_rows

        if employee and total_work_day is not None:
            tracker = frappe.get_value(
                "Weekend Tracker",
                {"employee": employee},
                ["name", "total_work_day"],
                as_dict=True
            )

            if tracker:
                tracker_doc = frappe.get_doc("Weekend Tracker", tracker.name)
                tracker_doc.total_work_day = (tracker_doc.total_work_day or 0) + total_work_day
                tracker_doc.save(ignore_permissions=True)
                frappe.msgprint(f"Weekend Tracker for {employee} updated to {total_work_day} work days.")
            else:
                new_tracker = frappe.new_doc("Weekend Tracker")
                new_tracker.employee = employee
                new_tracker.total_work_day = total_work_day
                new_tracker.insert(ignore_permissions=True)
                frappe.msgprint(f"Weekend Tracker created for {employee} with {total_work_day} work days.")
        else:
            frappe.throw("Employee ID or Total Work Day is missing in Off Day Work Entry.")
