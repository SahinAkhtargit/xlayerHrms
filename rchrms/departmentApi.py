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
def get_department(name=None, status=None):
    authenticate()
    try:
        if name:
            department = frappe.get_doc("Department", name)
            frappe.response["status"] = True
            frappe.response['message'] = "Department fetched"
            frappe.response["data"] = department.as_dict()
        elif status:
            departments = frappe.get_all(
                "Department",
                filters={"custom_status": status, "department_name": ("!=", "All Departments")},
                fields=["name", "department_name", "parent_department", "custom_status"]
            )
            frappe.response["status"] = True
            frappe.response['message'] = "Departments fetched"
            frappe.response["data"] = departments
        else:
            departments = frappe.get_all(
                "Department",
                filters={"department_name": ("!=", "All Departments")},
                fields=["name", "department_name", "parent_department", "custom_status"]
            )
            frappe.response["status"] = True
            frappe.response['message'] = "All departments fetched"
            frappe.response["data"] = departments
    except frappe.DoesNotExistError:
        frappe.response["status"] = False
        frappe.response['message'] = "Department not found"
        frappe.response["data"] = None
    except Exception as e:
        frappe.response["status"] = False
        frappe.response['message'] = str(e)
        frappe.response["data"] = None


@frappe.whitelist(allow_guest=False)
def create_department(department_name, parent_department=None, custom_status="Active"):
    authenticate()
    try:
        exists = frappe.db.exists("Department", {"department_name": department_name})
        if exists:
            frappe.response["status"] = False
            frappe.response["message"] = "Department already exists"
            frappe.response["data"] = None
            return

        doc = frappe.get_doc({
            "doctype": "Department",
            "department_name": department_name,
            "parent_department": parent_department,
            "custom_status": custom_status
        })
        doc.insert(ignore_permissions=True)
        frappe.response["status"] = True
        frappe.response["message"] = "Department created"
        frappe.response["data"] = doc.as_dict()
    except Exception as e:
        frappe.response["status"] = False
        frappe.response["message"] = str(e)
        frappe.response["data"] = None


@frappe.whitelist(allow_guest=False)
def update_department(name, department_name=None, parent_department=None, custom_status=None):
    authenticate()
    try:
        if not frappe.db.exists("Department", name):
            frappe.response["status"] = False
            frappe.response["message"] = "Department not found"
            frappe.response["data"] = None
            return

        doc = frappe.get_doc("Department", name)

        if department_name and department_name != doc.department_name:
            if frappe.db.exists("Department", {"department_name": department_name}):
                frappe.response["status"] = False
                frappe.response["message"] = f"Department '{department_name}' already exists"
                frappe.response["data"] = None
                return
            doc.department_name = department_name

        if parent_department is not None:
            doc.parent_department = parent_department

        if custom_status:
            doc.custom_status = custom_status

        doc.save(ignore_permissions=True)

        frappe.response["status"] = True
        frappe.response["message"] = "Department updated"
        frappe.response["data"] = doc.as_dict()

    except Exception as e:
        frappe.response["status"] = False
        frappe.response["message"] = str(e)
        frappe.response["data"] = None


@frappe.whitelist(allow_guest=False)
def delete_department(name):
    authenticate()
    try:
        if not frappe.db.exists("Department", name):
            frappe.response["status"] = False
            frappe.response["message"] = "Department not found"
            frappe.response["data"] = None
            return

        frappe.delete_doc("Department", name, ignore_permissions=True)
        frappe.response["status"] = True
        frappe.response["message"] = "Department deleted"
        frappe.response["data"] = {"name": name}
    except Exception as e:
        frappe.response["status"] = False
        frappe.response["message"] = str(e)
        frappe.response["data"] = None
