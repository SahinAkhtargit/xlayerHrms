
import frappe
import base64
import uuid
from frappe import _
from frappe.utils.file_manager import save_file

def authenticate():
    if not frappe.session.user or frappe.session.user == "Guest":
        frappe.response["status"] = False
        frappe.response['message'] = "Not Authorised"
        frappe.response["data"] = None
        return False
    return True

@frappe.whitelist(allow_guest=False)
def upload_user_image(user_email, image_base64, filename):
    if not authenticate():
        return

    try:
        if not frappe.db.exists("User", user_email):
            frappe.response["status"] = False
            frappe.response["message"] = "User not found"
            frappe.response["data"] = None
            return

        user = frappe.get_doc("User", user_email)
        if user.user_image:
            try:
                old_file_doc = frappe.get_doc("File", {"file_url": user.user_image})
                old_file_doc.delete()
            except frappe.DoesNotExistError:
                pass
        image_bytes = base64.b64decode(image_base64)
        file_doc = save_file(
            fname=f"{uuid.uuid4()}_{filename}",
            content=image_bytes,
            dt="User",
            dn=user_email,
            folder="Home",
            is_private=1
        )
        user.user_image = file_doc.file_url
        user.save(ignore_permissions=True)

        frappe.response["status"] = True
        frappe.response["message"] = "User image uploaded successfully"
        frappe.response["data"] = {
            "file_url": file_doc.file_url
        }

    except Exception as e:
        frappe.response["status"] = False
        frappe.response["message"] = str(e)
        frappe.response["data"] = None


