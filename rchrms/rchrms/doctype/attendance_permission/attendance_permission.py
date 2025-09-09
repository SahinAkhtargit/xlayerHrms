# Copyright (c) 2025, Sahin Akhtar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AttendancePermission(Document):
    def on_submit(self):
        # Fetch HR Config (singleton doctype)
        hr_config = frappe.get_single("HR Config")

        # Ensure HR Config has the child table field
        if not hasattr(hr_config, "attendance_config_data"):
            frappe.throw("HR Config is missing the 'attendance_config_data' child table.")

        # Loop through child table in Attendance Permission
        for row in self.attendance_config_data:
            hr_config.append("attendance_config_data", {
                "doc_link": row.doc_link
            })

        # Save changes
        hr_config.save(ignore_permissions=True)
        frappe.db.commit()
