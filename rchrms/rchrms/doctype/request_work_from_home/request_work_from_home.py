# Copyright (c) 2025, Sahin Akhtar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, date, timedelta
from frappe.utils import getdate
#class RequestWorkFromHome(Document):
#	pass
class RequestWorkFromHome(Document):
    def autoname(self):
        if self.employee and self.from_date:
            self.name = f"{self.employee}-{self.from_date}"
        else:
            frappe.throw("Both Employee and Dates are required for naming")
    def before_save(self):
        if self.from_date and self.to_date:
            from_date = getdate(self.from_date)
            to_date = getdate(self.to_date)

            diff = (to_date - from_date).days + 1

            if diff > 0:
                self.days = diff
            else:
                self.days = 0
                frappe.throw("To Date must be after From Date")


    def validate(self):
        if self.docstatus != 0:
            return

    
        role_profile = frappe.db.get_value("User", frappe.session.user, "role_profile_name")
        if not role_profile or role_profile != "xLayer Employee":
            return


        today = date.today()

        from_date = (
            datetime.strptime(self.from_date, "%Y-%m-%d").date()
            if isinstance(self.from_date, str)
            else self.from_date
        )
        to_date = (
            datetime.strptime(self.to_date, "%Y-%m-%d").date()
            if isinstance(self.to_date, str)
            else self.to_date
        )

        if from_date == today and to_date == today:
            hr_config = frappe.get_single("HR Config")
            last_allowed_time_str = hr_config.wfh_last_request_time

            if not last_allowed_time_str:
                frappe.throw("Work from home cutoff time is not set in HR Config.")

            allowed_time = datetime.strptime(last_allowed_time_str, "%H:%M:%S").time()
            now_time = datetime.now().time()

            if now_time > allowed_time:
                frappe.throw("You can't request work from home after the shift has started.")

    
        elif from_date == today and to_date == today + timedelta(days=1):
            pass

        else:
            pass

