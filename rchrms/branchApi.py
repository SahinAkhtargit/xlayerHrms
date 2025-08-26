import frappe
from frappe import _

def authenticate():
    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.response["status"]=False
        frappe.response['message']="Not Authorise"
        frappe.response["data"]=None
        # frappe.throw(_("Authentication required"), frappe.AuthenticationError)

  

# @frappe.whitelist(allow_guest=False)
@frappe.whitelist()
def get_branch(branch=None, status=None):
    # authenticate()
    try:
        if branch:
            Branch = frappe.get_doc("Branch", branch)
            frappe.response["status"]=True
            frappe.response['message']="Branch fetched"
            frappe.response["data"]=Branch.as_dict()
            return
        elif status:
            branches = frappe.get_all("Branch", filters={"custom_status": status}, fields=["name", "branch", "custom_status"])
            frappe.response["status"]=True
            frappe.response['message']="All branches fetched"
            frappe.response["data"]=branches
            return
        else:
            branches = frappe.get_all("Branch", fields=["name", "branch", "custom_status"])
            frappe.response["status"]=True
            frappe.response['message']="All branches fetched"
            frappe.response["data"]=branches
            return
    except frappe.DoesNotExistError:
        frappe.response["status"]=False
        frappe.response['message']="Branch not found"
        frappe.response["data"]=None
        return
    except Exception as e:
        frappe.response["status"]=False
        frappe.response['message']=str(e)
        frappe.response["data"]=None
        return

@frappe.whitelist(allow_guest=False)
def create_branch(branch, custom_status="Active"):
    authenticate()
    try:
        exists = frappe.db.exists("Branch", {"branch": branch})
        if exists:
            frappe.response["status"] = False
            frappe.response["message"] = "Branch already exists"
            frappe.response["data"] = None
            return

        doc = frappe.get_doc({
            "doctype": "Branch",
            "branch": branch,
            "custom_status": custom_status
        })
        doc.insert(ignore_permissions=True)
        frappe.response["status"]=True
        frappe.response["message"]="Branch created"
        frappe.response['data']=doc.as_dict()
        return
    except Exception as e:
        frappe.response["status"]=False
        frappe.response["message"]=str(e)
        frappe.response["data"]=None
        return


@frappe.whitelist(allow_guest=False)
def update_branch(name, branch=None, custom_status=None):
    authenticate()
    try:
        if not frappe.db.exists("Branch", name):
            frappe.response["status"] = False
            frappe.response["message"] = "Branch not found"
            frappe.response["data"] = None
            return

        doc = frappe.get_doc("Branch", name)
        if branch and branch != doc.branch:
            if frappe.db.exists("Branch", {"branch": branch}):
                frappe.response["status"] = False
                frappe.response["message"] = f"Branch '{branch}' already exists"
                frappe.response["data"] = None
                return
            doc.branch = branch

        if custom_status:
            doc.custom_status = custom_status

        doc.save(ignore_permissions=True)

        frappe.response["status"] = True
        frappe.response["message"] = "Branch updated"
        frappe.response["data"] = doc.as_dict()

    except Exception as e:
        frappe.response["status"] = False
        frappe.response["message"] = str(e)
        frappe.response["data"] = None


@frappe.whitelist(allow_guest=False)
def delete_branch(name):
    authenticate()
    try:
        if not frappe.db.exists("Branch", name):
            frappe.response["status"] = False
            frappe.response["message"] = "Branch not found"
            frappe.response["data"] = None
            return

        frappe.delete_doc("Branch", name, ignore_permissions=True)
        frappe.response["status"] = True
        frappe.response["message"] = "Branch deleted"
        frappe.response["data"] = {"name": name}
    except Exception as e:
        frappe.response["status"] = False
        frappe.response["message"] = str(e)
        frappe.response["data"] = None


