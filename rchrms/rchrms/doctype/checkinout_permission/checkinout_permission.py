# Copyright (c) 2025, Sahin Akhtar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CheckInOutPermission(Document):
    def before_save(self):
        hr_config = frappe.get_single("HR Config")

        # Try to find existing child row
        existing_row = next((d for d in hr_config.checkinout_permission_config if d.doc_link == self.name), None)

        if existing_row:
            # Update values if exists
            existing_row.late_early_validation = self.late_early_validation
            existing_row.image_required = self.image_required
        else:
            # Otherwise append new row
            hr_config.append("checkinout_permission_config", {
                "doc_link": self.name,
                "late_early_validation": self.late_early_validation,
                "image_required": self.image_required
            })

        hr_config.save(ignore_permissions=True)
        frappe.db.commit()
