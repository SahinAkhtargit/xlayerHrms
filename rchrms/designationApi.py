import frappe
from frappe import _

def authenticate():
    """Check if current session is authenticated."""
    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.response["status"] = False
        frappe.response['message'] = "Not Authorised"
        frappe.response["data"] = None
        frappe.throw(_("Authentication required"), frappe.AuthenticationError)


@frappe.whitelist(allow_guest=False)
def get_designation(name=None, status=None):
    authenticate()
    try:
        if name:
            designation = frappe.get_doc("Designation", name)
            frappe.response["status"] = True
            frappe.response['message'] = "Designation fetched"
            frappe.response["data"] = designation.as_dict()
        elif status:
            designations = frappe.get_all("Designation", filters={"custom_status": status}, fields=["name", "designation_name", "custom_status"])
            frappe.response["status"] = True
            frappe.response['message'] = "All designations fetched"
            frappe.response["data"] = designations
        else:
            designations = frappe.get_all("Designation", fields=["name", "designation_name", "custom_status"])
            frappe.response["status"] = True
            frappe.response['message'] = "All designations fetched"
            frappe.response["data"] = designations
    except frappe.DoesNotExistError:
        frappe.response["status"] = False
        frappe.response['message'] = "Designation not found"
        frappe.response["data"] = None
    except Exception as e:
        frappe.response["status"] = False
        frappe.response['message'] = str(e)
        frappe.response["data"] = None


@frappe.whitelist(allow_guest=False)
def create_designation(designation_name, custom_status="Active", description=None):
    authenticate()
    try:
        exists = frappe.db.exists("Designation", {"designation_name": designation_name})
        if exists:
            frappe.response["status"] = False
            frappe.response["message"] = "Designation already exists"
            frappe.response["data"] = None
            return

        doc = frappe.get_doc({
            "doctype": "Designation",
            "designation_name": designation_name,
            "custom_status": custom_status,
            "description": description
        })
        doc.insert(ignore_permissions=True)
        frappe.response["status"] = True
        frappe.response["message"] = "Designation created"
        frappe.response["data"] = doc.as_dict()
    except Exception as e:
        frappe.response["status"] = False
        frappe.response["message"] = str(e)
        frappe.response["data"] = None


@frappe.whitelist(allow_guest=False)
def update_designation(name, designation_name=None, custom_status=None, description=None):
    authenticate()
    try:
        if not frappe.db.exists("Designation", name):
            frappe.response["status"] = False
            frappe.response["message"] = "Designation not found"
            frappe.response["data"] = None
            return

        doc = frappe.get_doc("Designation", name)

        if designation_name and designation_name != doc.designation_name:
            if frappe.db.exists("Designation", {"designation_name": designation_name}):
                frappe.response["status"] = False
                frappe.response["message"] = f"Designation '{designation_name}' already exists"
                frappe.response["data"] = None
                return
            doc.designation_name = designation_name

        if custom_status:
            doc.custom_status = custom_status

        if description is not None:
            doc.description = description

        doc.save(ignore_permissions=True)

        frappe.response["status"] = True
        frappe.response["message"] = "Designation updated"
        frappe.response["data"] = doc.as_dict()

    except Exception as e:
        frappe.response["status"] = False
        frappe.response["message"] = str(e)
        frappe.response["data"] = None


@frappe.whitelist(allow_guest=False)
def delete_designation(name):
    authenticate()
    try:
        if not frappe.db.exists("Designation", name):
            frappe.response["status"] = False
            frappe.response["message"] = "Designation not found"
            frappe.response["data"] = None
            return

        frappe.delete_doc("Designation", name, ignore_permissions=True)
        frappe.response["status"] = True
        frappe.response["message"] = "Designation deleted"
        frappe.response["data"] = {"name": name}
    except Exception as e:
        frappe.response["status"] = False
        frappe.response["message"] = str(e)
        frappe.response["data"] = None
