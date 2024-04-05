import frappe
import requests
import json
from erpnext.accounts.utils import now
from frappe.utils import nowdate,getdate

def get_settings():
    return frappe.get_doc("Biometric Settings")

def get_auth_token():
    settings = get_settings()
    user_name = settings.user
    base_url = settings.base_url
    pswd = settings.password

    url = f"{base_url}/api/WebApi/Login?UserName={user_name}&Password={pswd}"

    payload = {}
    headers = {}
    
    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code == 200:
            return response.text
        else:
            frappe.log_error(response.text)
            return response.text

    except Exception as e:
        frappe.log_error(frappe.get_traceback())
        return '{}'
    

def run_biometric():
    auth_response = json.loads(get_auth_token())
   
    token = auth_response.get('AuthToken')
    log_response = json.loads(get_attendance_logs(token))
    log_list = log_response.get('Items') or []
    
    for log in log_list:
        try:
            if frappe.get_value('Employee',{'attendance_device_id':log.get('IDNo')},'name'):
                today_date = getdate(log.get('PunchTime'))
                emp_chk = frappe.new_doc('Employee Checkin')
                emp_chk.employee = frappe.get_value('Employee',{'attendance_device_id':log.get('IDNo')},'name')
    
                chkin_list = frappe.get_list('Employee Checkin',{'time':['between',(today_date,today_date)],'employee':frappe.get_value('Employee',{'attendance_device_id':log.get('IDNo')},'name')},['log_type'])
                if not chkin_list:
                    emp_chk.log_type = 'IN'
                elif chkin_list :
                    emp_chk.log_type = 'IN' if chkin_list[-1]['log_type'] =='OUT' else 'OUT'
                
                emp_chk.time = log.get('PunchTime')
                emp_chk.device_id = log.get('OUCode')
                emp_chk.save()
                # create_biometric_log(log,'Success')
            else:
                create_biometric_log(log,'Failure',f"No Employee ID - {frappe.get_value('Employee',{'attendance_device_id':log.get('IDNo')},'name')} Found")

        except Exception as e:
            create_biometric_log(log,'Failure',frappe.get_traceback())
    
    for i in frappe.get_all("Shift Type",pluck='name'):
        time = frappe.get_value('Employee Checkin',{'shift':i},'time',order_by='creation desc')
        frappe.db.set_value("Shift Type",i,'last_sync_of_checkin',time)
            
    frappe.db.commit()
            

def get_attendance_logs(token):
    settings = get_settings()
    base_url = settings.base_url
    from_time = settings.last_updated_time

    to_time = now()

    url = f"{base_url}/api/DeviceRequest/GetAttendanceDataByDateTime?FromDatetime={from_time}&ToDateTime={to_time}"

    payload = {}
    headers = {
    'AuthToken': f'{token}',
    'Content-Type': 'application/json'
    }
    
    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code == 200:
            frappe.db.set_single_value('Biometric Settings','last_updated_time',to_time)
            return response.text
        else:
            frappe.log_error(response.text)
            return response.text
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback())
        return '{}'
    
def create_biometric_log(log,status,traceback):
    bio_log = frappe.new_doc('Biometric Failure Log')
    bio_log.status = status
    bio_log.id = log.get('IDNo')
    bio_log.time = log.get('PunchTime')
    bio_log.device_id = log.get('OUCode')
    bio_log.error_msg = traceback
    bio_log.save()
