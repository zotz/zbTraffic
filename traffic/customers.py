# File: traffic/customers.py

from traffic.database import get_connection
from traffic.utilities import current_timestamp
import re

def _strip(v):
    return v.strip() if isinstance(v, str) else v

def validate_customer_data(data, partial=False):
    errors=[]
    cleaned={}
    if not partial or "company_name" in data:
        cn = _strip(data.get("company_name","")) if data.get("company_name") is not None else ""
        if not cn:
            errors.append("company_name is required.")
        elif len(cn) < 2:
            errors.append("company_name must be at least 2 characters.")
        else:
            cleaned["company_name"]=cn
    if "address_line1" in data:
        v=_strip(data.get("address_line1") or "")
        cleaned["address_line1"]=v if v else None
    if "address_line2" in data:
        v=_strip(data.get("address_line2") or "")
        cleaned["address_line2"]=v if v else None
    if "locality" in data:
        v=_strip(data.get("locality") or "")
        cleaned["locality"]=v if v else None
    if "administrative_area" in data:
        v=_strip(data.get("administrative_area") or "")
        cleaned["administrative_area"]=v if v else None
    if "postal_code" in data:
        v=_strip(data.get("postal_code") or "")
        if v and len(v) > 20:
            errors.append("postal_code too long (max 20).")
        cleaned["postal_code"]=v if v else None
    if "country_code" in data:
        v=_strip(data.get("country_code") or "").upper()
        if v:
            if not re.match(r"^[A-Z]{2}$", v):
                errors.append("country_code must be 2 letters (e.g. BS, US, GB, CA).")
            else:
                cleaned["country_code"]=v
        else:
            cleaned["country_code"]=None
    if "telephone" in data:
        v=_strip(data.get("telephone") or "")
        cleaned["telephone"]=v if v else None
    if "email" in data:
        v=_strip(data.get("email") or "")
        if v and "@" not in v:
            errors.append("Email address does not appear valid.")
        cleaned["email"]=v if v else None
    if "category_id" in data:
        cid=data.get("category_id")
        if cid in ("", None):
            cleaned["category_id"]=None
        else:
            try:
                cleaned["category_id"]=int(cid)
            except:
                errors.append("category_id must be integer.")
    if "active" in data:
        try:
            cleaned["active"]=int(data.get("active"))
        except:
            cleaned["active"]=1
    return {"valid": len(errors)==0, "errors": errors, "cleaned": cleaned, "company_name": cleaned.get("company_name"), "telephone": cleaned.get("telephone"), "email": cleaned.get("email")}

def _get_cleaned(vr, key):
    if key in vr:
        return vr.get(key)
    return vr.get("cleaned", {}).get(key)

def _update_field(customer_id, field, value):
    con=get_connection(); cur=con.cursor()
    cur.execute(f"UPDATE customers SET {field} = ?, modified_date = ? WHERE id = ?", (value, current_timestamp(), customer_id))
    con.commit(); affected=cur.rowcount; con.close()
    if affected==0:
        return False, ["Customer not found."]
    return True, []

def add_customer(data=None, company_name=None, telephone=None, email=None, category_id=None,
                 address_line1=None, address_line2=None, locality=None,
                 administrative_area=None, postal_code=None, country_code=None,
                 city=None, state=None, address1=None, address2=None, country=None,
                 **kwargs):
    """
    Supports:
      add_customer(dict)
      add_customer("Company", telephone, email)
      add_customer(company_name="Company", city="...", state="...")
      Legacy aliases: city->locality, state->administrative_area, address1->address_line1, country->country_code
    """
    # Handle positional first arg as dict or string via data param or kwargs
    # If data is a string and company_name is None, treat data as company_name (legacy positional)
    if isinstance(data, dict):
        # dict form
        data_dict = data
    elif isinstance(data, str) and company_name is None:
        # legacy positional: first arg is company name
        data_dict = {
            "company_name": data,
            "telephone": telephone,
            "email": email,
            "category_id": category_id,
            "address_line1": address_line1,
            "address_line2": address_line2,
            "locality": locality,
            "administrative_area": administrative_area,
            "postal_code": postal_code,
            "country_code": country_code,
        }
        # apply legacy aliases if provided via kwargs
        if city is not None: data_dict["locality"] = city
        if state is not None: data_dict["administrative_area"] = state
        if address1 is not None: data_dict["address_line1"] = address1
        if address2 is not None: data_dict["address_line2"] = address2
        if country is not None: data_dict["country_code"] = country
        # merge extra kwargs (like company_name passed as kwarg unexpectedly)
        for k,v in kwargs.items():
            if k in ("company_name","telephone","email","category_id","address_line1","address_line2","locality","administrative_area","postal_code","country_code","city","state","address1","address2","country"):
                # map legacy
                if k=="city": data_dict["locality"]=v
                elif k=="state": data_dict["administrative_area"]=v
                elif k=="address1": data_dict["address_line1"]=v
                elif k=="address2": data_dict["address_line2"]=v
                elif k=="country": data_dict["country_code"]=v
                else:
                    data_dict[k]=v
    else:
        # keyword form: add_customer(company_name=..., telephone=...)
        # data may be None, company_name contains name
        data_dict = {
            "company_name": company_name if company_name is not None else data,
            "telephone": telephone,
            "email": email,
            "category_id": category_id,
            "address_line1": address_line1,
            "address_line2": address_line2,
            "locality": locality,
            "administrative_area": administrative_area,
            "postal_code": postal_code,
            "country_code": country_code,
        }
        # legacy aliases from explicit params
        if city is not None and data_dict.get("locality") is None:
            data_dict["locality"]=city
        if state is not None and data_dict.get("administrative_area") is None:
            data_dict["administrative_area"]=state
        if address1 is not None and data_dict.get("address_line1") is None:
            data_dict["address_line1"]=address1
        if address2 is not None and data_dict.get("address_line2") is None:
            data_dict["address_line2"]=address2
        if country is not None and data_dict.get("country_code") is None:
            data_dict["country_code"]=country
        # extra kwargs (seed2 may pass company_name, address1 etc as kwargs)
        for k,v in kwargs.items():
            if k=="city": data_dict["locality"]=v
            elif k=="state": data_dict["administrative_area"]=v
            elif k=="address1": data_dict["address_line1"]=v
            elif k=="address2": data_dict["address_line2"]=v
            elif k=="country": data_dict["country_code"]=v
            else:
                data_dict[k]=v


    # Map legacy aliases in data_dict if present
    if data_dict.get("city") is not None and data_dict.get("locality") is None:
        data_dict["locality"]=data_dict.pop("city")
    if data_dict.get("state") is not None and data_dict.get("administrative_area") is None:
        data_dict["administrative_area"]=data_dict.pop("state")
    if data_dict.get("address1") is not None and data_dict.get("address_line1") is None:
        data_dict["address_line1"]=data_dict.pop("address1")
    if data_dict.get("address2") is not None and data_dict.get("address_line2") is None:
        data_dict["address_line2"]=data_dict.pop("address2")
    if data_dict.get("country") is not None and data_dict.get("country_code") is None:
        data_dict["country_code"]=data_dict.pop("country")



    validation=validate_customer_data(data_dict, partial=False)
    if not validation["valid"]:
        return None, validation["errors"]



    company_name = _get_cleaned(validation, "company_name")
    addr1 = validation["cleaned"].get("address_line1")
    addr2 = validation["cleaned"].get("address_line2")
    loc = validation["cleaned"].get("locality")
    admin = validation["cleaned"].get("administrative_area")
    pcode = validation["cleaned"].get("postal_code")
    ccode = validation["cleaned"].get("country_code")
    tel = validation["cleaned"].get("telephone")
    em = validation["cleaned"].get("email")
    cat_id = validation["cleaned"].get("category_id")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM customers
        WHERE company_name = ?
        """,
        (company_name,)
    )

    existing = cursor.fetchone()

    if existing:
        connection.close()
        return None, [
            f"Customer already exists: {company_name}"
        ]












    now=current_timestamp()
    cursor.execute(
        """
        INSERT INTO customers
        (company_name, address_line1, address_line2, locality, administrative_area, postal_code, country_code, telephone, email, category_id, active, created_date, modified_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        """,
        (company_name, addr1, addr2, loc, admin, pcode, ccode, tel, em, cat_id, now, now)
    )
    connection.commit()
    cid=cursor.lastrowid
    connection.close()
    return cid, []

def get_customer(customer_id):
    con=get_connection(); cur=con.cursor()
    cur.execute("SELECT * FROM customers WHERE id=?", (customer_id,))
    row=cur.fetchone(); con.close()
    return dict(row) if row else None

def list_customers(status="active"):
    con=get_connection(); cur=con.cursor()
    if status=="active":
        cur.execute("SELECT * FROM customers WHERE active=1 ORDER BY company_name")
    elif status=="inactive":
        cur.execute("SELECT * FROM customers WHERE active=0 ORDER BY company_name")
    else:
        cur.execute("SELECT * FROM customers ORDER BY company_name")
    rows=[dict(r) for r in cur.fetchall()]; con.close(); return rows

def update_company_name(customer_id, company_name):
    v=validate_customer_data({"company_name": company_name}, partial=True)
    if not v["valid"]: return False, v["errors"]
    return _update_field(customer_id, "company_name", v["cleaned"]["company_name"])

def update_telephone(customer_id, telephone):
    if telephone: telephone=telephone.strip()
    v=validate_customer_data({"telephone": telephone}, partial=True)
    if not v["valid"]: return False, v["errors"]
    return _update_field(customer_id, "telephone", v["cleaned"].get("telephone"))

def update_email(customer_id, email):
    if email:
        email=email.strip()
        if "@" not in email: return False, ["Email address does not appear valid."]
    v=validate_customer_data({"email": email}, partial=True)
    if not v["valid"]: return False, v["errors"]
    return _update_field(customer_id, "email", v["cleaned"].get("email"))

def update_address_line1(customer_id, address_line1):
    v=validate_customer_data({"address_line1": address_line1}, partial=True)
    if not v["valid"]: return False, v["errors"]
    return _update_field(customer_id, "address_line1", v["cleaned"].get("address_line1"))

def update_address_line2(customer_id, address_line2):
    v=validate_customer_data({"address_line2": address_line2}, partial=True)
    if not v["valid"]: return False, v["errors"]
    return _update_field(customer_id, "address_line2", v["cleaned"].get("address_line2"))

def update_locality(customer_id, locality):
    v=validate_customer_data({"locality": locality}, partial=True)
    if not v["valid"]: return False, v["errors"]
    return _update_field(customer_id, "locality", v["cleaned"].get("locality"))

def update_administrative_area(customer_id, administrative_area):
    v=validate_customer_data({"administrative_area": administrative_area}, partial=True)
    if not v["valid"]: return False, v["errors"]
    return _update_field(customer_id, "administrative_area", v["cleaned"].get("administrative_area"))

def update_postal_code(customer_id, postal_code):
    v=validate_customer_data({"postal_code": postal_code}, partial=True)
    if not v["valid"]: return False, v["errors"]
    return _update_field(customer_id, "postal_code", v["cleaned"].get("postal_code"))

def update_country_code(customer_id, country_code):
    v=validate_customer_data({"country_code": country_code}, partial=True)
    if not v["valid"]: return False, v["errors"]
    return _update_field(customer_id, "country_code", v["cleaned"].get("country_code"))

def update_category(customer_id, category_id):
    v=validate_customer_data({"category_id": category_id}, partial=True)
    if not v["valid"]: return False, v["errors"]
    return _update_field(customer_id, "category_id", v["cleaned"].get("category_id"))

def update_customer(customer_id, data):
    v=validate_customer_data(data, partial=True)
    if not v["valid"]: return False, v["errors"]
    cleaned=v["cleaned"]
    if not cleaned: return False, ["No fields to update."]
    sets=[]; params=[]
    for k,val in cleaned.items():
        sets.append(f"{k} = ?"); params.append(val)
    sets.append("modified_date = ?"); params.append(current_timestamp()); params.append(customer_id)
    sql=f"UPDATE customers SET {', '.join(sets)} WHERE id = ?"
    con=get_connection(); cur=con.cursor(); cur.execute(sql, tuple(params)); con.commit(); affected=cur.rowcount; con.close()
    if affected==0: return False, ["Customer not found."]
    return True, []

def deactivate_customer(customer_id):
    con=get_connection(); cur=con.cursor()
    cur.execute("UPDATE customers SET active=0, modified_date=? WHERE id=?", (current_timestamp(), customer_id))
    con.commit(); affected=cur.rowcount; con.close()
    return (False, ["Customer not found."]) if affected==0 else (True, [])

def activate_customer(customer_id):
    con=get_connection(); cur=con.cursor()
    cur.execute("UPDATE customers SET active=1, modified_date=? WHERE id=?", (current_timestamp(), customer_id))
    con.commit(); affected=cur.rowcount; con.close()
    return (False, ["Customer not found."]) if affected==0 else (True, [])

# Backward compat aliases
def update_address1(customer_id, value): return update_address_line1(customer_id, value)
def update_address2(customer_id, value): return update_address_line2(customer_id, value)
def update_city(customer_id, value): return update_locality(customer_id, value)
def update_state(customer_id, value): return update_administrative_area(customer_id, value)
def update_country(customer_id, value): return update_country_code(customer_id, value)
