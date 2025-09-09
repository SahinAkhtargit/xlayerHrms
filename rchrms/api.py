import frappe
from frappe import auth
from frappe import _


def custom_error_handler(e):
    # Default Frappe JSON response for API calls
    frappe.local.response.http_status_code = 200  # force 200 even on auth error

    frappe.local.response.update({
        "status": False,
        "message": str(e),
        "data": None
    })

    return frappe.local.response

@frappe.whitelist( allow_guest=True )
def login(usr, pwd):
    try:
        if frappe.request.method != "POST":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use POST request."
            frappe.local.response["data"] = None
            return
        login_manager = frappe.auth.LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)
        login_manager.post_login()

        frappe.get_doc({
            "doctype": "Activity Log",
            "subject": "Logged In",
            "user": frappe.session.user,
            "operation": "Login",
            "activity_type": "Login",
            "reference_doctype": "User",
            "reference_name": frappe.session.user
        }).insert(ignore_permissions=True)

    except frappe.exceptions.AuthenticationError:
        frappe.clear_messages()
        frappe.response["status"] = False
        frappe.response["message"] = "Authentication Error!"
        return

    api_key, api_secret = generate_keys(frappe.session.user)
    user = frappe.get_doc('User', frappe.session.user)
    
    frappe.response["status"] = True
    frappe.response["message"] = "Authentication Success"
    frappe.response["data"] = {
        "s_id": frappe.session.sid,
        "api_key": api_key,
        "api_secret": api_secret,
        #"Authorization":f"Token {api_key}:{api_secret}",
        "user": {
            "username": user.username,
            "email": user.email,
            "full_name": frappe.utils.get_fullname(user.full_name),
            "role": user.role_profile_name
        },
    }
    frappe.response.pop("home_page", None)
    frappe.response.pop("full_name", None)
def generate_keys(user):
    user_details = frappe.get_doc('User', user)

    if not user_details.api_key:
        user_details.api_key = frappe.generate_hash(length=15)

    api_secret = frappe.generate_hash(length=15)
    user_details.api_secret = api_secret
    user_details.save(ignore_permissions=True)

    return user_details.api_key, api_secret 


@frappe.whitelist( allow_guest=True )
def logout():
    if frappe.request.method != "POST":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use POST request."
            frappe.local.response["data"] = None
            return
    user = frappe.session.user

    if user == "Guest":
        frappe.response["status"] = False
        frappe.response["message"] = "No active session found"
        return

    frappe.get_doc({
        "doctype": "Activity Log",
        "subject": "Logged Out",
        "user": user,
        "operation": "Logout",
        "activity_type": "Logout",
        "reference_doctype": "User",
        "reference_name": user
    }).insert(ignore_permissions=True)

    frappe.local.login_manager.logout()
    frappe.db.commit()
    frappe.response["status"] = True
    frappe.response["message"] = "Successfully logged out"
    frappe.response.pop("home_page", None)
    frappe.response.pop("full_name", None)

@frappe.whitelist( allow_guest=False )
def get_User(username=None, status=None):
    # authenticate()
    try:
        if frappe.request.method != "GET":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use GET request."
            frappe.local.response["data"] = None
            return
        if username:
            Branch = frappe.get_doc("User", username)
            frappe.response["status"]=True
            frappe.response['message']="User fetched"
            frappe.response["data"]=username.as_dict()
            return
        else:
            users = frappe.get_all("User", fields=["username","full_name", "role_profile_name", "language","phone","mobile_no","email","enabled","time_zone","user_image"])
            frappe.response["status"]=True
            frappe.response['message']="All Users fetched"
            frappe.response["data"]=users
            return
    except frappe.DoesNotExistError:
        frappe.response["status"]=False
        frappe.response['message']="User not found"
        frappe.response["data"]=None
        return
    except Exception as e:
        frappe.response["status"]=False
        frappe.response['message']=str(e)
        frappe.response["data"]=None
        return

@frappe.whitelist(allow_guest=False)
def update_user(email, **kwargs):
    # authenticate()  # Uncomment if needed
    try:
        if frappe.request.method != "PUT":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use PUT request."
            frappe.local.response["data"] = None
            return
        if not frappe.db.exists("User", email):
            frappe.response["status"] = False
            frappe.response["message"] = "User not found"
            frappe.response["data"] = None
            return

        doc = frappe.get_doc("User", email)

        # List of fields that are safe to update via API
        allowed_fields = [
            "full_name", "phone", "mobile_no", "language",
            "enabled", "time_zone", "user_image", "role_profile_name"
        ]

        for key in allowed_fields:
            if key in kwargs:
                value = kwargs.get(key)
                # Handle type conversion if necessary
                if key == "enabled":
                    value = int(value)
                setattr(doc, key, value)

        doc.save(ignore_permissions=True)

        frappe.response["status"] = True
        frappe.response["message"] = "User updated"
        frappe.response["data"] = doc.as_dict()

    except Exception as e:
        frappe.response["status"] = False
        frappe.response["message"] = str(e)
        frappe.response["data"] = None

import socket

@frappe.whitelist()
def get_local_ip():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)
