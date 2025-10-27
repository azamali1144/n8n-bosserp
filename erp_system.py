from zeep import Client
from zeep.wsdl import wsdl
from zeep.xsd import Schema
from lxml import etree
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import json
from datetime import datetime
import sqlite3
from functools import wraps
import base64

# ==================== SOAP SERVICE ====================
app = Flask(__name__)
CORS(app)

# Basic Authentication Configuration
VALID_USERS = {
    'admin': 'admin123',
    'user': 'user123',
    'manager': 'manager123'
}


# Database initialization
def init_db():
    conn = sqlite3.connect('erp_system.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS customers
                 (id INTEGER PRIMARY KEY, name TEXT, email TEXT, phone TEXT, created_at TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, name TEXT, sku TEXT, price REAL, stock INTEGER, created_at TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY, customer_id INTEGER, product_id INTEGER, quantity INTEGER, 
                  total_price REAL, status TEXT, created_at TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS invoices
                 (id INTEGER PRIMARY KEY, order_id INTEGER, amount REAL, status TEXT, created_at TEXT)''')

    conn.commit()
    conn.close()


init_db()


# ==================== AUTHENTICATION DECORATOR ====================

def check_auth(username, password):
    """Check if username/password combination is valid."""
    return username in VALID_USERS and VALID_USERS[username] == password


def authenticate():
    """Send 401 response that enables basic auth."""
    return jsonify({'message': 'Authentication required'}), 401, {
        'WWW-Authenticate': 'Basic realm="Login Required"'
    }


def requires_auth(f):
    """Decorator to require basic authentication."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


def check_soap_auth(soap_request):
    """Extract and verify basic auth from SOAP request headers."""
    auth_header = request.headers.get('Authorization', '')

    if not auth_header.startswith('Basic '):
        return False, None

    try:
        # Decode base64 credentials
        encoded_credentials = auth_header[6:]
        decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
        username, password = decoded_credentials.split(':', 1)

        if check_auth(username, password):
            return True, username
        return False, None
    except:
        return False, None


# ==================== WSDL & SOAP DEFINITIONS ====================
WSDL_CONTENT = '''<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
             xmlns:tns="http://erpsystem.local/soap"
             xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
             xmlns:xsd="http://www.w3.org/2001/XMLSchema"
             targetNamespace="http://erpsystem.local/soap"
             name="ERPSystem">

    <types>
        <xsd:schema targetNamespace="http://erpsystem.local/soap">
            <xsd:element name="Customer">
                <xsd:complexType>
                    <xsd:sequence>
                        <xsd:element name="id" type="xsd:int"/>
                        <xsd:element name="name" type="xsd:string"/>
                        <xsd:element name="email" type="xsd:string"/>
                        <xsd:element name="phone" type="xsd:string"/>
                    </xsd:sequence>
                </xsd:complexType>
            </xsd:element>

            <xsd:element name="Product">
                <xsd:complexType>
                    <xsd:sequence>
                        <xsd:element name="id" type="xsd:int"/>
                        <xsd:element name="name" type="xsd:string"/>
                        <xsd:element name="sku" type="xsd:string"/>
                        <xsd:element name="price" type="xsd:float"/>
                        <xsd:element name="stock" type="xsd:int"/>
                    </xsd:sequence>
                </xsd:complexType>
            </xsd:element>

            <xsd:element name="Order">
                <xsd:complexType>
                    <xsd:sequence>
                        <xsd:element name="id" type="xsd:int"/>
                        <xsd:element name="customer_id" type="xsd:int"/>
                        <xsd:element name="product_id" type="xsd:int"/>
                        <xsd:element name="quantity" type="xsd:int"/>
                        <xsd:element name="total_price" type="xsd:float"/>
                        <xsd:element name="status" type="xsd:string"/>
                    </xsd:sequence>
                </xsd:complexType>
            </xsd:element>
        </xsd:schema>
    </types>

    <message name="AddCustomerRequest">
        <part name="name" type="xsd:string"/>
        <part name="email" type="xsd:string"/>
        <part name="phone" type="xsd:string"/>
    </message>
    <message name="AddCustomerResponse">
        <part name="result" type="xsd:string"/>
    </message>

    <message name="GetCustomersRequest"/>
    <message name="GetCustomersResponse">
        <part name="customers" type="xsd:string"/>
    </message>

    <message name="AddProductRequest">
        <part name="name" type="xsd:string"/>
        <part name="sku" type="xsd:string"/>
        <part name="price" type="xsd:float"/>
        <part name="stock" type="xsd:int"/>
    </message>
    <message name="AddProductResponse">
        <part name="result" type="xsd:string"/>
    </message>

    <message name="GetProductsRequest"/>
    <message name="GetProductsResponse">
        <part name="products" type="xsd:string"/>
    </message>

    <message name="CreateOrderRequest">
        <part name="customer_id" type="xsd:int"/>
        <part name="product_id" type="xsd:int"/>
        <part name="quantity" type="xsd:int"/>
    </message>
    <message name="CreateOrderResponse">
        <part name="result" type="xsd:string"/>
    </message>

    <message name="GetOrdersRequest"/>
    <message name="GetOrdersResponse">
        <part name="orders" type="xsd:string"/>
    </message>

    <portType name="ERPPortType">
        <operation name="AddCustomer">
            <input message="tns:AddCustomerRequest"/>
            <output message="tns:AddCustomerResponse"/>
        </operation>
        <operation name="GetCustomers">
            <input message="tns:GetCustomersRequest"/>
            <output message="tns:GetCustomersResponse"/>
        </operation>
        <operation name="AddProduct">
            <input message="tns:AddProductRequest"/>
            <output message="tns:AddProductResponse"/>
        </operation>
        <operation name="GetProducts">
            <input message="tns:GetProductsRequest"/>
            <output message="tns:GetProductsResponse"/>
        </operation>
        <operation name="CreateOrder">
            <input message="tns:CreateOrderRequest"/>
            <output message="tns:CreateOrderResponse"/>
        </operation>
        <operation name="GetOrders">
            <input message="tns:GetOrdersRequest"/>
            <output message="tns:GetOrdersResponse"/>
        </operation>
    </portType>

    <binding name="ERPBinding" type="tns:ERPPortType">
        <soap:binding style="rpc" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="AddCustomer">
            <soap:operation soapAction="AddCustomer"/>
            <input><soap:body use="literal"/></input>
            <output><soap:body use="literal"/></output>
        </operation>
        <operation name="GetCustomers">
            <soap:operation soapAction="GetCustomers"/>
            <input><soap:body use="literal"/></input>
            <output><soap:body use="literal"/></output>
        </operation>
        <operation name="AddProduct">
            <soap:operation soapAction="AddProduct"/>
            <input><soap:body use="literal"/></input>
            <output><soap:body use="literal"/></output>
        </operation>
        <operation name="GetProducts">
            <soap:operation soapAction="GetProducts"/>
            <input><soap:body use="literal"/></input>
            <output><soap:body use="literal"/></output>
        </operation>
        <operation name="CreateOrder">
            <soap:operation soapAction="CreateOrder"/>
            <input><soap:body use="literal"/></input>
            <output><soap:body use="literal"/></output>
        </operation>
        <operation name="GetOrders">
            <soap:operation soapAction="GetOrders"/>
            <input><soap:body use="literal"/></input>
            <output><soap:body use="literal"/></output>
        </operation>
    </binding>

    <service name="ERPService">
        <port name="ERPPort" binding="tns:ERPBinding">
            <soap:address location="http://localhost:5000/soap"/>
        </port>
    </service>
</definitions>
'''


# ==================== SOAP SERVICE IMPLEMENTATIONS ====================

def add_customer(name, email, phone):
    try:
        conn = sqlite3.connect('erp_system.db')
        c = conn.cursor()
        created_at = datetime.now().isoformat()
        c.execute('INSERT INTO customers (name, email, phone, created_at) VALUES (?, ?, ?, ?)',
                  (name, email, phone, created_at))
        conn.commit()
        customer_id = c.lastrowid
        conn.close()
        return json.dumps({"status": "success", "id": customer_id, "message": "Customer added"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def get_customers():
    try:
        conn = sqlite3.connect('erp_system.db')
        c = conn.cursor()
        c.execute('SELECT * FROM customers')
        customers = [{"id": row[0], "name": row[1], "email": row[2], "phone": row[3]} for row in c.fetchall()]
        conn.close()
        return json.dumps(customers)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def add_product(name, sku, price, stock):
    try:
        conn = sqlite3.connect('erp_system.db')
        c = conn.cursor()
        created_at = datetime.now().isoformat()
        c.execute('INSERT INTO products (name, sku, price, stock, created_at) VALUES (?, ?, ?, ?, ?)',
                  (name, sku, price, stock, created_at))
        conn.commit()
        product_id = c.lastrowid
        conn.close()
        return json.dumps({"status": "success", "id": product_id, "message": "Product added"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def get_products():
    try:
        conn = sqlite3.connect('erp_system.db')
        c = conn.cursor()
        c.execute('SELECT * FROM products')
        products = [{"id": row[0], "name": row[1], "sku": row[2], "price": row[3], "stock": row[4]} for row in
                    c.fetchall()]
        conn.close()
        return json.dumps(products)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def create_order(customer_id, product_id, quantity):
    try:
        conn = sqlite3.connect('erp_system.db')
        c = conn.cursor()

        # Get product price
        c.execute('SELECT price, stock FROM products WHERE id = ?', (product_id,))
        product = c.fetchone()

        if not product:
            return json.dumps({"status": "error", "message": "Product not found"})

        price, stock = product
        if stock < quantity:
            return json.dumps({"status": "error", "message": "Insufficient stock"})

        total_price = price * quantity
        created_at = datetime.now().isoformat()

        c.execute(
            'INSERT INTO orders (customer_id, product_id, quantity, total_price, status, created_at) VALUES (?, ?, ?, ?, ?, ?)',
            (customer_id, product_id, quantity, total_price, "pending", created_at))

        # Update stock
        c.execute('UPDATE products SET stock = stock - ? WHERE id = ?', (quantity, product_id))

        conn.commit()
        order_id = c.lastrowid

        # Create invoice
        c.execute('INSERT INTO invoices (order_id, amount, status, created_at) VALUES (?, ?, ?, ?)',
                  (order_id, total_price, "pending", created_at))
        conn.commit()
        conn.close()

        return json.dumps({"status": "success", "id": order_id, "message": "Order created", "total": total_price})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def get_orders():
    try:
        conn = sqlite3.connect('erp_system.db')
        c = conn.cursor()
        c.execute('SELECT * FROM orders')
        orders = [{"id": row[0], "customer_id": row[1], "product_id": row[2], "quantity": row[3], "total_price": row[4],
                   "status": row[5]} for row in c.fetchall()]
        conn.close()
        return json.dumps(orders)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ==================== SOAP ENDPOINT WITH AUTH ====================

@app.route('/soap', methods=['POST'])
def soap_endpoint():
    # Check authentication
    is_authenticated, username = check_soap_auth(request.data.decode('utf-8'))

    if not is_authenticated:
        return '''<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <soap:Fault>
                    <faultcode>Server.Authentication</faultcode>
                    <faultstring>Authentication required. Please provide valid credentials.</faultstring>
                </soap:Fault>
            </soap:Body>
        </soap:Envelope>''', 401, {
            'Content-Type': 'text/xml',
            'WWW-Authenticate': 'Basic realm="SOAP API"'
        }

    soap_request = request.data.decode('utf-8')

    if 'AddCustomer' in soap_request:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(soap_request)
        name = root.find('.//{http://erpsystem.local/soap}name').text
        email = root.find('.//{http://erpsystem.local/soap}email').text
        phone = root.find('.//{http://erpsystem.local/soap}phone').text
        result = add_customer(name, email, phone)

        response = f'''<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <AddCustomerResponse xmlns="http://erpsystem.local/soap">
                    <result>{result}</result>
                </AddCustomerResponse>
            </soap:Body>
        </soap:Envelope>'''

    elif 'GetCustomers' in soap_request:
        result = get_customers()
        response = f'''<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <GetCustomersResponse xmlns="http://erpsystem.local/soap">
                    <customers>{result}</customers>
                </GetCustomersResponse>
            </soap:Body>
        </soap:Envelope>'''

    elif 'AddProduct' in soap_request:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(soap_request)
        name = root.find('.//{http://erpsystem.local/soap}name').text
        sku = root.find('.//{http://erpsystem.local/soap}sku').text
        price = float(root.find('.//{http://erpsystem.local/soap}price').text)
        stock = int(root.find('.//{http://erpsystem.local/soap}stock').text)
        result = add_product(name, sku, price, stock)

        response = f'''<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <AddProductResponse xmlns="http://erpsystem.local/soap">
                    <result>{result}</result>
                </AddProductResponse>
            </soap:Body>
        </soap:Envelope>'''

    elif 'GetProducts' in soap_request:
        result = get_products()
        response = f'''<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <GetProductsResponse xmlns="http://erpsystem.local/soap">
                    <products>{result}</products>
                </GetProductsResponse>
            </soap:Body>
        </soap:Envelope>'''

    elif 'CreateOrder' in soap_request:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(soap_request)
        customer_id = int(root.find('.//{http://erpsystem.local/soap}customer_id').text)
        product_id = int(root.find('.//{http://erpsystem.local/soap}product_id').text)
        quantity = int(root.find('.//{http://erpsystem.local/soap}quantity').text)
        result = create_order(customer_id, product_id, quantity)

        response = f'''<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <CreateOrderResponse xmlns="http://erpsystem.local/soap">
                    <result>{result}</result>
                </CreateOrderResponse>
            </soap:Body>
        </soap:Envelope>'''

    elif 'GetOrders' in soap_request:
        result = get_orders()
        response = f'''<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <GetOrdersResponse xmlns="http://erpsystem.local/soap">
                    <orders>{result}</orders>
                </GetOrdersResponse>
            </soap:Body>
        </soap:Envelope>'''

    else:
        response = '''<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <soap:Fault>
                    <faultcode>Server</faultcode>
                    <faultstring>Unknown operation</faultstring>
                </soap:Fault>
            </soap:Body>
        </soap:Envelope>'''

    return response, 200, {'Content-Type': 'text/xml'}


@app.route('/wsdl', methods=['GET'])
def wsdl_endpoint():
    return WSDL_CONTENT, 200, {'Content-Type': 'text/xml'}


# ==================== REST API WITH AUTH ====================

@app.route('/api/customers', methods=['GET', 'POST'])
@requires_auth
def customers_api():
    if request.method == 'POST':
        data = request.json
        return add_customer(data['name'], data['email'], data['phone'])
    else:
        return get_customers()


@app.route('/api/products', methods=['GET', 'POST'])
@requires_auth
def products_api():
    if request.method == 'POST':
        data = request.json
        return add_product(data['name'], data['sku'], data['price'], data['stock'])
    else:
        return get_products()


@app.route('/api/orders', methods=['GET', 'POST'])
@requires_auth
def orders_api():
    if request.method == 'POST':
        data = request.json
        return create_order(data['customer_id'], data['product_id'], data['quantity'])
    else:
        return get_orders()


# ==================== WEB UI WITH LOGIN ====================

@app.route('/login')
def login_page():
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ERP System - Login</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: Arial, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .login-container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                width: 400px;
            }
            h1 { color: #333; margin-bottom: 30px; text-align: center; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; color: #333; font-weight: bold; }
            input { 
                width: 100%; 
                padding: 12px; 
                border: 1px solid #ddd; 
                border-radius: 5px; 
                font-size: 14px; 
            }
            button { 
                width: 100%;
                background: #667eea; 
                color: white; 
                padding: 12px; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer; 
                font-size: 16px;
                font-weight: bold;
            }
            button:hover { background: #5568d3; }
            .error { color: red; margin-top: 10px; text-align: center; }
            .info { 
                background: #f0f0f0; 
                padding: 15px; 
                border-radius: 5px; 
                margin-top: 20px;
                font-size: 12px;
            }
            .info h3 { margin-bottom: 10px; color: #667eea; }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h1>🔐 ERP System Login</h1>
            <form id="loginForm">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" id="username" required>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="password" required>
                </div>
                <button type="submit">Login</button>
                <div id="errorMsg" class="error"></div>
            </form>

            <div class="info">
                <h3>Test Accounts:</h3>
                <p><strong>Admin:</strong> admin / admin123</p>
                <p><strong>User:</strong> user / user123</p>
                <p><strong>Manager:</strong> manager / manager123</p>
            </div>
        </div>

        <script>
            document.getElementById('loginForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;

                // Store credentials in base64
                const credentials = btoa(username + ':' + password);

                // Test authentication
                const response = await fetch('/api/customers', {
                    headers: {
                        'Authorization': 'Basic ' + credentials
                    }
                });

                if (response.ok) {
                    localStorage.setItem('auth', credentials);
                    localStorage.setItem('username', username);
                    window.location.href = '/';
                } else {
                    document.getElementById('errorMsg').textContent = 'Invalid credentials';
                }
            });
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)


@app.route('/')
def dashboard():
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ERP System Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #f5f5f5; }
            .header { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .header h1 { font-size: 24px; }
            .user-info { display: flex; align-items: center; gap: 15px; }
            .logout-btn {
                background: rgba(255,255,255,0.2);
                color: white;
                border: 1px solid white;
                padding: 8px 15px;
                border-radius: 5px;
                cursor: pointer;
            }
            .logout-btn:hover { background: rgba(255,255,255,0.3); }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .section { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .section h2 { color: #667eea; margin-bottom: 15px; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; color: #333; font-weight: bold; }
            input, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
            button { background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
            button:hover { background: #5568d3; }
            table { width: 100%; border-collapse: collapse; margin-top: 15px; }
            th { background: #f0f0f0; padding: 12px; text-align: left; border-bottom: 2px solid #ddd; }
            td { padding: 12px; border-bottom: 1px solid #ddd; }
            .success { color: green; }
            .error { color: red; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 ERP System Dashboard</h1>
            <div class="user-info">
                <span>👤 <span id="currentUser"></span></span>
                <button class="logout-btn" onclick="logout()">Logout</button>
            </div>
        </div>

        <div class="container">
            <div class="grid">
                <div class="section">
                    <h2>👥 Customer Management</h2>
                    <form id="customerForm">
                        <div class="form-group">
                            <label>Name</label>
                            <input type="text" id="custName" required>
                        </div>
                        <div class="form-group">
                            <label>Email</label>
                            <input type="email" id="custEmail" required>
                        </div>
                        <div class="form-group">
                            <label>Phone</label>
                            <input type="tel" id="custPhone" required>
                        </div>
                        <button type="submit">Add Customer</button>
                        <div id="customerMsg" style="margin-top: 10px;"></div>
                    </form>
                    <div id="customerList"></div>
                </div>

                <div class="section">
                    <h2>📦 Product Management</h2>
                    <form id="productForm">
                        <div class="form-group">
                            <label>Product Name</label>
                            <input type="text" id="prodName" required>
                        </div>
                        <div class="form-group">
                            <label>SKU</label>
                            <input type="text" id="prodSku" required>
                        </div>
                        <div class="form-group">
                            <label>Price</label>
                            <input type="number" id="prodPrice" step="0.01" required>
                        </div>
                        <div class="form-group">
                            <label>Stock</label>
                            <input type="number" id="prodStock" required>
                        </div>
                        <button type="submit">Add Product</button>
                        <div id="productMsg" style="margin-top: 10px;"></div>
                    </form>
                    <div id="productList"></div>
                </div>
            </div>

            <div class="section">
                <h2>📋 Order Management</h2>
                <form id="orderForm">
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 15px;">
                        <div class="form-group">
                            <label>Customer ID</label>
                            <input type="number" id="ordCustomerId" required>
                        </div>
                        <div class="form-group">
                            <label>Product ID</label>
                            <input type="number" id="ordProductId" required>
                        </div>
                        <div class="form-group">
                            <label>Quantity</label>
                            <input type="number" id="ordQuantity" required>
                        </div>
                        <div style="display: flex; align-items: flex-end;">
                            <button type="submit">Create Order</button>
                        </div>
                    </div>
                    <div id="orderMsg" style="margin-top: 10px;"></div>
                </form>
                <div id="orderList"></div>
            </div>
        </div>

        <script>
            // Check authentication on page load
            const auth = localStorage.getItem('auth');
            const username = localStorage.getItem('username');

            if (!auth) {
                window.location.href = '/login';
            } else {
                document.getElementById('currentUser').textContent = username;
            }

            function logout() {
                localStorage.removeItem('auth');
                localStorage.removeItem('username');
                window.location.href = '/login';
            }

            function getAuthHeaders() {
                return {
                    'Authorization': 'Basic ' + localStorage.getItem('auth'),
                    'Content-Type': 'application/json'
                };
            }

            async function loadCustomers() {
                try {
                    const res = await fetch('/api/customers', { headers: getAuthHeaders() });
                    if (res.status === 401) { logout(); return; }
                    const data = await res.json();
                    const html = '<h3>Customers:</h3><table><tr><th>ID</th><th>Name</th><th>Email</th><th>Phone</th></tr>' +
                        data.map(c => `<tr><td>${c.id}</td><td>${c.name}</td><td>${c.email}</td><td>${c.phone}</td></tr>`).join('') +
                        '</table>';
                    document.getElementById('customerList').innerHTML = html;
                } catch (e) {
                    console.error('Error loading customers:', e);
                }
            }

            async function loadProducts() {
                try {
                    const res = await fetch('/api/products', { headers: getAuthHeaders() });
                    if (res.status === 401) { logout(); return; }
                    const data = await res.json();
                    const html = '<h3>Products:</h3><table><tr><th>ID</th><th>Name</th><th>SKU</th><th>Price</th><th>Stock</th></tr>' +
                        data.map(p => `<tr><td>${p.id}</td><td>${p.name}</td><td>${p.sku}</td><td>$${p.price.toFixed(2)}</td><td>${p.stock}</td></tr>`).join('') +
                        '</table>';
                    document.getElementById('productList').innerHTML = html;
                } catch (e) {
                    console.error('Error loading products:', e);
                }
            }

            async function loadOrders() {
                try {
                    const res = await fetch('/api/orders', { headers: getAuthHeaders() });
                    if (res.status === 401) { logout(); return; }
                    const data = await res.json();
                    const html = '<h3>Orders:</h3><table><tr><th>ID</th><th>Customer</th><th>Product</th><th>Qty</th><th>Total</th><th>Status</th></tr>' +
                        data.map(o => `<tr><td>${o.id}</td><td>${o.customer_id}</td><td>${o.product_id}</td><td>${o.quantity}</td><td>$${o.total_price.toFixed(2)}</td><td>${o.status}</td></tr>`).join('') +
                        '</table>';
                    document.getElementById('orderList').innerHTML = html;
                } catch (e) {
                    console.error('Error loading orders:', e);
                }
            }

            document.getElementById('customerForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const res = await fetch('/api/customers', {
                    method: 'POST',
                    headers: getAuthHeaders(),
                    body: JSON.stringify({
                        name: document.getElementById('custName').value,
                        email: document.getElementById('custEmail').value,
                        phone: document.getElementById('custPhone').value
                    })
                });
                if (res.status === 401) { logout(); return; }
                const data = await res.json();
                document.getElementById('customerMsg').innerHTML = `<span class="success">${data.message}</span>`;
                document.getElementById('customerForm').reset();
                loadCustomers();
            });

            document.getElementById('productForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const res = await fetch('/api/products', {
                    method: 'POST',
                    headers: getAuthHeaders(),
                    body: JSON.stringify({
                        name: document.getElementById('prodName').value,
                        sku: document.getElementById('prodSku').value,
                        price: parseFloat(document.getElementById('prodPrice').value),
                        stock: parseInt(document.getElementById('prodStock').value)
                    })
                });
                if (res.status === 401) { logout(); return; }
                const data = await res.json();
                document.getElementById('productMsg').innerHTML = `<span class="success">${data.message}</span>`;
                document.getElementById('productForm').reset();
                loadProducts();
            });

            document.getElementById('orderForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const res = await fetch('/api/orders', {
                    method: 'POST',
                    headers: getAuthHeaders(),
                    body: JSON.stringify({
                        customer_id: parseInt(document.getElementById('ordCustomerId').value),
                        product_id: parseInt(document.getElementById('ordProductId').value),
                        quantity: parseInt(document.getElementById('ordQuantity').value)
                    })
                });
                if (res.status === 401) { logout(); return; }
                const data = await res.json();
                if (data.status === 'success') {
                    document.getElementById('orderMsg').innerHTML = `<span class="success">${data.message} - Total: $${data.total.toFixed(2)}</span>`;
                } else {
                    document.getElementById('orderMsg').innerHTML = `<span class="error">${data.message}</span>`;
                }
                document.getElementById('orderForm').reset();
                loadOrders();
            });

            loadCustomers();
            loadProducts();
            loadOrders();
            setInterval(() => { loadCustomers(); loadProducts(); loadOrders(); }, 5000);
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 ERP System with SOAP Support & Authentication")
    print("=" * 60)
    print("📍 Web Dashboard: http://localhost:5000")
    print("📍 Login Page: http://localhost:5000/login")
    print("📍 WSDL: http://localhost:5000/wsdl")
    print("📍 SOAP Endpoint: http://localhost:5000/soap")
    print("=" * 60)
    print("🔐 Test Accounts:")
    print("   Admin: admin / admin123")
    print("   User: user / user123")
    print("   Manager: manager / manager123")
    print("=" * 60)
    app.run(debug=True, port=5000)
