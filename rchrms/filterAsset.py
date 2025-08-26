#import frappe
#from frappe.utils import cint
#from frappe import _

#@frappe.whitelist()
#def get_filtered_assets():
 #   user = frappe.session.user

    # Check if user is HR Manager
  #  roles = frappe.get_roles(user)
   ## if "HR Manager" in roles:
       # Return all asset names
    #    assets = frappe.get_all("Asset", pluck="name")
   # else:
        # Get Employee record linked to this user
    #    employee = frappe.get_value("Employee", {"user_id": user}, "name")
     #   if not employee:
      #      return []

       # # Return assets assigned to this employee
       # assets = frappe.get_all("Asset", filters={"custodian": employee}, pluck="name")

   # return assets

