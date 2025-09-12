import frappe
from frappe import _
from frappe.utils import nowdate
import math
import re
import base64
from frappe.utils.file_manager import save_file
from frappe.utils import get_first_day, get_last_day
from frappe.utils import getdate, add_days


@frappe.whitelist(allow_guest=False)
def create_employee(**kwargs):
    if frappe.session.user == "Guest":
        frappe.throw(_("Unauthorized access"), frappe.PermissionError)

    try:
        if frappe.request.method != "POST":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use POST request."
            frappe.local.response["data"] = None
            return
        if kwargs.get("personal_email") and frappe.db.exists("Employee", {"personal_email": kwargs.get("personal_email")}):
            frappe.response["status"] = False
            frappe.response["message"] = "Duplicate entry not allowed: personal_email already exists"
            frappe.response["data"] = None
            return

        if kwargs.get("company_email") and frappe.db.exists("Employee", {"company_email": kwargs.get("company_email")}):
            frappe.response["status"] = False
            frappe.response["message"] = "Duplicate entry not allowed: company_email already exists"
            frappe.response["data"] = None
            return

        if kwargs.get("employee_number") and frappe.db.exists("Employee", {"employee_number": kwargs.get("employee_number")}):
            frappe.response["status"] = False
            frappe.response["message"] = "Duplicate entry not allowed: employee_number already exists"
            frappe.response["data"] = None
            return

        # Create Employee
        employee = frappe.new_doc("Employee")

        for key, value in kwargs.items():
            if hasattr(employee, key):
                setattr(employee, key, value)

        if not employee.date_of_joining:
            employee.date_of_joining = nowdate()
        if not employee.status:
            employee.status = "Active"

        employee.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.response["status"] = True
        frappe.response["message"] = "Employee created successfully"
        frappe.response["data"] = employee.as_dict()

    except Exception as e:
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None


@frappe.whitelist(allow_guest=False)
def get_all_employees(email=None):
    if frappe.session.user == "Guest":
        frappe.throw(_("Unauthorized access"), frappe.PermissionError)

    try:
        if frappe.request.method != "GET":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use GET request."
            frappe.local.response["data"] = None
            return
        user = frappe.session.user
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee:
            frappe.response["status"] = False
            frappe.response["message"] = "No Employee linked with this user"
            frappe.response["data"] = None
            return
        filters = {}

        if email:
            filters["employee"] = employee
        employees = frappe.get_all("Employee", filters=filters, fields=["*"])
       
        frappe.response["status"] = True
        frappe.response["message"] = "Employees fetched successfully"
        frappe.response["data"] = employees
    except Exception as e:
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None

@frappe.whitelist(allow_guest=False)
def update_employee(name, **kwargs):
    if frappe.session.user == "Guest":
        frappe.throw(_("Unauthorized access"), frappe.PermissionError)

    try:
        if frappe.request.method != "PUT":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use PUT request."
            frappe.local.response["data"] = None
            return
        if not frappe.db.exists("Employee", name):
            frappe.response["status"] = False
            frappe.response["message"] = "Employee not found"
            frappe.response["data"] = None
            return

        doc = frappe.get_doc("Employee", name)

        for key, value in kwargs.items():
            if hasattr(doc, key):
                setattr(doc, key, value)

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        frappe.response["status"] = True
        frappe.response["message"] = "Employee updated successfully"
        frappe.response["data"] = doc.as_dict()
    except Exception as e:
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None

@frappe.whitelist(allow_guest=False)
def delete_employee(name):
    if frappe.session.user == "Guest":
        frappe.throw(_("Unauthorized access"), frappe.PermissionError)

    try:
        if frappe.request.method != "DELETE":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use DELETE request."
            frappe.local.response["data"] = None
            return
        if not frappe.db.exists("Employee", name):
            frappe.response["status"] = False
            frappe.response["message"] = "Employee not found"
            frappe.response["data"] = None
            return
        employee = frappe.get_doc("Employee", name)
        linked_user = employee.user_id if hasattr(employee, "user_id") else None

        if linked_user:
            employee.user_id = None
            employee.save(ignore_permissions=True)
            frappe.db.commit()
            user_permissions = frappe.get_all("User Permission", filters={"for_value": name, "allow": "Employee"})
            for perm in user_permissions:
                frappe.delete_doc("User Permission", perm.name, ignore_permissions=True)
            if frappe.db.exists("User", linked_user):
                frappe.delete_doc("User", linked_user, ignore_permissions=True)
                frappe.db.commit()

        frappe.delete_doc("Employee", name, ignore_permissions=True)
        frappe.db.commit()

        frappe.response["status"] = True
        frappe.response["message"] = "Employee and linked user deleted successfully"
        frappe.response["data"] = {"employee": name, "user": linked_user}

    except Exception as e:
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None


@frappe.whitelist(allow_guest=False)
def get_employee_checkins(employee=None, log_type=None, month=None, year=None):
    try:
        if frappe.request.method != "GET":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use GET request."
            frappe.local.response["data"] = None
            return
        user = frappe.session.user
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee:
            frappe.response["status"] = False
            frappe.response["message"] = "No Employee linked with this user"
            frappe.response["data"] = None
            return

        filters = {"employee": employee}

        # Log type filter
        if log_type:
            filters["log_type"] = log_type

        # ✅ Month-wise filter
        if month and year:
            try:
                month = int(month)
                year = int(year)
                start_date = get_first_day(f"{year}-{month}-01")
                end_date = get_last_day(f"{year}-{month}-01")
                filters["time"] = ["between", [start_date, end_date]]
            except Exception:
                frappe.response["status"] = False
                frappe.response["message"] = "Invalid month/year format"
                frappe.response["data"] = None
                return

        result = frappe.get_list(
            "Employee Checkin",
            filters=filters,
            fields=[
                "name",
                "employee",
                "log_type",
                "time",
                "device_id",
                "skip_auto_attendance",
                "checkin_image"
            ],
            limit_page_length=1000,
            order_by="time desc"
        )

        frappe.response["status"] = True
        frappe.response["message"] = "Check-ins fetched successfully"
        frappe.response["total_in_and_out"] = len(result)
        frappe.response["data"] = result

    except Exception as e:
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None



@frappe.whitelist(allow_guest=False)
def create_employee_checkin():
    try:
        if frappe.request.method != "POST":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use POST request."
            frappe.local.response["data"] = None
            return

        data = frappe.local.form_dict
        user = frappe.session.user
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")

        if not employee:
            frappe.response["status"] = False
            frappe.response["message"] = "No Employee linked with this user"
            frappe.response["data"] = None
            return

        required_fields = ["log_type", "time", "latitude", "longitude", "checkin_image"]
        for field in required_fields:
            if not data.get(field):
                frappe.response["status"] = False
                frappe.response["message"] = f"Missing required field: {field}"
                frappe.response["data"] = None
                return

        # HR config geo-check
        hr_config = frappe.get_single("HR Config")
        if hr_config.geo_location_required:
            config_lat = float(hr_config.latitude)
            config_lon = float(hr_config.longitude)
            allowed_area = float(hr_config.allowed_area)
            user_lat = float(data.get("latitude"))
            user_lon = float(data.get("longitude"))

            distance = get_distance_in_meters(config_lat, config_lon, user_lat, user_lon)

            if distance > allowed_area:
                frappe.response["status"] = False
                frappe.response["message"] = (
                    f"You are outside the allowed check-in area. "
                    f"Distance: {round(distance, 2)}m, Allowed: {allowed_area}m."
                )
                frappe.response["data"] = None
                return

        # Create the checkin doc
        doc = frappe.new_doc("Employee Checkin")
        doc.employee = employee
        doc.log_type = data.get("log_type")
        doc.time = data.get("time")
        doc.latitude = data.get("latitude")
        doc.longitude = data.get("longitude")
        doc.device_id = data.get("device_id")
        doc.skip_auto_attendance = frappe.utils.cint(data.get("skip_auto_attendance") or 0)
        doc.insert(ignore_permissions=True)
        base64_image = data.get("checkin_image")
        if base64_image:
            decoded = base64.b64decode(base64_image)
            filename = f"checkin_{doc.employee}_{frappe.utils.now_datetime().strftime('%Y%m%d%H%M%S')}.png"

            file_doc = save_file(
                filename,
                decoded,
                "Employee Checkin",
                doc.name if doc.name else None,  # file linked after insert
                folder=None,
                is_private=1
            )
            # Assign file_url to the doc
            if file_doc:
                doc.checkin_image = file_doc.file_url
                doc.save(ignore_permissions=True)

        # Insert only once
        #doc.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.response["status"] = True
        frappe.response["message"] = "Employee Checkin created successfully"
        frappe.response["data"] = {
            "name": doc.name,
            "employee": doc.employee,
            "log_type": doc.log_type,
            "time": doc.time,
            "device_id": doc.device_id,
            "skip_auto_attendance": doc.skip_auto_attendance,
            "checkin_image": doc.checkin_image,
        }

    except Exception as e:
        frappe.db.rollback()
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None



def get_distance_in_meters(lat1, lon1, lat2, lon2):
    """Haversine formula to calculate distance between two lat/lon points in meters."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c



@frappe.whitelist(allow_guest=False)
def get_employee_attendance():
    try:
        if frappe.request.method != "GET":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use GET request."
            frappe.local.response["data"] = None
            return
        user = frappe.session.user
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee:
            frappe.response["status"] = False
            frappe.response["message"] = "No Employee linked with this user"
            frappe.response["data"] = None
            return
        filters = {}
        if employee:
            filters["employee"] = employee
        attendance_records = frappe.get_list(
            "Attendance",
            filters=filters,
            fields=[
                "name",
                "employee",
                "employee_name",
                "attendance_date",
                "status",
                "shift",
                "company",
                "workflow_state"
            ],
            order_by="attendance_date desc",
            limit_page_length=1000
        )
        total = len(attendance_records)
        frappe.response["status"] = True
        frappe.response["message"] = "Attendance records fetched successfully"
        frappe.response["total_attendance"] = total
        frappe.response["data"] = attendance_records

    except Exception as e:
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None

#################### Leave Application API's Start ##############

from collections import Counter
@frappe.whitelist(allow_guest=False)
def get_leave_applications():
    try:
        if frappe.request.method != "GET":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use GET request."
            frappe.local.response["data"] = None
            return
        user = frappe.session.user
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee:
            frappe.response["status"] = False
            frappe.response["message"] = "No Employee linked with this user"
            frappe.response["data"] = None
            return
        filters = {}
        if employee:
            filters["employee"] = employee

        leave_apps = frappe.get_list(
            "Leave Application",
            filters=filters,
            fields=[
                "name",
                "employee",
                "employee_name",
                "leave_type",
                "from_date",
                "to_date",
                "posting_date",
                "half_day",
                "total_leave_days",
                "half_day_date",
                "custom_session",
                "status",
                "workflow_state",
                "description",
                "company"
            ],
            order_by="from_date desc",
            limit_page_length=1000
        )

        total = len(leave_apps)
        status_counts = Counter(app["status"] for app in leave_apps)

        frappe.response["status"]=True
        frappe.response["message"]="Leave applications fetched successfully"
        frappe.response["summary"]={
                                    "total_applications": total,
                                    "status_counts": dict(status_counts)
                                    }
        frappe.response["data"]=leave_apps

    except Exception as e:
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None

@frappe.whitelist(allow_guest=False)
def create_leave_application_for_admin():
    try:
        if frappe.request.method != "POST":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use POST request."
            frappe.local.response["data"] = None
            return
        data = frappe.local.form_dict

        required_fields = ["employee", "leave_type", "from_date", "to_date"]
        for field in required_fields:
            if not data.get(field):
                frappe.response["status"]=False
                frappe.response["message"]=f"Missing required field: {field}"
                frappe.response["data"]=None

        doc = frappe.new_doc("Leave Application")
        doc.employee = data.get("employee")
        doc.leave_type = data.get("leave_type")
        doc.from_date = data.get("from_date")
        doc.to_date = data.get("to_date")
        doc.custom_session = data.get("custom_session")
        doc.company = data.get("company")
        doc.half_day = int(data.get("half_day") or 0)
        doc.half_day_date = data.get("half_day_date") if doc.half_day else None
        doc.description = data.get("description") or ""

        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.response["status"]=True
        frappe.response["message"]="Leave Application created successfully"
        frappe.response["data"]={
                                "name": doc.name
                                }

    except Exception as e:
        frappe.db.rollback()
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None


@frappe.whitelist(allow_guest=False)
def create_leave_application():
    try:
        if frappe.request.method != "POST":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use POST request."
            frappe.local.response["data"] = None
            return
        data = frappe.local.form_dict

        user = frappe.session.user
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee:
            frappe.response["status"] = False
            frappe.response["message"] = "No Employee linked with this user"
            frappe.response["data"] = None
            return

        required_fields = ["leave_type", "from_date", "to_date"]
        for field in required_fields:
            if not data.get(field):
                frappe.response["status"] = False
                frappe.response["message"] = f"Missing required field: {field}"
                frappe.response["data"] = None
                return

        # Create Leave Application
        doc = frappe.new_doc("Leave Application")
        doc.employee = employee
        doc.leave_type = data.get("leave_type")
        doc.from_date = data.get("from_date")
        doc.to_date = data.get("to_date")
        doc.company = data.get("company")
        doc.custom_session = data.get("custom_session")
        doc.half_day = int(data.get("half_day") or 0)
        doc.half_day_date = data.get("half_day_date") if doc.half_day else None
        doc.description = data.get("description") or ""

        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.response["status"] = True
        frappe.response["message"] = "Leave Application created successfully"
        frappe.response["data"] = {"name": doc.name}

    except Exception as e:
        frappe.db.rollback()
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None


@frappe.whitelist(allow_guest=False)
def update_leave_application():
    try:
        if frappe.request.method != "PUT":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use PUT request."
            frappe.local.response["data"] = None
            return
        data = frappe.local.form_dict

        if not data.get("name"):
            frappe.response["status"]=False
            frappe.response["message"]="Missing required field: name"
            frappe.response["data"]=None

        doc = frappe.get_doc("Leave Application", data.get("name"))

        updatable_fields = [
            "from_date", "to_date", "leave_type", "half_day","custom_session",
            "half_day_date", "description", "company"
        ]
        for field in updatable_fields:
            if field in data:
                setattr(doc, field, data.get(field))

        doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.response["status"]=True
        frappe.response["message"]="Leave Application updated successfully"
        frappe.response["data"]={
                "name":doc.name
                }

    except Exception as e:
        frappe.db.rollback()
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None

@frappe.whitelist(allow_guest=False)
def delete_leave_application():
    try:
        if frappe.request.method != "DELETE":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use DELETE request."
            frappe.local.response["data"] = None
            return
        data = frappe.local.form_dict

        if not data.get("name"):
            frappe.response["status"]=False
            frappe.response["message"]="Missing required field: name"
            frappe.response["data"]=None

        doc = frappe.get_doc("Leave Application", data.get("name"))

        frappe.delete_doc("Leave Application", doc.name, ignore_permissions=True)
        frappe.db.commit()
        
        frappe.response["status"]=True
        frappe.response["message"]=f"Leave Application '{doc.name}' deleted successfully"
        frappe.response["data"]={
                    "name":doc.name
                }

    except frappe.DoesNotExistError:
        frappe.response["status"]=False
        frappe.response["message"]="Leave Application not found"
        frappe.response["data"]=None

    except Exception as e:
        frappe.db.rollback()
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None

############## Leave Application API's End #############

############## Request Work From Home API's Start ########

@frappe.whitelist(allow_guest=False)
def get_work_from_home_request():
    try:
        if frappe.request.method != "GET":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use GET request."
            frappe.local.response["data"] = None
            return
        user = frappe.session.user
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee:
            frappe.response["status"] = False
            frappe.response["message"] = "No Employee linked with this user"
            frappe.response["data"] = None
            return
        filters = {}
        if employee:
            filters["employee"] = employee

        leave_apps = frappe.get_list(
            "Request Work From Home",
            filters=filters,
            fields=[
                "name",
                "employee",
                "employee_name",
                "request_approver",
                "request_approver_name",
                "from_date",
                "to_date",
                "days",
                "status",
                "reason",
                "work_details"
            ],
            order_by="from_date desc",
            limit_page_length=1000
        )

        total = len(leave_apps)
        status_counts = Counter(app["status"] for app in leave_apps)
        
        frappe.response["status"]=True
        frappe.response["message"]="Request Work From Home fetched successfully"
        frappe.response["summary"]={
                "total_applications": total,
                "status_counts": dict(status_counts)
                }
        frappe.response["data"]=leave_apps

    except Exception as e:
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None

@frappe.whitelist(allow_guest=False)
def create_work_from_home_requests():
    try:
        if frappe.request.method != "POST":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use POST request."
            frappe.local.response["data"] = None
            return
        data = frappe.local.form_dict
        user = frappe.session.user

        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee:
            frappe.response["status"] = False
            frappe.response["message"] = "No Employee linked with this user"
            frappe.response["data"] = None
            return

        required_fields = ["from_date", "to_date", "reason"]
        for field in required_fields:
            if not data.get(field):
                frappe.response["status"] = False
                frappe.response["message"] = f"Missing required field: {field}"
                frappe.response["data"] = None
                return  # Exit early if a required field is missing

        # Check for duplicate WFH requests with overlapping dates
        duplicate = frappe.db.sql("""
            SELECT name FROM `tabRequest Work From Home`
            WHERE employee = %s
            AND (
                (from_date <= %s AND to_date >= %s) OR
                (from_date <= %s AND to_date >= %s) OR
                (from_date >= %s AND to_date <= %s)
            )
        """, (
            employee,
            data.get("from_date"), data.get("from_date"),
            data.get("to_date"), data.get("to_date"),
            data.get("from_date"), data.get("to_date")
        ), as_dict=True)

        if duplicate:
            frappe.response["status"] = False
            frappe.response["message"] = "Duplicate WFH request exists for the selected dates."
            frappe.response["data"] = None
            return

        # Create new request
        doc = frappe.new_doc("Request Work From Home")
        doc.employee = employee
        doc.from_date = data.get("from_date")
        doc.to_date = data.get("to_date")
        doc.reason = data.get("reason")
        doc.work_details = data.get("work_details")

        if data.get("request_approver"):
            doc.request_approver = data.get("request_approver")

        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.response["status"] = True
        frappe.response["message"] = "Request Work From Home created successfully"
        frappe.response["data"] = {
            "name": doc.name
        }

    except Exception as e:
        frappe.db.rollback()
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None

@frappe.whitelist(allow_guest=False)
def create_work_from_home_requests_for_admin():
    try:
        if frappe.request.method != "POST":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use POST request."
            frappe.local.response["data"] = None
            return
        data = frappe.local.form_dict

        required_fields = ["employee", "from_date", "to_date", "reason"]
        for field in required_fields:
            if not data.get(field):
                frappe.response["status"] = False
                frappe.response["message"] = f"Missing required field: {field}"
                frappe.response["data"] = None
                return  # Exit early if a required field is missing

        # Check for duplicate WFH requests with overlapping dates
        duplicate = frappe.db.sql("""
            SELECT name FROM `tabRequest Work From Home`
            WHERE employee = %s
            AND (
                (from_date <= %s AND to_date >= %s) OR
                (from_date <= %s AND to_date >= %s) OR
                (from_date >= %s AND to_date <= %s)
            )
        """, (
            data.get("employee"),
            data.get("from_date"), data.get("from_date"),
            data.get("to_date"), data.get("to_date"),
            data.get("from_date"), data.get("to_date")
        ), as_dict=True)

        if duplicate:
            frappe.response["status"] = False
            frappe.response["message"] = "Duplicate WFH request exists for the selected dates."
            frappe.response["data"] = None
            return

        # Create new request
        doc = frappe.new_doc("Request Work From Home")
        doc.employee = data.get("employee")
        doc.from_date = data.get("from_date")
        doc.to_date = data.get("to_date")
        doc.reason = data.get("reason")
        doc.work_details = data.get("work_details")

        if data.get("request_approver"):
            doc.request_approver = data.get("request_approver")

        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.response["status"] = True
        frappe.response["message"] = "Request Work From Home created successfully"
        frappe.response["data"] = {
            "name": doc.name
        }

    except Exception as e:
        frappe.db.rollback()
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None


@frappe.whitelist(allow_guest=False)
def update_work_from_home_request():
    try:
        if frappe.request.method != "PUT":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use PUT request."
            frappe.local.response["data"] = None
            return
        data = frappe.local.form_dict

        if not data.get("name"):
            frappe.response["status"]=False
            frappe.response["message"]="Missing required field: name"
            frappe.response["data"]=None

        doc = frappe.get_doc("Request Work From Home", data.get("name"))

        updatable_fields = [
            "from_date", "to_date", "reason", "work_details", "request_approver"
        ]
        for field in updatable_fields:
            if field in data:
                setattr(doc, field, data.get(field))

        doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.response["status"]=True
        frappe.response["message"]="Request Work From Home updated successfully"
        frappe.response["data"]={
                        "name":doc.name
                }

    except frappe.DoesNotExistError:
        frappe.response["status"]=False
        frappe.response["message"]="Request Work From Home not found"
        frappe.response["data"]=None

    except Exception as e:
        frappe.db.rollback()
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None


@frappe.whitelist(allow_guest=False)
def delete_work_from_home_request():
    try:
        if frappe.request.method != "DELETE":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use DELETE request."
            frappe.local.response["data"] = None
            return
        data = frappe.local.form_dict

        if not data.get("name"):
            frappe.response["status"]=False
            frappe.response["message"]="Missing required field: name"
            frappe.response["data"]=None

        doc = frappe.get_doc("Request Work From Home", data.get("name"))

        frappe.delete_doc("Request Work From Home", doc.name, ignore_permissions=True)
        frappe.db.commit()
        
        frappe.response["status"]=True
        frappe.response["message"]=f"Request Work From Home '{doc.name}' deleted successfully"
        frappe.response["data"]={
                        "name":doc.name
                }

    except frappe.DoesNotExistError:
        frappe.response["status"]=False
        frappe.response["message"]="Request Work From Home not found"
        frappe.response["data"]=None

    except Exception as e:
        frappe.db.rollback()
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None

############# Request Work From Home API's End #############

########### Attendance Request API's Start ############

@frappe.whitelist(allow_guest=False)
def get_attendance_requests():
    try:
        if frappe.request.method != "GET":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use GET request."
            frappe.local.response["data"] = None
            return
        user = frappe.session.user
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee:
            frappe.response["status"] = False
            frappe.response["message"] = "No Employee linked with this user"
            frappe.response["data"] = None
            return
        filters = {}
        if employee:
            filters["employee"] = employee

        requests = frappe.get_list(
            "Attendance Request",
            filters=filters,
            fields=[
                "name",
                "employee",
                "employee_name",
                "department",
                "company",
                "from_date",
                "to_date",
                "custom_days",
                "docstatus",
                "half_day",
                "half_day_date",
                "include_holidays",
                "shift",
                "reason",
                "explanation",
                "amended_from",
                "workflow_state"
            ],
            order_by="from_date desc",
            limit_page_length=1000
        )

        total = len(requests)
        
        frappe.response["status"]=True
        frappe.response["message"]="Attendance requests fetched successfully"
        frappe.response["total_requests"]=total
        frappe.response["data"]=requests

    except Exception as e:
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None


@frappe.whitelist(allow_guest=False)
def post_attendance_request():
    try:
        if frappe.request.method != "POST":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use POST request."
            frappe.local.response["data"] = None
            return
        data = frappe.local.form_dict
        user = frappe.session.user
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee:
            frappe.response["status"] = False
            frappe.response["message"] = "No Employee linked with this user"
            frappe.response["data"] = None
            return

        required_fields = ["from_date", "to_date", "reason"]
        for field in required_fields:
            if not data.get(field):
                frappe.response["status"]=False
                frappe.response["message"]=f"Missing required field: {field}"
                frappe.response["data"]=None

        doc = frappe.new_doc("Attendance Request")
        doc.employee = employee
        doc.from_date = data.get("from_date")
        doc.to_date = data.get("to_date")
        doc.reason = data.get("reason")
        doc.explanation = data.get("explanation", "")
        doc.half_day = int(data.get("half_day") or 0)
        doc.half_day_date = data.get("half_day_date") if doc.half_day else None
        doc.include_holidays = int(data.get("include_holidays") or 0)
        doc.shift = data.get("shift")
        doc.company = data.get("company")

        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.response["status"]=True
        frappe.response["message"]="Attendance Request created successfully"
        frappe.response["data"]={
                "name": doc.name,
                "employee": doc.employee,
                "from_date": doc.from_date,
                "to_date": doc.to_date,
                "reason": doc.reason,
                "status": doc.docstatus

                }

    except Exception as e:
        frappe.db.rollback()
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None

def calculate_custom_days(doc, method=None):
    if not doc.from_date or not doc.to_date:
        return

    from_date = getdate(doc.from_date)
    to_date = getdate(doc.to_date)

    # Get Holiday List from Employee or Company
    holiday_list = None
    if doc.employee:
        holiday_list = frappe.db.get_value("Employee", doc.employee, "holiday_list")
    if not holiday_list and doc.company:
        holiday_list = frappe.db.get_value("Company", doc.company, "default_holiday_list")

    holidays = set()
    if holiday_list:
        holidays = {
            getdate(h.holiday_date)
            for h in frappe.get_all(
                "Holiday",
                filters={"parent": holiday_list},
                fields=["holiday_date"]
            )
        }

    # Count days
    total_days = 0
    current = from_date
    while current <= to_date:
        if doc.include_holidays:
            total_days += 1
        else:
            if current not in holidays:
                total_days += 1
        current = add_days(current, 1)

    # Apply half day adjustment
    if doc.half_day and total_days > 0:
        total_days -= 0.5

    # Update field
    doc.custom_days = total_days


@frappe.whitelist(allow_guest=False)
def update_attendance_request():
    try:
        if frappe.request.method != "PUT":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use PUT request."
            frappe.local.response["data"] = None
            return
        data = frappe.local.form_dict

        if not data.get("name"):
            frappe.response["status"]=False
            frappe.response["message"]="Missing required field: name"
            frappe.response["data"]=None
        doc = frappe.get_doc("Attendance Request", data.get("name"))

        # Update fields if they are provided
        fields_to_update = [
            "from_date", "to_date", "reason", "explanation", "half_day",
            "half_day_date", "include_holidays", "shift", "company"
        ]
        for field in fields_to_update:
            if field in data:
                setattr(doc, field, data.get(field))

        doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.response["status"]=True
        frappe.response["message"]="Attendance Request updated successfully"
        frappe.response["data"]={
                "name":doc.name
                }

    except Exception as e:
        frappe.db.rollback()
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None
@frappe.whitelist(allow_guest=False)
def delete_attendance_request():
    try:
        if frappe.request.method != "DELETE":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use DELETE request."
            frappe.local.response["data"] = None
            return
        data = frappe.local.form_dict

        if not data.get("name"):
            frappe.response["status"]=False
            frappe.response["message"]="Missing required field: name"
            frappe.response["data"]=None

        frappe.delete_doc("Attendance Request", data.get("name"), ignore_permissions=True)
        frappe.db.commit()
        
        frappe.response["status"]=True
        frappe.response["message"]="Attendance Request deleted successfully"
        frappe.response["data"]={
                "name":data.get("name")
                }

    except Exception as e:
        frappe.db.rollback()
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None
######Attendance Request API Ends ################

@frappe.whitelist(allow_guest=False)
def get_leave_allocation():
    from hrms.hr.doctype.leave_application.leave_application import get_leave_details

    try:
        if frappe.request.method != "GET":
            frappe.local.response["http_status_code"] = 405
            frappe.local.response["status"] = False
            frappe.local.response["message"] = "Method Not Allowed. Use GET request."
            frappe.local.response["data"] = None
            return

        user = frappe.session.user
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee:
            frappe.response["status"] = False
            frappe.response["message"] = "No Employee linked with this user"
            frappe.response["data"] = None
            return
    
        date = frappe.utils.today()

        result = get_leave_details(employee=employee, date=date)
        leave_allocation = result.get("leave_allocation", {})
        lwps = result.get("lwps", [])

        frappe.response["status"] = True
        frappe.response["message"] = "Leave dashboard data fetched"
        frappe.response["data"] = {
            "leave_allocation": leave_allocation,
            "lwps": lwps,
            "allowed_leave_types": list(leave_allocation.keys()) + lwps
        }

    except Exception as e:
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None

@frappe.whitelist(allow_guest=False)
def get_leave_dashboard(employee=None, date=None):
    from hrms.hr.doctype.leave_application.leave_application import get_leave_details

    try:
        # If employee is not provided, fetch from session
        if not employee:
            user = frappe.session.user
            employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
            if not employee:
                frappe.response["status"] = False
                frappe.response["message"] = "No Employee linked with this user"
                frappe.response["data"] = None
                return

        # Set date to today if not provided
        if not date:
            date = frappe.utils.today()

        # Get leave details
        result = get_leave_details(employee=employee, date=date)
        leave_allocation = result.get("leave_allocation", {})
        lwps = result.get("lwps", [])

        frappe.response["status"] = True
        frappe.response["message"] = "Leave dashboard data fetched"
        frappe.response["data"] = {
            "leave_allocation": leave_allocation,
            "lwps": lwps,
            "allowed_leave_types": list(leave_allocation.keys()) + lwps
        }

    except Exception as e:
        raw_message = str(e)
        clean_message = re.sub(r"<.*?>", "", raw_message)
        frappe.response["status"] = False
        frappe.response["message"] = clean_message.strip()
        frappe.response["data"] = None


